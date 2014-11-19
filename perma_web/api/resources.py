from tastypie import fields
from tastypie.resources import ModelResource
from perma.models import LinkUser, Link, Asset, Folder, VestingOrg
from django.conf.urls import url
from tastypie.utils import trailing_slash
from django.core.exceptions import ObjectDoesNotExist
from tastypie.exceptions import NotFound
from validations import LinkValidation

from tastypie.authentication import ApiKeyAuthentication
from authentication import DefaultAuthentication

from tastypie.authorization import ReadOnlyAuthorization
from authorizations import DefaultAuthorization

# LinkResource
from celery import chain
from django.conf import settings
from perma.utils import run_task
from perma.tasks import get_pdf, proxy_capture
from mirroring.tasks import compress_link_assets, poke_mirrors
from mimetypes import MimeTypes
import os
from django.core.files.storage import default_storage
from datetime import datetime


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

USER_FIELDS = [
    'id',
    'first_name',
    'last_name'
]

class CurrentUserResource(ModelResource):
    class Meta:
        resource_name = 'user'
        queryset = LinkUser.objects.all()
        always_return_data = True
        authentication = ApiKeyAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = []
        detail_allowed_methods = ['get']
        fields = USER_FIELDS

    def dispatch_list(self, request, **kwargs):
        return self.dispatch_detail(request, **kwargs)

    def obj_get(self, bundle, **kwargs):
        '''
        Always returns the logged in user.
        '''
        return bundle.request.user

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        bundle_or_obj = None
        try:
            return self._build_reverse_url(url_name, kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''

class LinkUserResource(ModelResource):
    class Meta:
        resource_name = 'users'
        queryset = LinkUser.objects.all()
        always_return_data = True
        fields = USER_FIELDS

class VestingOrgResource(ModelResource):
    class Meta:
        resource_name = 'vesting_orgs'
        queryset = VestingOrg.objects.all()
        always_return_data = True
        fields = [
            'id',
            'name'
        ]

class AssetResource(ModelResource):
    # archive = fields.ForeignKey(LinkResource, 'link', full=False, null=False, readonly=True)
    archive = fields.CharField(attribute='link_id')

    class Meta:
        resource_name = 'assets'
        queryset = Asset.objects.all()
        filtering = { 'archive': ['exact'] }
        always_return_data = True

    def dehydrate_archive(self, bundle):
        return {'guid': bundle.data['archive']}

class LinkResource(MultipartResource, ModelResource):
    guid = fields.CharField(attribute='guid', readonly=True)
    creation_timestamp = fields.DateTimeField(attribute='creation_timestamp', readonly=True)
    url = fields.CharField(attribute='submitted_url')
    title = fields.CharField(attribute='submitted_title', blank=True)
    notes = fields.CharField(attribute='notes', blank=True)
    vested = fields.BooleanField(attribute='vested', blank=True, default=False)
    vested_timestamp = fields.DateTimeField(attribute='vested_timestamp', readonly=True, null=True)
    dark_archived = fields.BooleanField(attribute='dark_archived', blank=True, default=False)
    dark_archived_robots_txt_blocked = fields.BooleanField(attribute='dark_archived_robots_txt_blocked', blank=True, default=False)
    # Relationships
    created_by = fields.ForeignKey(LinkUserResource, 'created_by', full=True, null=True, blank=True, readonly=True)
    vested_by_editor = fields.ForeignKey(LinkUserResource, 'vested_by_editor', full=True, null=True, blank=True, readonly=True)
    vesting_org = fields.ForeignKey(VestingOrgResource, 'vesting_org', full=True, null=True, readonly=True)
    # assets = fields.ToManyField(AssetResource, 'assets', full=True, readonly=True)

    class Meta:
        resource_name = 'archives'
        queryset = Link.objects.all()
        fields = [None] # prevents ModelResource from auto-including additional fields
        authentication = DefaultAuthentication()
        authorization = DefaultAuthorization(user_field='created_by')
        validation = LinkValidation()
        always_return_data = True

    # via: http://django-tastypie.readthedocs.org/en/latest/cookbook.html#nested-resources
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/assets%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_assets_list'), name="api_get_assets_list"),
        ]

    def get_assets_list(self, request, **kwargs):
        try:
            bundle = self.build_bundle(data={'pk': kwargs['pk']}, request=request)
            obj = self.cached_obj_get(bundle=bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        asset_resource = AssetResource()
        return asset_resource.get_list(request, archive=obj.pk)
        
    def hydrate_url(self, bundle):
        # Clean up the user submitted url
        if bundle.data.get('url', None):
            url = bundle.data.get('url','').strip()
            if url[:4] != 'http':
                url = 'http://' + url

            bundle.data['url'] = url
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
            # celery tasks to run after scraping is complete
            postprocessing_tasks = []
            if settings.MIRRORING_ENABLED:
                postprocessing_tasks += [
                    compress_link_assets.s(guid=asset.link.guid),
                    poke_mirrors.s(link_guid=asset.link.guid),
                ]

            asset.image_capture = 'pending'
            task_args = [asset.link.guid,
                         asset.link.submitted_url,
                         asset.base_storage_path,
                         bundle.request.META.get('HTTP_USER_AGENT', '')]

            # If it appears as if we're trying to archive a PDF, only run our PDF retrieval tool
            if asset.link.media_type == 'pdf':
                asset.pdf_capture = 'pending'

                # run background celery tasks as a chain (each finishes before calling the next)
                run_task(chain(
                    get_pdf.s(*task_args),
                    *postprocessing_tasks
                ))
            else:  # else, it's not a PDF. Let's try our best to retrieve what we can
                asset.text_capture = 'pending'
                asset.warc_capture = 'pending'

                # run background celery tasks as a chain (each finishes before calling the next)
                run_task(chain(
                    proxy_capture.s(*task_args),
                    *postprocessing_tasks
                ))

            asset.save()

        return bundle

    # https://github.com/toastdriven/django-tastypie/blob/ec16d5fc7592efb5ea86321862ec0b5962efba1b/tastypie/resources.py#L2194
    def obj_delete(self, bundle, **kwargs):
        if not hasattr(bundle.obj, 'delete'):
            try:
                bundle.obj = self.obj_get(bundle=bundle, **kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")

        self.authorized_delete_detail(self.get_object_list(bundle.request), bundle)
        if not bundle.obj.user_deleted and not bundle.obj.vested:
            bundle.obj.user_deleted=True
            bundle.obj.user_deleted_timestamp=datetime.now()
            bundle.obj.save()

class FolderResource(ModelResource):
    class Meta:
        resource_name = 'folders'
        queryset = Folder.objects.all()
        always_return_data = True
        fields = [
            'creation_timestamp',
            'id',
            'is_root_folder',
            'is_shared_folder',
            'level',
            'lft',
            'name',
            'resource_uri',
            'rght',
            'slug',
            'tree_id'
        ]
