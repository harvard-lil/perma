import json
from mimetypes import MimeTypes
import os

from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import NoReverseMatch
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.core.files.storage import default_storage

from extendedmodelresource import ExtendedModelResource
from mptt.exceptions import InvalidMove
from tastypie import fields
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash
from tastypie import http
from tastypie.resources import ModelResource
from tastypie.exceptions import NotFound, ImmediateHttpResponse

from validations import LinkValidation, FolderValidation
from perma.models import (LinkUser,
                          Link,
                          Asset,
                          Folder,
                          VestingOrg,
                          Registrar)

from authentication import (DefaultAuthentication,
                            CurrentUserAuthentication)

from authorizations import (FolderAuthorization,
                            LinkAuthorization,
                            CurrentUserAuthorization,
                            CurrentUserVestingOrgAuthorization, PublicLinkAuthorization,
                            AuthenticatedLinkAuthorization)

# LinkResource
from perma.utils import run_task
from perma.tasks import get_pdf, proxy_capture, upload_to_internet_archive



class DefaultResource(ExtendedModelResource):
    class Meta:
        authentication = DefaultAuthentication()
        authorization = ReadOnlyAuthorization()
        always_return_data = True
        include_resource_uri = False

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


class VestingOrgResource(DefaultResource):
    id = fields.IntegerField(attribute='id')
    name = fields.CharField(attribute='name')

    class Meta(DefaultResource.Meta):
        resource_name = 'vesting_orgs'
        queryset = VestingOrg.objects.all()

    class Nested:
        folders = fields.ToManyField('api.resources.FolderResource', 'folders', null=True)


class RegistrarResource(DefaultResource):
    id = fields.IntegerField(attribute='id')
    name = fields.CharField(attribute='name')

    class Meta(DefaultResource.Meta):
        resource_name = 'registrars'
        queryset = Registrar.objects.all()

    class Nested:
        vesting_orgs = fields.ToManyField('api.resources.VestingOrgResource', 'vesting_orgs', null=True)


