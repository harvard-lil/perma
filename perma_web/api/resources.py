import json

from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import NoReverseMatch
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from extendedmodelresource import ExtendedModelResource
from mptt.exceptions import InvalidMove
from tastypie import fields
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.utils import trailing_slash
from tastypie import http
from tastypie.resources import ModelResource
from tastypie.exceptions import NotFound, ImmediateHttpResponse, BadRequest

from validations import (LinkValidation,
                         FolderValidation,
                         mime_type_lookup,
                         get_mime_type,
                         DefaultValidation)

from perma.models import (LinkUser,
                          Link,
                          Folder,
                          Organization,
                          Registrar,
                          Capture,
                          CaptureJob)

from authentication import (DefaultAuthentication,
                            CurrentUserAuthentication)

from authorizations import (FolderAuthorization,
                            LinkAuthorization,
                            CurrentUserAuthorization,
                            CurrentUserOrganizationAuthorization,
                            PublicLinkAuthorization,
                            AuthenticatedLinkAuthorization,
                            CurrentUserNestedAuthorization,
                            CurrentUserCaptureJobAuthorization)

from serializers import DefaultSerializer

# LinkResource
from perma.utils import run_task
from perma.tasks import proxy_capture, upload_to_internet_archive, delete_from_internet_archive, run_next_capture


class DefaultResource(ExtendedModelResource):
    class Meta:
        authentication = DefaultAuthentication()
        authorization = ReadOnlyAuthorization()
        always_return_data = True
        include_resource_uri = False
        serializer = DefaultSerializer()
        validation = DefaultValidation()
        allowed_update_fields = []

    @classmethod
    # Hack to prevent ModelResource from auto-including additional fields
    def get_fields(cls, fields=None, excludes=None):
        return []

    # Convert a resource public key to a uri that tastypie can consume
    def pk_to_uri(self, resource, pk):
        return resource().get_resource_uri(resource._meta.object_class(pk=pk))

    def put_url_params_to_patch(self, request, **kwargs):
        # Only allow PUT
        if request.method != 'PUT':
            raise ImmediateHttpResponse(response=http.HttpNotImplemented())

        # Mimic a PATCH request
        request.method = 'PATCH'

        # Modify request body
        try:
            data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        except:
            data = {}

        for k in kwargs.keys():
            if k not in ['api_name', 'resource_name', self._meta.detail_uri_name]:
                # Use pop() so as to remove the url params from kwargs filters
                data[k] = kwargs.pop(k)

        request._body = json.dumps(data)
        request.META['CONTENT_TYPE'] = 'application/json'

        # Call dispatch_detail as though it was originally a PATCH
        return self.dispatch_detail(request, **kwargs)

    def as_json(self, obj, request=None):
        """
            Serialize an object as JSON,
            using the privileges of the requesting user if supplied.
        """
        bundle = self.build_bundle(obj=obj, request=request)
        return self.serialize(None, self.full_dehydrate(bundle), 'application/json')

    # http://stackoverflow.com/questions/11076396/tastypie-list-related-resources-keys-instead-of-urls
    def many_to_many_to_ids(self, bundle, field_name):
        field_ids = getattr(bundle.obj, field_name).values_list('id', flat=True)
        field_ids = map(int, field_ids)
        return field_ids

    # http://stackoverflow.com/questions/11076396/tastypie-list-related-resources-keys-instead-of-urls
    def foreign_key_to_id(self, bundle, field_name):
        field = getattr(bundle.obj, field_name)
        field_id = getattr(field, 'id', None)
        return field_id

    def build_bundle(self, obj=None, data=None, request=None, objects_saved=None):
        """ Inject parent_object into bundle (this assumes it was already injected into the request object. """
        bundle = super(DefaultResource, self).build_bundle(obj, data, request, objects_saved)
        bundle.parent_object = getattr(request, 'parent_object', None)
        return bundle

    def dispatch(self, request_type, request, **kwargs):
        """ Inject parent_object into request object. """
        request.parent_object = kwargs.get('parent_object', None)
        return super(DefaultResource, self).dispatch(request_type, request, **kwargs)

    def raise_error_response(self, bundle, errors):
        raise ImmediateHttpResponse(response=self.error_response(bundle.request, errors))

    def _handle_500(self, request, exception):
        if settings.READ_ONLY_MODE:
            return self.error_response(request, {
                'error_message':"Perma is in read only mode for scheduled maintenance. Please try again shortly."
            })
        return super(DefaultResource, self)._handle_500(request, exception)

    def update_in_place(self, request, original_bundle, new_data):
        """
            Make sure that only allowed fields are updated.
            Via http://stackoverflow.com/a/17111959
        """
        if set(new_data.keys()) - set(self._meta.allowed_update_fields):
            raise BadRequest('Only updates on these fields are allowed: %s' % ', '.join(self._meta.allowed_update_fields))

        return super(DefaultResource, self).update_in_place(request, original_bundle, new_data)


