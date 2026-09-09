import csv
import logging
import os.path
from collections import OrderedDict

import django_filters
import surt
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework import status

from perma.celery_tasks import (
    delete_link_from_daily_item,
    run_next_capture,
    upload_link_to_internet_archive
)
from perma.models import Capture, CaptureJob, Folder, Link, LinkBatch
from perma.utils import stream_archive_if_permissible

from ..serializers import AuthenticatedLinkSerializer, LinkSerializer
from ..utils import (
    LimitedTastypiePagination,
    get_download_file_format,
    load_parent,
    raise_general_validation_error,
    raise_invalid_capture_job,
    reverse_api_view_relative,
    url_is_invalid_unicode,
)
from .base import BaseView

logger = logging.getLogger(__name__)


class LinkFilter(django_filters.rest_framework.FilterSet):
    """
    Custom filter for searching links by query string.
    """
    date = django_filters.IsoDateTimeFilter(field_name="creation_timestamp", lookup_expr='date')      # ?date=
    min_date = django_filters.IsoDateTimeFilter(field_name="creation_timestamp", lookup_expr='gte')   # ?min_date=
    max_date = django_filters.IsoDateTimeFilter(field_name="creation_timestamp", lookup_expr='lte')   # ?max_date=
    url = django_filters.CharFilter(method='surt_filter')                                             # ?url=

    class Meta:
        model = Link
        fields = ['url', 'date', 'min_date', 'max_date']

    def surt_filter(self, queryset, _name, value):
        try:
            canonicalized = surt.surt(value)
        except ValueError:
            # if the user-specified value is not a valid URL and therefore cannot be parsed
            # and formatted as a surt, return the queryset as is, as though `url` was not
            # included in the querystring
            return queryset
        return queryset.filter(submitted_url_surt=canonicalized)


# /public/archives
class PublicLinkListView(BaseView):
    permission_classes = ()  # no login required
    serializer_class = LinkSerializer

    def get(self, request, format=None):
        """
        List public links.
        """

        queryset = Link.objects\
            .order_by('-creation_timestamp')\
            .select_related('capture_job')\
            .prefetch_related('captures').discoverable()
        return self.simple_list(request, queryset, paginator_class=LimitedTastypiePagination)


