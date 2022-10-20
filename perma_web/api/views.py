from collections import OrderedDict
import csv
import django_filters
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.http import Http404, HttpResponse, HttpResponseRedirect
from mptt.exceptions import InvalidMove
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import surt

from perma.utils import stream_warc, stream_warc_if_permissible
from perma.tasks import run_next_capture
from perma.models import Folder, CaptureJob, Link, Capture, Organization, LinkBatch

from .utils import TastypiePagination, load_parent, raise_general_validation_error, \
    raise_invalid_capture_job, dispatch_multiple_requests, reverse_api_view_relative, \
    url_is_invalid_unicode
from .serializers import FolderSerializer, CaptureJobSerializer, LinkSerializer, AuthenticatedLinkSerializer, \
    LinkUserSerializer, OrganizationSerializer, LinkBatchSerializer, DetailedLinkBatchSerializer
from django.conf import settings
from django.urls import reverse

### BASE VIEW ###

class BaseView(APIView):
    permission_classes = (IsAuthenticated,)  # by default all users must be authenticated
    serializer_class = None  # overridden for each subclass
    queryset = None  # override to provide queryset for list and detail views

    # configure filtering of list endpoints by query string
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,  # subclasses can be filtered by keyword if filterset_class is set
        SearchFilter,         # subclasses can be filtered by q= if search_fields is set
        OrderingFilter        # subclasses can be ordered by order_by= if ordering_fields is set
    )
    ordering_fields = ()      # lock down order_by fields -- security risk if unlimited


    ### helpers ###

    def get_queryset(self, queryset=None):
        """Return queryset, or self.queryset, or raise config error."""
        if queryset is None:
            if self.queryset is None:
                raise NotImplementedError("No queryset configured on subclass.")
            queryset = self.queryset
        return queryset


    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        Copied from GenericAPIView
        """
        try:
            for backend in list(self.filter_backends):
                queryset = backend().filter_queryset(self.request, queryset, self)
            return queryset
        except DjangoValidationError as e:
            raise ValidationError(e.error_dict)

    def get_object_for_user(self, user, queryset):
        """
            Get single object from queryset, making sure that returned object is accessible_to(user).
        """
        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404
        if not obj.accessible_to(user):
            raise PermissionDenied()
        return obj

    def get_object_for_user_by_pk(self, user, pk):
        """
            Get single object by primary key, based on our serializer_class.
        """
        queryset = self.queryset.all() if self.queryset is not None else self.serializer_class.Meta.model.objects.all()
        return self.get_object_for_user(user, queryset.filter(pk=pk))


    ### basic views ###

    def simple_list(self, request, queryset=None, serializer_class=None):
        """
            Paginate and return a list of objects from given queryset.
        """
        queryset = self.get_queryset(queryset)
        queryset = self.filter_queryset(queryset)
        paginator = TastypiePagination()
        items = paginator.paginate_queryset(queryset, request)
        serializer_class = serializer_class if serializer_class else self.serializer_class
        serializer = serializer_class(items, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def simple_get(self, request, pk=None, obj=None, serializer_class=None):
        """
            Return single serialized object based on either primary key or object already loaded.
        """
        if not obj:
            obj = self.get_object_for_user_by_pk(request.user, pk)
        serializer_class = serializer_class if serializer_class else self.serializer_class
        serializer = serializer_class(obj, context={"request": request})
        return Response(serializer.data)

    def simple_create(self, data, save_kwargs={}):
        """
            Validate and save new object.
        """
        serializer = self.serializer_class(data=data, context={'request': self.request})
        if serializer.is_valid():
            serializer.save(**save_kwargs)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def simple_update(self, obj, data):
        """
            Validate and update given fields on object.
        """
        serializer = self.serializer_class(obj, data=data, partial=True, context={'request': self.request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        raise ValidationError(serializer.errors)

    def simple_delete(self, obj):
        """
            Delete object.
        """
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


### ORGANIZATION VIEWS ###

# /organizations
class OrganizationListView(BaseView):
    serializer_class = OrganizationSerializer
    ordering_fields = ('name', 'registrar')

    def get(self, request, format=None):
        """ List orgs. """
        queryset = Organization.objects.accessible_to(request.user).select_related('registrar', 'shared_folder')
        return self.simple_list(request, queryset)

# /organizations/:id
class OrganizationDetailView(BaseView):
    serializer_class = OrganizationSerializer

    def get(self, request, pk, format=None):
        """ Single org details. """
        return self.simple_get(request, pk)


### DEVELOPER DOCS VIEWS ###
class DeveloperDocsView(APIView):
    def get(self, request, format=None):
        """ reverse to Developer Docs to fetch correct url (view) named as 'dev_docs' """
        absolute_url_to_redirect_to = f"{ self.request.scheme }://{ settings.HOST }{ reverse('dev_docs', urlconf='perma.urls') }"
        """ Redirect to Dev Docs """
        return HttpResponseRedirect(absolute_url_to_redirect_to)

### FOLDER VIEWS ###

# /folders
# /folders/:parent_id/folders
class FolderListView(BaseView):
    serializer_class = FolderSerializer

    @load_parent
    def get(self, request, format=None):
        """ List folders for user. """
        if request.parent:
            # for /folders/:parent_id/folders, list subfolders of parent folder
            queryset = Folder.objects.filter(parent=request.parent)
        else:
            # for /folders, list all top level folders for user
            queryset = request.user.top_level_folders()
        return self.simple_list(request, queryset)

    @load_parent
    def post(self, request, format=None):
        """ Create folder. """
        # if parent folder is not supplied in post data, try to get it from /folders/:parent_id:
        data = request.data.copy()
        if request.parent:
            data.setdefault('parent', request.parent.pk)

        return self.simple_create(data, {'created_by': request.user})

# /folders/:id
# /folders/:parent_id/folders/:id
class FolderDetailView(BaseView):
    serializer_class = FolderSerializer

    @load_parent
    def get(self, request, pk, format=None):
        """ Single folder details. """
        return self.simple_get(request, pk)

    def folder_update(self, request, pk, data):
        """ Helper for updating folder details -- used by patch and put methods. """
        obj = self.get_object_for_user_by_pk(request.user, pk)
        try:
            return self.simple_update(obj, data)
        except InvalidMove as e:
            raise ValidationError({"parent":[e.args[0]]})

    @load_parent
    def patch(self, request, pk, format=None):
        """ Update folder. """
        return self.folder_update(request, pk, request.data)

    @load_parent
    def put(self, request, pk, format=None):
        """
            Move folder.
            For nested endpoint, PUT /folders/:id into /folders/:parent_id.
        """
        if not request.parent:
            raise_general_validation_error("PUT is only valid for nested folder endpoints.")
        return self.folder_update(request, pk, {'parent': request.parent.pk})

    @load_parent
    def delete(self, request, pk, format=None):
        """ Delete folder. """
        folder = self.get_object_for_user_by_pk(request.user, pk)

        # delete validations
        if folder.is_shared_folder or folder.is_root_folder:
            raise_general_validation_error("Top-level folders cannot be deleted.")
        elif not folder.is_empty():
            raise_general_validation_error("Folders can only be deleted if they are empty.")

        return self.simple_delete(folder)


### CAPTUREJOB VIEWS ###

# /capture_jobs
class CaptureJobListView(BaseView):
    serializer_class = CaptureJobSerializer

    def get(self, request, format=None):
        """ List capture_jobs for user. """
        queryset = CaptureJob.objects.select_related('link').filter(link__created_by_id=request.user.pk, status__in=['pending', 'in_progress'])
        return self.simple_list(request, queryset)


# /capture_jobs/:id
# /capture_jobs/:guid
class CaptureJobDetailView(BaseView):
    serializer_class = CaptureJobSerializer

    def get(self, request, pk=None, guid=None, format=None):
        """ Single capture_job details. """
        if guid:
            # We were called as /capture_jobs/:guid
            # Return capture_job for given link_id
            obj = self.get_object_for_user(request.user, CaptureJob.objects.filter(link_id=guid).select_related('link'))
            return self.simple_get(request, obj=obj)
        else:
            # We were called as /capture_jobs/:id
            return self.simple_get(request, pk)


### LINK VIEWS ###

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

    def surt_filter(self, queryset, name, value):
        try:
            canonicalized = surt.surt(value)
        except ValueError:
            return queryset
        return queryset.filter(submitted_url_surt=canonicalized)


# /public/archives
class PublicLinkListView(BaseView):
    permission_classes = ()  # no login required
    serializer_class = LinkSerializer
    filterset_class = LinkFilter
    search_fields = ('guid', 'submitted_url', 'submitted_title')  # fields that can be searched with q= query string

    def get(self, request, format=None):
        """ List public links. """
        queryset = Link.objects\
            .order_by('-creation_timestamp')\
            .select_related('capture_job')\
            .prefetch_related('captures').discoverable()
        return self.simple_list(request, queryset)

# /public/archives/:guid
class PublicLinkDetailView(BaseView):
    permission_classes = ()  # no login required
    serializer_class = LinkSerializer

    def get(self, request, guid, format=None):
        """ Get public link details. """
        try:
            obj = Link.objects.discoverable().get(pk=guid)
        except Link.DoesNotExist:
            raise Http404
        return self.simple_get(request, obj=obj)


#/public/archives/:guid/download
class PublicLinkDownloadView(BaseView):
    permission_classes = ()  # no login required
    serializer_class = LinkSerializer

    def get(self, request, guid, format=None):
        """ Download public link  """
        try:
            link = Link.objects.discoverable().get(pk=guid)
        except Link.DoesNotExist:
            raise Http404
        if link.replacement_link_id:
            return HttpResponseRedirect(reverse_api_view_relative('public_archives_download', kwargs={'guid': link.replacement_link_id}))
        return stream_warc(link)


# /archives
# /folders/:parent_id/archives
class AuthenticatedLinkListView(BaseView):
    serializer_class = AuthenticatedLinkSerializer
    filterset_class = LinkFilter
    search_fields = PublicLinkListView.search_fields + ('notes',)  # private links can also be searched by notes field

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
            Used by AuthenticatedLinkListView.get and AuthenticatedLinkListExportView.get
        """
        queryset = Link.objects\
            .order_by('-creation_timestamp')\
            .select_related('organization', 'organization__registrar', 'organization__shared_folder', 'capture_job', 'created_by')\
            .prefetch_related('captures')\
            .accessible_to(request.user)

        # for /folders/:parent_id/archives, limit to links in folder
        if request.parent:
            queryset = queryset.filter(folders=request.parent)

        return queryset

    @load_parent
    def get(self, request, format=None):
        """ List links for user. """
        return self.simple_list(request, self.load_links(request))

    @load_parent
    def post(self, request, format=None):
        """ Create new link. """
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
            submitted_url=submitted_url,
            created_by=request.user
        )

        # Batch is set directly on the request object by the LinkBatch api,
        # to prevent abuse of this feature by those POSTing directly to this route.
        if getattr(request, 'batch', None):
            capture_job.link_batch = LinkBatch.objects.get(id=request.batch)
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
                    url=link.submitted_url,
                ).save()

                # create screenshot placeholder
                Capture(
                    link=link,
                    role='screenshot',
                    status='pending',
                    record_type='resource',
                    url=f"file:///{link.guid}/cap.png",
                    content_type='image/png',
                ).save()


                # kick off capture tasks -- no need for guid since it'll work through the queue
                capture_job.status = 'pending'
                capture_job.link = link
                capture_job.save(update_fields=['status', 'link'])
                run_next_capture.delay()

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
        """ Single link details. """
        return self.simple_get(request, guid)

    def patch(self, request, guid, format=None):
        """ Update link. """
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
                link.mark_capturejob_superseded()

                # write new warc and capture
                link.write_uploaded_file(uploaded_file, cache_break=True)

            # update internet archive if privacy changes
            if 'is_private' in data and was_private != bool(data.get("is_private")) and link.is_permanent():
                if was_private:
                    # if link was private but has been marked public, mark it for upload.
                    link.internet_archive_upload_status = 'upload_or_reupload_required'
                else:
                    # if link was public but has been marked private, mark it for deletion.
                    link.internet_archive_upload_status = 'deletion_required'
                link.save(update_fields=["internet_archive_upload_status"])

            # include remaining links in response
            links_remaining = request.user.get_links_remaining()
            serializer.data['links_remaining'] = 'Infinity' if links_remaining[0] == float('inf') else links_remaining[0]
            serializer.data['links_remaining_period'] = links_remaining[1]

            return Response(serializer.data)

        raise ValidationError(serializer.errors)

    def delete(self, request, guid, format=None):
        """ Delete link. """
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
        """ Download warc. """
        link = self.get_object_for_user_by_pk(request.user, guid)
        if link.replacement_link_id:
            return HttpResponseRedirect(reverse_api_view_relative('archives_download', kwargs={'guid': link.replacement_link_id}))
        return stream_warc_if_permissible(link, request.user)


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