# via: http://stackoverflow.com/a/14134853/313561
# also: https://github.com/toastdriven/django-tastypie/issues/42#issuecomment-5485666
class MultipartResource(object):
    def deserialize(self, request, data, format=None):
        if not format:
            format = request.META.get('CONTENT_TYPE', 'application/json')
        if format == 'application/x-www-form-urlencoded':
            return request.POST
        if format.startswith('multipart'):
            data = request.POST.copy()
            data.update(request.FILES)
            return data
        return super(MultipartResource, self).deserialize(request, data, format)


class LinkUserResource(DefaultResource):
    id = fields.IntegerField(attribute='id')
    first_name = fields.CharField(attribute='first_name', blank=True, null=True)
    last_name = fields.CharField(attribute='last_name', blank=True, null=True)
    full_name = fields.CharField(attribute='get_full_name', blank=True, null=True)
    short_name = fields.CharField(attribute='get_short_name', blank=True, null=True)

    class Meta(DefaultResource.Meta):
        resource_name = 'users'
        queryset = LinkUser.objects.all()


class OrganizationResource(DefaultResource):
    id = fields.IntegerField(attribute='id')
    name = fields.CharField(attribute='name')
    registrar = fields.CharField(attribute='registrar__name')
    default_to_private = fields.BooleanField(attribute='default_to_private', null=True, blank=True)
    shared_folder = fields.ForeignKey('api.resources.FolderResource', 'shared_folder', null=True, blank=True, full=True)

    class Meta(DefaultResource.Meta):
        resource_name = 'organizations'
        queryset = Organization.objects.select_related('registrar', 'shared_folder')
        ordering = ['name', 'registrar']

    class Nested:
        folders = fields.ToManyField('api.resources.FolderResource', 'folders', null=True)


class RegistrarResource(DefaultResource):
    id = fields.IntegerField(attribute='id')
    name = fields.CharField(attribute='name')

    class Meta(DefaultResource.Meta):
        resource_name = 'registrars'
        queryset = Registrar.objects.all()

    class Nested:
        organizations = fields.ToManyField('api.resources.OrganizationResource', 'organizations', null=True)