class FolderResource(DefaultResource):
    id = fields.IntegerField(attribute='id')
    name = fields.CharField(attribute='name')
    parent = fields.ForeignKey('api.resources.FolderResource', 'parent', null=True, blank=True)

    class Meta(DefaultResource.Meta):
        resource_name = 'folders'
        queryset = Folder.objects.all()
        authorization = FolderAuthorization()
        validation = FolderValidation()

    class Nested:
        folders = fields.ToManyField('api.resources.FolderResource', 'children', full=True, readonly=True)
        archives = fields.ToManyField('api.resources.LinkResource', 'links', full=True, readonly=True)

    def dehydrate_parent(self, bundle):
        return self.foreign_key_to_id(bundle, 'parent')

    def prepend_urls(self):
        return [
            # /folders/<parent>/folders/<pk>/
            url(r"^(?P<resource_name>%s)/(?P<parent>\w[\w/-]*)/%s/(?P<%s>.*?)%s$" % (self._meta.resource_name, self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('put_url_params_to_patch'), name="api_move_folder"),
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


class AssetResource(DefaultResource):
    base_storage_path = fields.CharField(attribute='base_storage_path', null=True, blank=True)
    favicon = fields.CharField(attribute='favicon', null=True, blank=True)
    image_capture = fields.CharField(attribute='image_capture', null=True, blank=True)
    warc_capture = fields.CharField(attribute='warc_capture', null=True, blank=True)
    pdf_capture = fields.CharField(attribute='pdf_capture', null=True, blank=True)
    text_capture = fields.CharField(attribute='text_capture', null=True, blank=True)

    class Meta(DefaultResource.Meta):
        resource_name = 'assets'
        queryset = Asset.objects.all()
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
            AuthorizedLinkResource          AuthorizedLinkAuthentication
                LinkResource                LinkAuthentication                          /archives
                LinkResource                                                            /folders/<id>/archives
                LinkResource                                                            /user/vesting_orgs/<id>/folders
                CurrentUserLinkResource                                                 /user/archives
    """

    always_return_data = True
    guid = fields.CharField(attribute='guid', readonly=True)
    view_count = fields.IntegerField(attribute='view_count', default=1)
    creation_timestamp = fields.DateTimeField(attribute='creation_timestamp', readonly=True)
    url = fields.CharField(attribute='submitted_url')
    title = fields.CharField(attribute='submitted_title', blank=True)
    vested = fields.BooleanField(attribute='vested', blank=True, default=False)
    vested_timestamp = fields.DateTimeField(attribute='vested_timestamp', readonly=True, null=True)
    dark_archived = fields.BooleanField(attribute='dark_archived', blank=True, default=False)
    dark_archived_robots_txt_blocked = fields.BooleanField(attribute='dark_archived_robots_txt_blocked', blank=True, default=False)
    expiration_date = fields.DateTimeField(attribute='get_expiration_date', readonly=True)
    vesting_org = fields.ForeignKey(VestingOrgResource, 'vesting_org', full=True, blank=True, null=True)
    assets = fields.ToManyField(AssetResource, 'assets', readonly=True, full=True)

    class Meta(DefaultResource.Meta):
        resource_name = 'archives'
        queryset = Link.objects.all().order_by('-creation_timestamp')  # default order
        validation = LinkValidation()

    class Nested:
        assets = fields.ToManyField(AssetResource, 'assets')

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
        serializer = Serializer(formats=['json', 'jsonp'])  # enable jsonp


class AuthenticatedLinkResource(BaseLinkResource):
    notes = fields.CharField(attribute='notes', blank=True)
    created_by = fields.ForeignKey(LinkUserResource, 'created_by', full=True, null=True, blank=True, readonly=True)
    vested_by_editor = fields.ForeignKey(LinkUserResource, 'vested_by_editor', full=True, null=True, blank=True,
                                         readonly=True)
    dark_archived_by = fields.ForeignKey(LinkUserResource, 'dark_archived_by', full=True, null=True, blank=True,
                                         readonly=True)
    # folders = fields.ToManyField(FolderResource, 'folders', readonly=True, null=True)

    class Meta(BaseLinkResource.Meta):
        authorization = AuthenticatedLinkAuthorization()

    def get_search_filters(self, search_query):
        return (super(AuthenticatedLinkResource, self).get_search_filters(search_query) |
                Q(notes__icontains=search_query))


class LinkResource(AuthenticatedLinkResource):

    class Meta(BaseLinkResource.Meta):
        authorization = LinkAuthorization()

    def prepend_urls(self):
        return [
            url(r"^%s/(?P<folder>\w[\w/-]*)/(?P<resource_name>%s)/(?P<%s>.*?)%s$" % (
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

    def hydrate_dark_archived(self, bundle):
        if not bundle.obj.dark_archived and bundle.data.get('dark_archived', None):
            bundle.obj.dark_archived_by = bundle.request.user

        return bundle

    def hydrate_vested(self, bundle):
        if not bundle.obj.vested and bundle.data.get('vested', None):
            bundle.obj.vested_by_editor = bundle.request.user
            bundle.obj.vested_timestamp = timezone.now()

        return bundle

    def hydrate_vesting_org(self, bundle):
        if bundle.data.get('vested', None) and not bundle.obj.vesting_org:
            # If the user passed a vesting org id, grab the object.
            # Permissions will be checked later.
            if bundle.data.get('vesting_org', None):
                try:
                    bundle.data['vesting_org'] = VestingOrg.objects.get(pk=bundle.data['vesting_org'])
                except VestingOrg.DoesNotExist:
                    self.raise_error_response(bundle, {'vesting_org':"Vesting org not found."})
            # A folder was passed in via URL during vest i.e. /folders/123/archives/ABC-EFG
            elif bundle.data.get('folder', None):
                bundle.data['vesting_org'] = bundle.data['folder'].vesting_org
            elif VestingOrg.objects.accessible_to(bundle.request.user).count() == 1:
                bundle.data['vesting_org'] = VestingOrg.objects.accessible_to(bundle.request.user).first()
        else:
            # Clear out the vesting_org so it's not updated otherwise
            bundle.data.pop('vesting_org', None)

        return bundle

    def hydrate(self, bundle):
        if bundle.data.get('folder', None):
            try:
                bundle.data['folder'] = Folder.objects.get(pk=bundle.data['folder'])
            except Folder.DoesNotExist:
                self.raise_error_response(bundle, {'folder': "Folder not found."})
        return bundle

    def obj_create(self, bundle, **kwargs):
        # We've received a request to archive a URL. That process is managed here.
        # We create a new entry in our datastore and pass the work off to our indexing
        # workers. They do their thing, updating the model as they go. When we get some minimum
        # set of results we can present the user (a guid for the link), we respond back.

        # Runs validation (exception thrown if invalid), sets properties and saves the object
        bundle = super(LinkResource, self).obj_create(bundle, created_by=bundle.request.user)
        asset = Asset(link=bundle.obj)

        uploaded_file = bundle.data.get('file')
        if uploaded_file:
            mime = MimeTypes()
            mime_type = mime.guess_type(uploaded_file.name)[0]
            file_name = 'cap' + mime.guess_extension(mime_type)
            file_path = os.path.join(asset.base_storage_path, file_name)

            uploaded_file.file.seek(0)
            file_name = default_storage.store_file(uploaded_file, file_path)

            if mime_type == 'application/pdf':
                asset.pdf_capture = file_name
            else:
                asset.image_capture = file_name
            asset.save()
        else:
            asset.image_capture = 'pending'
            # If it appears as if we're trying to archive a PDF, only run our PDF retrieval tool
            if asset.link.media_type == 'pdf':
                asset.pdf_capture = 'pending'
                task = get_pdf
            else:  # else, it's not a PDF. Let's try our best to retrieve what we can
                asset.warc_capture = 'pending'
                task = proxy_capture

            asset.save()
            run_task(task.s(asset.link.guid,
                            asset.link.submitted_url,
                            asset.base_storage_path,
                            bundle.request.META.get('HTTP_USER_AGENT', '')))

        return bundle

    def obj_update(self, bundle, skip_errors=False, **kwargs):
        was_vested = bundle.obj.vested

        bundle = super(LinkResource, self).obj_update(bundle, skip_errors, **kwargs)

        if bundle.data.get('folder', None):
            bundle.obj.move_to_folder_for_user(bundle.data['folder'], bundle.request.user)

        if not was_vested and bundle.obj.vested:
            if settings.UPLOAD_TO_INTERNET_ARCHIVE and bundle.obj.can_upload_to_internet_archive():
                run_task(upload_to_internet_archive, link_guid=bundle.obj.guid)

        return bundle

    # https://github.com/toastdriven/django-tastypie/blob/ec16d5fc7592efb5ea86321862ec0b5962efba1b/tastypie/resources.py#L2194
    def obj_delete(self, bundle, **kwargs):
        if not hasattr(bundle.obj, 'delete'):
            try:
                bundle.obj = self.obj_get(bundle=bundle, **kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")

        self.authorized_delete_detail(self.get_object_list(bundle.request), bundle)

        bundle.obj.user_deleted = True
        bundle.obj.user_deleted_timestamp = timezone.now()
        bundle.obj.save()

    def add_cors_headers(self, request, response):
        response['Access-Control-Allow-Origin'] = "http%s://%s" % ("s" if request.is_secure() else "", request.mirror_server_host)
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
        authentication = CurrentUserAuthentication()
        authorization = CurrentUserAuthorization()
        list_allowed_methods = []
        detail_allowed_methods = ['get']

    # Limit the url to only the first route (/resource) to allow nested resources
    def base_urls(self):
        return [super(CurrentUserResource, self).base_urls()[0]]

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
        authorization = CurrentUserAuthorization()

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


class CurrentUserVestingOrgResource(CurrentUserNestedResource, VestingOrgResource):
    class Meta(CurrentUserNestedResource.Meta, VestingOrgResource.Meta):
        resource_name = 'user/' + VestingOrgResource.Meta.resource_name
        authorization = CurrentUserVestingOrgAuthorization()
