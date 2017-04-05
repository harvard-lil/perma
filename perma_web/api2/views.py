import django_filters
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.http import Http404
from mptt.exceptions import InvalidMove
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import DjangoFilterBackend, SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from perma.utils import run_task
from perma.tasks import upload_to_internet_archive, delete_from_internet_archive, run_next_capture
from perma.models import Folder, CaptureJob, Link, Capture, Organization

from .utils import TastypiePagination, load_parent, raise_validation_error
from .serializers import FolderSerializer, CaptureJobSerializer, LinkSerializer, AuthenticatedLinkSerializer, \
    LinkUserSerializer, OrganizationSerializer


### BASE VIEW ###

class BaseView(APIView):
    permission_classes = (IsAuthenticated,)  # by default all users must be authenticated
    serializer_class = None  # overridden for each subclass

    # configure filtering of list endpoints by query string
    filter_backends = (
        DjangoFilterBackend,  # subclasses can be filtered by keyword if filter_class is set
        SearchFilter,         # subclasses can be filtered by q= if search_fields is set
        OrderingFilter        # subclasses can be ordered by order_by= if ordering_fields is set
    )
    ordering_fields = ()      # lock down order_by fields -- security risk if unlimited


    ### helpers ###

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
        ModelClass = self.serializer_class.Meta.model
        return self.get_object_for_user(user, ModelClass.objects.filter(pk=pk))


    ### basic views ###

    def simple_list(self, request, queryset):
        """
            Paginate and return a list of objects from given queryset.
        """
        queryset = self.filter_queryset(queryset)
        paginator = TastypiePagination()
        items = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(items, many=True)
        return paginator.get_paginated_response(serializer.data)

    def simple_get(self, request, pk=None, obj=None):
        """
            Return single serialized object based on either primary key or object already loaded.
        """
        if not obj:
            obj = self.get_object_for_user_by_pk(request.user, pk)
        serializer = self.serializer_class(obj)
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
            raise_validation_error("PUT is only valid for nested folder endpoints.")
        return self.folder_update(request, pk, {'parent': request.parent.pk})

    @load_parent
    def delete(self, request, pk, format=None):
        """ Delete folder. """
        folder = self.get_object_for_user_by_pk(request.user, pk)

        # delete validations
        if folder.is_shared_folder or folder.is_root_folder:
            raise_validation_error("Top-level folders cannot be deleted.")
        elif not folder.is_empty():
            raise_validation_error("Folders can only be deleted if they are empty.")

        return self.simple_delete(folder)


### CAPTUREJOB VIEWS ###

# /capture_jobs
class CaptureJobListView(BaseView):
    serializer_class = CaptureJobSerializer

    def get(self, request, format=None):
        """ List capture_jobs for user. """
        queryset = CaptureJob.objects.filter(link__created_by_id=request.user.pk, status__in=['pending', 'in_progress'])
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
    date = django_filters.IsoDateTimeFilter(name="creation_timestamp", lookup_expr='date')      # ?date=
    min_date = django_filters.IsoDateTimeFilter(name="creation_timestamp", lookup_expr='gte')   # ?min_date=
    max_date = django_filters.IsoDateTimeFilter(name="creation_timestamp", lookup_expr='lte')   # ?max_date=
    url = django_filters.CharFilter(name="submitted_url", lookup_expr='icontains')              # ?url=
    class Meta:
        model = Link
        fields = ['url', 'date', 'min_date', 'max_date']


# /public/archives
class PublicLinkListView(BaseView):
    permission_classes = ()  # no login required
    serializer_class = LinkSerializer
    filter_class = LinkFilter
    search_fields = ('guid', 'submitted_url', 'submitted_title')  # fields that can be searched with q= query string

    def get(self, request, format=None):
        """ List public links. """
        queryset = Link.objects.order_by('-creation_timestamp').prefetch_related('captures').discoverable()
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

# /archives
# /folders/:parent_id/archives
class AuthenticatedLinkListView(BaseView):
    serializer_class = AuthenticatedLinkSerializer
    filter_class = LinkFilter
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
            except Folder.DoesNotExist:
                raise ValidationError({'folder': ["Folder not found."]})
        return None

    @load_parent
    def get(self, request, format=None):
        """ List links for user. """
        queryset = Link.objects\
            .order_by('-creation_timestamp')\
            .select_related('organization', 'organization__registrar','capture_job')\
            .prefetch_related('captures')\
            .accessible_to(request.user)

        # for /folders/:parent_id/archives, limit to links in folder
        if request.parent:
            queryset = queryset.filter(folders=request.parent)

        return self.simple_list(request, queryset)

    @load_parent
    def post(self, request, format=None):
        """ Create new link. """
        data = request.data

        # Set target folder, in order of preference:
        # - 'folder' key in data
        # - parent folder, if posting to /folders/:parent_id/archives
        # - user's personal folder
        folder = self.get_folder_from_request(request) or request.parent or request.user.root_folder

        # Make sure a limited user has links left to create
        if not folder.organization:
            links_remaining = request.user.get_links_remaining()
            if links_remaining < 1:
                raise_validation_error("You've already reached your limit.")

        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():

            link = serializer.save(created_by=request.user)

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
                    url="file:///%s/cap.png" % link.guid,
                    content_type='image/png',
                ).save()

                # create CaptureJob
                CaptureJob(link=link, human=request.data.get('human', False)).save()

                # kick off capture tasks -- no need for guid since it'll work through the queue
                run_task(run_next_capture.s())

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

        serializer = self.serializer_class(link, data=data, partial=True, context={'request': self.request})
        if serializer.is_valid():
            serializer.save()

            # move to new folder
            folder = AuthenticatedLinkListView.get_folder_from_request(request)
            if folder:
                link.move_to_folder_for_user(folder, request.user)

            # handle file patch
            uploaded_file = request.data.get('file')
            if uploaded_file:

                # delete related cdxlines and captures, delete warc (rename)
                link.delete_related()
                link.safe_delete_warc()

                # write new warc and capture
                link.write_uploaded_file(uploaded_file, cache_break=True)

            # update internet archive if privacy changes
            if 'is_private' in data and was_private != bool(data.get("is_private")) and link.is_archive_eligible():
                if was_private:
                    # link was private but has been marked public
                    run_task(upload_to_internet_archive.s(link_guid=link.guid))

                else:
                    # link was public but has been marked private
                    run_task(delete_from_internet_archive.s(link_guid=link.guid))

            # include remaining links in response
            links_remaining = request.user.get_links_remaining()
            serializer.data['links_remaining'] = links_remaining

            # clear out any caches that might be based on old link data
            link.clear_cache()

            return Response(serializer.data)

        raise ValidationError(serializer.errors)

    def delete(self, request, guid, format=None):
        """ Delete link. """
        link = self.get_object_for_user_by_pk(request.user, guid)

        if not request.user.can_delete(link):
            raise PermissionDenied()

        link.delete_related()  # delete related captures and cdxlines
        link.safe_delete()
        link.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


# /folders/:parent_id/archives/:guid
class MoveLinkView(BaseView):
    serializer_class = AuthenticatedLinkSerializer

    @load_parent
    def put(self, request, guid, format=None):
        """
            Move link to new folder.
        """
        link = self.get_object_for_user_by_pk(request.user, guid)
        link.move_to_folder_for_user(request.parent, request.user)
        serializer = self.serializer_class(link)
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