### LINKUSER ###

# /user
class LinkUserView(BaseView):
    serializer_class = LinkUserSerializer

    @load_parent
    def get(self, request, format=None):
        """ Get current user details. """
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)


### LINKBATCH ###

# /batches
class LinkBatchesListView(BaseView):
    serializer_class = LinkBatchSerializer
    queryset = (LinkBatch.objects
        # order capture_jobs for each batch by order they were run
        .prefetch_related(
            Prefetch(
                'capture_jobs',
                queryset=CaptureJob.objects.order_by('-human', 'order', 'pk').select_related('link')
            ))
        # order batches by most recent first
        .order_by('-started_on'))

    def get(self, request, format=None):
        """ List link batches for user. """
        return self.simple_list(request, serializer_class=DetailedLinkBatchSerializer)

    def post(self, request, format=None):
        """ Create link batch. """
        # mark batch with user
        if not request.user.is_authenticated:
            raise PermissionDenied()
        if request.content_type != 'application/json':
            content = {'detail': 'content-type must be aplication/json'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        request.data['created_by'] = request.user.pk

        # save batch
        serializer = self.serializer_class(data=request.data, context={'request': self.request})
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        serializer.save(created_by=request.user)

        # Attempt creation of Perma Links
        path = reverse_api_view_relative('archives')
        batch_id = serializer.data['id']
        call_list = [
            {
                'path': path,
                'verb': 'POST',
                'data': {
                    'url': url,
                    'folder': request.data['target_folder'],
                    'human': request.data.get('human', False)
                }
            } for url in request.data.get('urls', [])
        ]
        dispatch_multiple_requests(request, call_list, {"batch": batch_id})
        # TODO: how can we communicate these errors to the user?
        # if dispatch_multiple_requests returns to "responses"
        # internal_server_errors = [
        #     response['data']['data']['url'] for response in responses if response['status_code'] == 500
        # ]
        # Get an up-to-date version of this LinkBatch's data,
        # formatted by the LinkBatch serializer
        call_for_fresh_serializer_data = [{
            'path': reverse_api_view_relative('link_batch', kwargs={"pk": batch_id}),
            'verb': 'GET'
        }]
        response = dispatch_multiple_requests(request, call_for_fresh_serializer_data)
        data = response[0]['data'].copy()
        links_remaining = request.user.get_links_remaining()
        data['links_remaining'] = 'Infinity' if links_remaining[0] == float('inf') else links_remaining[0]
        data['links_remaining_period'] = links_remaining[1]
        return Response(data, status=status.HTTP_201_CREATED)


# /batches/:id
class LinkBatchesDetailView(BaseView):
    serializer_class = DetailedLinkBatchSerializer
    queryset = LinkBatchesListView.queryset.select_related('target_folder')

    def get(self, request, pk, format=None):
        """ Single link batch details. """
        return self.simple_get(request, pk)


# /batches/:id/export
class LinkBatchesDetailExportView(LinkBatchesDetailView):
    def get(self, request, pk, format=None):
        """ Single link batch details. """
        api_response = self.simple_get(request, pk)
        formatted_data = [
            {
                'url': job['submitted_url'],
                'status': "success",
                'error_message': "",
                'title': job['title'],
                'perma_link': f"{request.scheme}://{request.get_host()}/{job['guid']}"
            } if job['status'] == "completed" else {
                'url': job['submitted_url'],
                'status': "error",
                'error_message': job['message'],
                'title': "",
                "perma_link": ""
            }
            for job in api_response.data['capture_jobs']
        ]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="perma-batch-{pk}.csv"'
        if formatted_data:
            writer = csv.DictWriter(response, fieldnames=list(formatted_data[0].keys()))
            writer.writeheader()
            writer.writerows(formatted_data)
        return response