class FolderResource(DefaultResource):
    id = fields.IntegerField(attribute='id')
    name = fields.CharField(attribute='name')
    parent = fields.ForeignKey('api.resources.FolderResource', 'parent', null=True, blank=True)

    class Meta(DefaultResource.Meta):
        resource_name = 'folders'
        queryset = Folder.objects.all()
        authorization = FolderAuthorization()
        validation = FolderValidation()
        limit = 300
        max_limit = 300
        allowed_update_fields = ['name', 'parent']

    class Nested:
        folders = fields.ToManyField('api.resources.FolderResource', 'children', full=True, readonly=True)
        archives = fields.ToManyField('api.resources.LinkResource', 'links', full=True, readonly=True)

    def dehydrate_parent(self, bundle):
        return self.foreign_key_to_id(bundle, 'parent')

    def prepend_urls(self):
        return [
            # /folders/<parent>/folders/<pk>/
            url(r"^(?P<resource_name>%s)/(?P<parent>\d+)/%s/(?P<%s>\d+)%s$" % (self._meta.resource_name, self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('put_url_params_to_patch'), name="api_move_folder"),
        ]

    def hydrate_name(self, bundle):
        # Clean up the user submitted name
        if bundle.data.get('name', None):
            bundle.data['name'] = bundle.data['name'].strip()
        return bundle

    def hydrate_parent(self, bundle):
        # If the user passed a parent id, grab the uri
        # but don't make a DB call - we'll validate it later
        if bundle.data.get('parent', None):
            try:
                # int() sniffs if an id has been passed
                int(bundle.data['parent'])
                bundle.data['parent'] = self.pk_to_uri(FolderResource,
                                                       bundle.data['parent'])
            except ValueError:
                pass

        return bundle

    def post_list(self, request, **kwargs):
        # Bypass extendedmodelresource as it doesn't allow nested post_list
        return super(ModelResource, self).post_list(request, **kwargs)

    def obj_create(self, bundle, **kwargs):
        # Assign the parent folder on nested post_list
        if 'parent_object' in kwargs:
            kwargs = {'parent': kwargs['parent_object']}

        kwargs['created_by'] = bundle.request.user
        return super(FolderResource, self).obj_create(bundle, **kwargs)

    def obj_update(self, bundle, skip_errors=False, **kwargs):
        try:
            super(FolderResource, self).obj_update(bundle, skip_errors, **kwargs)
        except InvalidMove as e:
            self.raise_error_response(bundle, {"parent":e.args[0]})


class CaptureJobResource(DefaultResource):
    guid = fields.CharField(attribute='link_id')
    status = fields.CharField(attribute='status')
    attempt = fields.IntegerField(attribute='attempt')
    step_count = fields.FloatField(attribute='step_count')
    step_description = fields.CharField(attribute='step_description', blank=True, null=True)
    capture_start_time = fields.DateTimeField(attribute='capture_start_time', blank=True, null=True)
    capture_end_time = fields.DateTimeField(attribute='capture_end_time', blank=True, null=True)

    # calculated fields
    queue_position = fields.DateTimeField(attribute='queue_position')

    class Meta(DefaultResource.Meta):
        resource_name = 'capture_jobs'
        queryset = CaptureJob.objects.all()
        detail_uri_name = 'link_id'

    def prepend_urls(self):
        """ URLs should match on CaptureJob.link_id as well as CaptureJob.id. """
        return [
            url(r"^(?P<resource_name>%s)/(?P<link_id>[\w\d-]+)/?$" % self._meta.resource_name,
                self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class CaptureResource(DefaultResource):
    role = fields.CharField(attribute='role', null=True, blank=True)
    status = fields.CharField(attribute='status', null=True, blank=True)
    url = fields.CharField(attribute='url', null=True, blank=True)
    record_type = fields.CharField(attribute='record_type', null=True, blank=True)
    content_type = fields.CharField(attribute='content_type', null=True, blank=True)
    user_upload = fields.BooleanField(attribute='user_upload', null=True, blank=True)

    # calculated fields
    playback_url = fields.CharField(attribute='playback_url', null=True, blank=True)

    class Meta(DefaultResource.Meta):
        resource_name = 'captures'
        queryset = Capture.objects.all()
        filtering = {'archive': ['exact']}

    def dehydrate_archive(self, bundle):
        return {'guid': bundle.data['archive']}


class BaseLinkResource(MultipartResource, DefaultResource):
    """
        This resource is not used directly, but is subclassed by the endpoints that show archives.

        Class hierarchy:

        Resource                            Authentication Class (if not inherited)     Endpoint URL
        --------------                      ---------------------------------------     ------------
        BaseLinkResource
            PublicLinkResource              PublicLinkAuthentication                    /public/archives
            AuthenticatedLinkResource       AuthenticatedLinkResource
                LinkResource                LinkAuthentication                          /archives
                LinkResource                                                            /folders/<id>/archives
                LinkResource                                                            /user/organizations/<id>/folders
                CurrentUserLinkResource                                                 /user/archives
    """

    always_return_data = True
    guid = fields.CharField(attribute='guid', readonly=True)
    view_count = fields.IntegerField(attribute='view_count', default=1, readonly=True)
    creation_timestamp = fields.DateTimeField(attribute='creation_timestamp', readonly=True)
    url = fields.CharField(attribute='submitted_url')
    title = fields.CharField(attribute='submitted_title', blank=True)
    captures = fields.ToManyField(CaptureResource, 'captures', readonly=True, full=True)

    class Meta(DefaultResource.Meta):
        resource_name = 'archives'
        queryset = Link.objects.order_by('-creation_timestamp').select_related('organization', 'organization__registrar').prefetch_related('captures')
        validation = LinkValidation()

    # class Nested:
    #     captures = fields.ToManyField(CaptureResource, 'captures')

    def apply_filters(self, request, applicable_filters):
        base_object_list = super(BaseLinkResource, self).apply_filters(request, applicable_filters)

        search_query = request.GET.get('q', None)
        if search_query:
            return base_object_list.filter(self.get_search_filters(search_query))
        else:
            return base_object_list

    def get_search_filters(self, search_query):
        return (Q(guid__icontains=search_query) |
                Q(submitted_url__icontains=search_query) |
                Q(submitted_title__icontains=search_query))


class PublicLinkResource(BaseLinkResource):
    class Meta(BaseLinkResource.Meta):
        resource_name = 'public/' + BaseLinkResource.Meta.resource_name
        authorization = PublicLinkAuthorization()
        serializer = DefaultSerializer(formats=['json', 'jsonp'])  # enable jsonp

    def dehydrate_organization(self, bundle):
        # The org for a given link may or may not be public.
        # For now, just mark all as private.
        return None


class AuthenticatedLinkResource(BaseLinkResource):
    notes = fields.CharField(attribute='notes', blank=True)
    created_by = fields.ForeignKey(LinkUserResource, 'created_by', full=True, null=True, blank=True, readonly=True)

    is_private = fields.BooleanField(attribute='is_private')
    private_reason = fields.CharField(attribute='private_reason', blank=True, null=True)
    archive_timestamp = fields.DateTimeField(attribute='archive_timestamp', readonly=True)
    organization = fields.ForeignKey(OrganizationResource, 'organization', full=True, blank=True, null=True, readonly=True)

    class Meta(BaseLinkResource.Meta):
        authorization = AuthenticatedLinkAuthorization()
        queryset = BaseLinkResource.Meta.queryset.select_related('created_by',)
        allowed_update_fields = ['title', 'notes', 'is_private', 'private_reason', 'folder']

    def get_search_filters(self, search_query):
        return (super(AuthenticatedLinkResource, self).get_search_filters(search_query) |
                Q(notes__icontains=search_query))


class LinkResource(AuthenticatedLinkResource):

    class Meta(AuthenticatedLinkResource.Meta):
        authorization = LinkAuthorization()

    def prepend_urls(self):
        return [
            url(r"^%s/(?P<folder>\w[\w/-]*)/(?P<resource_name>%s)/(?P<%s>[^\./]+)%s$" % (
                FolderResource()._meta.resource_name, self._meta.resource_name, self._meta.detail_uri_name,
                trailing_slash()), self.wrap_view('put_url_params_to_patch'), name="api_move_archive"),
        ]

    def hydrate_url(self, bundle):
        # Clean up the user submitted url
        if bundle.data.get('url', None):
            url = bundle.data.get('url', '').strip()
            if url[:4] != 'http':
                url = 'http://' + url

            bundle.data['url'] = url
        return bundle

    def hydrate_is_private(self, bundle):
        if 'is_private' in bundle.data:
            if not bundle.data.get('private_reason'):
                if bundle.obj.is_private and not bundle.data['is_private']:
                    bundle.data['private_reason'] = None
                elif not bundle.obj.is_private and bundle.data['is_private']:
                    bundle.data['private_reason'] = 'user'

        return bundle

    def hydrate_human(self, bundle):
        if 'human' in bundle.data:
            bundle.data['human'] = bool(bundle.data['human'])
        return bundle

    def hydrate(self, bundle):
        if bundle.data.get('folder', None):
            try:
                bundle.data['folder'] = Folder.objects.accessible_to(bundle.request.user).get(pk=bundle.data['folder'])
            except Folder.DoesNotExist:
                self.raise_error_response(bundle, {'folder': "Folder not found."})
        elif not bundle.obj.pk:
            # If this is a newly created link and no folder was provided, default to user's My Links folder.
            bundle.data['folder'] = bundle.request.user.root_folder
        return bundle

    def obj_create(self, bundle, **kwargs):
        # We've received a request to archive a URL. That process is managed here.
        # We create a new entry in our datastore and pass the work off to our indexing
        # workers. They do their thing, updating the model as they go. When we get some minimum
        # set of results we can present the user (a guid for the link), we respond back.
        if settings.READ_ONLY_MODE:
            raise ImmediateHttpResponse(response=self.error_response(bundle.request, {
                'archives': {'__all__': "Perma has paused archive creation for scheduled maintenance. Please try again shortly."},
                'reason': "Perma has paused archive creation for scheduled maintenance. Please try again shortly.",
            }))
        
        # Runs validation (exception thrown if invalid), sets properties and saves the object
        bundle = super(LinkResource, self).obj_create(bundle, created_by=bundle.request.user)
        link = bundle.obj

        # put link in folder and handle Org settings based on folder
        folder = bundle.data.get('folder')
        if folder.organization and folder.organization.default_to_private:
            link.is_private = True
            link.save()
        link.move_to_folder_for_user(folder, bundle.request.user)  # also sets link.organization

        uploaded_file = bundle.data.get('file')
        if uploaded_file:
            # normalize file name to upload.jpg, upload.png, upload.gif, or upload.pdf
            mime_type = get_mime_type(uploaded_file.name)
            file_name = 'upload.%s' % mime_type_lookup[mime_type]['new_extension']
            warc_url = "file:///%s/%s" % (link.guid, file_name)

            capture = Capture(link=link,
                              role='primary',
                              status='success',
                              record_type='resource',
                              user_upload='True',
                              content_type=mime_type,
                              url=warc_url)

            uploaded_file.file.seek(0)
            capture.write_warc_resource_record(uploaded_file)
            capture.save()

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
            CaptureJob(link=link, human=bundle.data.get('human', False)).save()

            # kick off capture tasks -- no need for guid since it'll work through the queue
            run_task(run_next_capture.s())

        return bundle

    def obj_update(self, bundle, skip_errors=False, **kwargs):
        is_private = bundle.obj.is_private
        bundle = super(LinkResource, self).obj_update(bundle, skip_errors, **kwargs)

        if bundle.data.get('folder', None):
            bundle.obj.move_to_folder_for_user(bundle.data['folder'], bundle.request.user)

        if 'is_private' in bundle.data:
            if bundle.obj.is_archive_eligible():
                going_private = bundle.data.get("is_private")
                # if link was private but has been marked public
                if is_private and not going_private:
                    run_task(upload_to_internet_archive.s(link_guid=bundle.obj.guid))

                # if link was public but has been marked private
                elif not is_private and going_private:
                    run_task(delete_from_internet_archive.s(link_guid=bundle.obj.guid))

        links_remaining = bundle.request.user.get_links_remaining()
        bundle.data['links_remaining'] = links_remaining
        return bundle

    # https://github.com/toastdriven/django-tastypie/blob/ec16d5fc7592efb5ea86321862ec0b5962efba1b/tastypie/resources.py#L2194
    def obj_delete(self, bundle, **kwargs):
        if not hasattr(bundle.obj, 'delete'):
            try:
                bundle.obj = self.obj_get(bundle=bundle, **kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")

        self.authorized_delete_detail(self.get_object_list(bundle.request), bundle)

        bundle.obj.safe_delete()
        bundle.obj.save()
        if bundle.obj.uploaded_to_internet_archive:
            run_task(delete_from_internet_archive.s(link_guid=bundle.obj.guid))

    ###
    # Allow cross-domain requests from insecure site to secure site.
    # This allows us to update the loading icons for live-view single-link page for insecure links.
    # Can be removed when we stop showing that view.
    ###

    def add_cors_headers(self, request, response):
        response['Access-Control-Allow-Origin'] = 'http://%s' % settings.HOST
        response['Access-Control-Allow-Headers'] = 'content-type, authorization, x-requested-with'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    def get_detail(self, request, **kwargs):
        """ Allow single-link mirror pages to read link details from the main server. """
        response = super(LinkResource, self).get_detail(request, **kwargs)
        self.add_cors_headers(request, response)
        return response

    def method_check(self, request, allowed=None):
        """
            Check for an OPTIONS request. If so return the Allow- headers.
            Based on https://gist.github.com/miraculixx/6536381
        """
        try:
            return super(LinkResource, self).method_check(request, allowed)
        except ImmediateHttpResponse as response_exception:
            if request.method.lower() == "options":
                self.add_cors_headers(request, response_exception.response)
            raise


class CurrentUserResource(LinkUserResource):
    class Meta(DefaultResource.Meta):
        resource_name = 'user'
        queryset = LinkUser.objects.all()[:0] # needed for /schema to render
        authentication = CurrentUserAuthentication()
        authorization = CurrentUserAuthorization()
        list_allowed_methods = []
        detail_allowed_methods = ['get']

    # Limit the url to only the first route (/resource) and schema to allow nested resources
    def base_urls(self):
        return super(CurrentUserResource, self).base_urls()[0:2]

    # Map the detail view to the list view so that detail shows at the resource root
    def dispatch_list(self, request, **kwargs):
        return self.dispatch_detail(request, **kwargs)

    def obj_get(self, bundle, **kwargs):
        '''
        Always returns the logged in user.
        '''
        return bundle.request.user

    # Build the URI (included in the JSON response) to match our remapped dispatch_list
    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        bundle_or_obj = None
        try:
            return self._build_reverse_url(url_name, kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''


class CurrentUserNestedResource(object):
    class Meta(DefaultResource.Meta):
        authentication = CurrentUserAuthentication()
        authorization = CurrentUserNestedAuthorization()

    def obj_create(self, bundle, **kwargs):
        """
        Assign created objects to the current user
        """
        return super(CurrentUserNestedResource, self).obj_create(bundle, created_by=bundle.request.user)


class CurrentUserLinkResource(CurrentUserNestedResource, AuthenticatedLinkResource):
    class Meta(CurrentUserNestedResource.Meta, AuthenticatedLinkResource.Meta):
        resource_name = 'user/' + AuthenticatedLinkResource.Meta.resource_name
        authorization = AuthenticatedLinkAuthorization()


class CurrentUserFolderResource(CurrentUserNestedResource, FolderResource):
    class Meta(CurrentUserNestedResource.Meta, FolderResource.Meta):
        resource_name = 'user/' + FolderResource.Meta.resource_name


class CurrentUserOrganizationResource(CurrentUserNestedResource, OrganizationResource):
    class Meta(CurrentUserNestedResource.Meta, OrganizationResource.Meta):
        resource_name = 'user/' + OrganizationResource.Meta.resource_name
        authorization = CurrentUserOrganizationAuthorization()


class CurrentUserCaptureJobResource(CurrentUserNestedResource, CaptureJobResource):
    class Meta(CurrentUserNestedResource.Meta, CaptureJobResource.Meta):
        resource_name = 'user/' + CaptureJobResource.Meta.resource_name
        authorization = CurrentUserCaptureJobAuthorization()