# /archives
# /folders/:parent_id/archives
class AuthenticatedLinkListView(BaseView):
    serializer_class = AuthenticatedLinkSerializer
    filterset_class = LinkFilter
    search_fields = ('guid', 'submitted_url', 'submitted_title', 'notes',)  # fields that can be searched with q= query string

    @staticmethod
    def get_folder_from_request(request):
        """
        Helper method to load folder from request.data['folder'].
        Used by AuthenticatedLinkListView.post and AuthenticatedLinkDetailView.patch.
        """
        if request.data.get('folder'):
            try:
                return Folder.objects.accessible_to(request.user).get(pk=request.data['folder'])
            except (Folder.DoesNotExist, ValueError):
                raise ValidationError({'folder': ["Folder not found."]})
        return None

    @staticmethod
    def load_links(request):
        """
        Helper method to load links.
        Used by AuthenticatedLinkListView.get and AuthenticatedLinkListExportView.get.
        """
        queryset = Link.objects\
            .order_by('-creation_timestamp')\
            .select_related('organization', 'organization__registrar', 'organization__shared_folder', 'capture_job', 'created_by')\
            .prefetch_related('captures')

        if request.parent:
            # For /folders/:parent_id/archives, limit to links in folder.
            # The code that sets request.parent guarantees that folder is accessible to this user;
            # no need for a check here.
            queryset = queryset.filter(folders=request.parent)
        else:
            # Otherwise, get all the links accessible to the user
            queryset = queryset.accessible_to(request.user)

        return queryset

    @load_parent
    def get(self, request, format=None):
        """
        List links for user.
        """
        return self.simple_list(request, self.load_links(request))

    @load_parent
    def post(self, request, format=None):
        """
        Create new link.
        """
        data = request.data

        human = request.data.get('human', False)
        if not isinstance(human, bool):
            raise ValidationError({'human': f'Value must be of type bool, not {type(human).__name__}.'})
        # Somehow it's possible for some control characters to get to the server
        submitted_url = request.data.get('url', '')
        if url_is_invalid_unicode(submitted_url):
            raise ValidationError({'url': "Unicode error while processing URL."})

        capture_job = CaptureJob(
            human=human,
            submitted_url=submitted_url[:2100],
            created_by=request.user,
            archive_formats = settings.ARCHIVE_FORMATS
        )

        # Batch is set directly on the request object by the LinkBatch api,
        # to prevent abuse of this feature by those POSTing directly to this route.
        if getattr(request, 'batch', None):
            batch = LinkBatch.objects.get(id=request.batch)
            capture_job.link_batch = batch
            batch.cached_capture_job_count = F('cached_capture_job_count') + 1
            batch.save(update_fields=['cached_capture_job_count'])
        capture_job.save()

        # Set target folder, in order of preference:
        # - 'folder' key in data
        # - parent folder, if posting to /folders/:parent_id/archives
        # - user's personal folder
        try:
            folder = self.get_folder_from_request(request) or request.parent or request.user.root_folder
        except ValidationError as e:
            raise_invalid_capture_job(capture_job, e.detail)

        message_template = "Perma can't create this link. {error} {resolution}"

        # Disallow creation of links in top-level sponsored folder
        if folder.is_sponsored_root_folder:
            message = message_template.format_map({
                'error': "You can't make links directly in your Sponsored Links folder.",
                'resolution': "Select a folder belonging to a sponsor."
            })
            raise_invalid_capture_job(capture_job, message)

        # Make sure a limited user has links left to create
        if not folder.organization and not folder.sponsored_by:
            if not request.user.link_creation_allowed():

                error = "You've reached your usage limit."
                resolution = "Visit your Usage Plan page for information and plan options."

                if request.user.cached_subscription_status == 'Hold':  # generally for users with CC issues
                    error = 'Your account needs attention —'
                    resolution = 'see your Usage Plan page for details.'
                elif request.user.nonpaying:
                    resolution = 'Get in touch if you need more.'

                message = message_template.format_map({'error': error, 'resolution': resolution})
                raise_invalid_capture_job(capture_job, message)
        else:
            registrar = folder.sponsored_by if folder.sponsored_by else folder.organization.registrar
            registrar_contact_string = ', '.join([user.email for user in registrar.active_registrar_users()])

            resolution = 'See your Usage Plan page for details.' if request.user.registrar else \
                f"For assistance, contact: {registrar_contact_string}."

            if not registrar.link_creation_allowed():
                message = message_template.format_map({'error': f"The {registrar.name} account needs attention.",
                                                       'resolution': resolution})
                raise_invalid_capture_job(capture_job, message)

            if folder.read_only:
                message = message_template.format_map({'error': f"{registrar.name} set this folder to read-only.",
                                                       'resolution': resolution})
                raise_invalid_capture_job(capture_job, message)


        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():

            with transaction.atomic():
                # Technique from https://github.com/harvard-lil/capstone/blob/0f7fb80f26e753e36e0c7a6a199b8fdccdd318be/capstone/capapi/serializers.py#L121
                #
                # Fetch the current user data here inside a transaction, using select_for_update
                # to lock the row so we don't collide with any simultaneous requests
                user = request.user.__class__.objects.select_for_update().get(pk=request.user.pk)

                # If this is a Personal Link, and if the user only has bonus links left, decrement bonus links
                bonus_link = False
                if not folder.organization and not folder.sponsored_by:
                    links_remaining, _ , bonus_links = user.get_links_remaining()
                    if bonus_links and not links_remaining:
                        # (this works because it's part of the same transaction with the select_for_update --
                        # we don't have to use the same object)
                        request.user.bonus_links = bonus_links - 1
                        request.user.save(update_fields=['bonus_links'])
                        bonus_link = True

                link = serializer.save(created_by=request.user, bonus_link=bonus_link)

                # put link in folder and handle Org settings based on folder
                if folder.organization and folder.organization.default_to_private:
                    link.is_private = True
                    link.save()
                link.move_to_folder_for_user(folder, request.user)  # also sets link.organization

            # handle uploaded file
            uploaded_file = request.data.get('file')
            if uploaded_file:
                link.write_uploaded_file(uploaded_file)

            # handle submitted url
            else:
                # create primary capture placeholder
                Capture(
                    link=link,
                    role='primary',
                    status='pending',
                    record_type='response',
                    url=link.ascii_safe_url,
                ).save()

                # kick off capture tasks -- no need for guid since it'll work through the queue
                capture_job.status = 'pending'
                capture_job.link = link
                if validation_status_code := getattr(serializer, 'validation_status_code', None):
                    capture_job.validation_status_code = validation_status_code
                capture_job.save(update_fields=['status', 'link', 'validation_status_code'])
                if not os.path.exists(settings.DEPLOYMENT_SENTINEL):
                    run_next_capture.delay()
                else:
                    logger.info("Deployment sentinel is present, not running next capture.")

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        raise_invalid_capture_job(capture_job, serializer.errors)


# /archives/export
# /folders/:parent_id/archives/export
class AuthenticatedLinkListExportView(BaseView):

    @load_parent
    def get(self, request, format=None):
        def report_status(link):
            if link.has_capture_job() and link.capture_job.status in ['pending', 'in_progress']:
                return link.capture_job.status
            return 'success' if link.can_play_back() else 'failure'

        queryset = AuthenticatedLinkListView.load_links(request)
        formatted_data = [
            OrderedDict([
                ('url', link.submitted_url),
                ('status', report_status(link)),
                ('error_message', link.capture_job.message if link.has_capture_job() else ''),
                ('title', link.submitted_title),
                ('created_on', link.creation_timestamp.strftime('%B %d, %Y')),
                ('notes', link.notes),
                ('perma_link', f"{request.scheme}://{request.get_host()}/{link.guid}")
            ])
            for link in queryset
        ]
        response = HttpResponse(content_type='text/csv')
        if request.parent:
            filename = f"perma-folder-{request.parent.id}-archives.csv"
        else:
            filename = "perma-archives.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        if formatted_data:
            writer = csv.DictWriter(response, fieldnames=list(formatted_data[0].keys()))
            writer.writeheader()
            writer.writerows(formatted_data)
        return response


