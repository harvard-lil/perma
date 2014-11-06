from tastypie.authentication import ApiKeyAuthentication
from tastypie import fields
from tastypie.resources import ModelResource
from perma.models import LinkUser, Link, Asset, Folder, VestingOrg
from django.core.exceptions import ObjectDoesNotExist
from tastypie.exceptions import NotFound
from validations import LinkValidation
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
        authentication = ApiKeyAuthentication()
        authorization = DefaultAuthorization()
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
        fields = USER_FIELDS

class VestingOrgResource(ModelResource):
    class Meta:
        resource_name = 'vesting_orgs'
        queryset = VestingOrg.objects.all()
        fields = [
            'id',
            'name'
        ]

class LinkResource(MultipartResource, ModelResource):
    created_by = fields.ForeignKey(LinkUserResource, 'created_by', full=True, null=True, blank=True)
    vested_by_editor = fields.ForeignKey(LinkUserResource, 'vested_by_editor', full=True, null=True, blank=True)
    vesting_org = fields.ForeignKey(VestingOrgResource, 'vesting_org', full=True, null=True)

    class Meta:
        authentication = ApiKeyAuthentication()
        authorization = DefaultAuthorization()
        resource_name = 'archives'
        validation = LinkValidation()
        queryset = Link.objects.all()
        fields = [
            'guid',
            'created_by',
            'creation_timestamp',
            'submitted_title',
            'submitted_url',
            'notes',
            'vested',
            'vesting_org',
            'vested_timestamp',
            'vested_timestamp',
            'dark_archived',
            'dark_archived_robots_txt_blocked'
        ]

    def obj_create(self, bundle, **kwargs):
        # We've received a request to archive a URL. That process is managed here.
        # We create a new entry in our datastore and pass the work off to our indexing
        # workers. They do their thing, updating the model as they go. When we get some minimum
        # set of results we can present the user (a guid for the link), we respond back.

        url = bundle.data.get('url','').strip()
        if url[:4] != 'http':
            url = 'http://' + url

        # Runs validation (exception thrown if invalid), sets properties and saves the object
        bundle = super(LinkResource, self).obj_create(bundle,
                                                      created_by=bundle.request.user,
                                                      submitted_url=url,
                                                      submitted_title=bundle.data.get('title'))

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

            # If it appears as if we're trying to archive a PDF, only run our PDF retrieval tool
            if asset.link.media_type == 'pdf':
                asset.pdf_capture = 'pending'
                asset.image_capture = 'pending'
                asset.save()

                # run background celery tasks as a chain (each finishes before calling the next)
                run_task(chain(
                    get_pdf.s(asset.link.guid,
                              asset.link.submitted_url,
                              asset.base_storage_path,
                              bundle.request.META['HTTP_USER_AGENT']),
                    *postprocessing_tasks
                ))
            else:  # else, it's not a PDF. Let's try our best to retrieve what we can
                asset.image_capture = 'pending'
                asset.text_capture = 'pending'
                asset.warc_capture = 'pending'
                asset.save()

                # run background celery tasks as a chain (each finishes before calling the next)
                run_task(chain(
                    proxy_capture.s(asset.link.guid,
                                    asset.link.submitted_url,
                                    asset.base_storage_path,
                                    bundle.request.META['HTTP_USER_AGENT']),
                    *postprocessing_tasks
                ))

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