# /archives/:guid
class AuthenticatedLinkDetailView(BaseView):
    serializer_class = AuthenticatedLinkSerializer

    def get(self, request, guid, format=None):
        """
        Single link details
        """
        return self.simple_get(request, guid)

    def patch(self, request, guid, format=None):
        """
        Update link.
        """
        link = self.get_object_for_user_by_pk(request.user, guid)

        was_private = link.is_private
        data = request.data
        folder = AuthenticatedLinkListView.get_folder_from_request(request)
        if folder and folder.is_sponsored_root_folder:
            raise_general_validation_error("You can't move links to your Sponsored Links folder. Select a folder belonging to a sponsor or organization, or your Personal Links folder.")

        serializer = self.serializer_class(link, data=data, partial=True, context={'request': self.request})
        if serializer.is_valid():
            serializer.save()

            # move to new folder
            if folder:
                link.move_to_folder_for_user(folder, request.user)

            # handle file patch
            uploaded_file = request.data.get('file')
            if uploaded_file:

                if link.has_capture_job() and link.capture_job.status ==  'in_progress' :
                    raise_general_validation_error("Capture in progress: please wait until complete before uploading a replacement.")

                # delete related captures, delete warc (rename), mark capture job as superseded
                link.delete_related_captures()
                link.safe_delete_warc()
                link.safe_delete_wacz()
                link.mark_capturejob_superseded()

                # write new warc and capture
                link.write_uploaded_file(uploaded_file)

            # update internet archive if privacy changes
            if 'is_private' in data and was_private != bool(data.get("is_private")) and link.is_permanent():
                if was_private:
                    # if link was private but has been marked public, mark it for upload.
                    link.internet_archive_upload_status = 'upload_or_reupload_required'
                    link.save(update_fields=["internet_archive_upload_status"])
                    logger.info(f"Link {link.guid} was toggled to public. Requesting the IA upload.")
                    upload_link_to_internet_archive.delay(link.guid)
                else:
                    # if link was public but has been marked private, mark it for deletion.
                    link.internet_archive_upload_status = 'deletion_required'
                    link.save(update_fields=["internet_archive_upload_status"])
                    logger.info(f"Link {link.guid} was toggled to private. Requesting the IA deletion.")
                    delete_link_from_daily_item.delay(link.guid)

            # include remaining links in response
            links_remaining = request.user.get_links_remaining()
            serializer.data['links_remaining'] = 'Infinity' if links_remaining[0] == float('inf') else links_remaining[0]
            serializer.data['links_remaining_period'] = links_remaining[1]

            return Response(serializer.data)

        raise ValidationError(serializer.errors)

    def delete(self, request, guid, format=None):
        """
        Delete link.
        """
        link = self.get_object_for_user_by_pk(request.user, guid)

        if not request.user.can_delete(link):
            raise PermissionDenied()

        if link.has_capture_job() and link.capture_job.status ==  'in_progress' :
            raise_general_validation_error("Capture in progress: please wait until complete before deleting.")

        with transaction.atomic():
            link.delete_related_captures()
            link.cached_can_play_back = False
            link.safe_delete()
            link.save()

            if link.bonus_link:
                link.created_by.bonus_links = (link.created_by.bonus_links or 0) + 1
                link.created_by.save(update_fields=['bonus_links'])

        return Response(status=status.HTTP_204_NO_CONTENT)


#/archives/:guid/download
class AuthenticatedLinkDownloadView(BaseView):
    serializer_class = AuthenticatedLinkSerializer

    def get(self, request, guid, format=None):
        """
        Download WARC.
        """
        link = self.get_object_for_user_by_pk(request.user, guid)
        file_format = get_download_file_format(request)
        if link.replacement_link_id:
            base_url = reverse_api_view_relative('archives_download', kwargs={'guid': link.replacement_link_id})
            return HttpResponseRedirect(f"{base_url}?file_format={file_format}")
        return stream_archive_if_permissible(link, request.user, file_format=file_format)


# /folders/:parent_id/archives/:guid
class MoveLinkView(BaseView):
    serializer_class = AuthenticatedLinkSerializer

    @load_parent
    def put(self, request, guid, format=None):
        """
        Move link to new folder.
        """
        link = self.get_object_for_user_by_pk(request.user, guid)
        if request.parent.is_sponsored_root_folder:
            raise_general_validation_error("You can't move links to your Sponsored Links folder. Select a folder belonging to a sponsor or organization, or your Personal Links folder.")
        link.move_to_folder_for_user(request.parent, request.user)
        serializer = self.serializer_class(link, context={'request': request})
        return Response(serializer.data)
