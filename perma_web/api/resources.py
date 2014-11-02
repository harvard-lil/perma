from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie import fields
from tastypie.resources import ModelResource
from perma.models import LinkUser, Link, Folder, VestingOrg

# LinkResource
import socket
from urlparse import urlparse
from django.core.validators import URLValidator
from netaddr import IPAddress, IPNetwork
import requests
from django.conf import settings

HEADER_CHECK_TIMEOUT = 10

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
        authorization = Authorization()
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

class LinkResource(ModelResource):
    created_by = fields.ForeignKey(LinkUserResource, 'created_by', full=True, null=True, blank=True)
    vested_by_editor = fields.ForeignKey(LinkUserResource, 'vested_by_editor', full=True, null=True, blank=True)
    vesting_org = fields.ForeignKey(VestingOrgResource, 'vesting_org', full=True, null=True)

    class Meta:
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        resource_name = 'archives'
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

        target_url = bundle.data["url"].strip()

        # If we don't get a protocol, assume http
        if target_url[:4] != 'http':
            target_url = 'http://' + target_url

        # Does this thing look like a valid URL?
        validate = URLValidator()
        try:
            validate(target_url)
        except ValidationError:
            return HttpResponseBadRequest("Not a valid URL.")

        # By default, use the domain as title
        url_details = urlparse(target_url)
        target_title = url_details.netloc

        # Check for banned IP.
        try:
            target_ip = socket.gethostbyname(url_details.netloc.split(':')[0])
        except socket.gaierror:
            return HttpResponseBadRequest("Couldn't resolve domain.")
        for banned_ip_range in settings.BANNED_IP_RANGES:
            if IPAddress(target_ip) in IPNetwork(banned_ip_range):
                return HttpResponseBadRequest("Not a valid IP.")

        # Get target url headers. We get the mime-type and content length from this.
        try:
            target_url_headers = requests.head(
                target_url,
                verify=False, # don't check SSL cert?
                headers={'User-Agent': bundle.request.META['HTTP_USER_AGENT'], 'Accept-Encoding':'*'},
                timeout=HEADER_CHECK_TIMEOUT
            ).headers
        except (requests.ConnectionError, requests.Timeout):
            return HttpResponseBadRequest("Couldn't load URL.")
        try:
            if int(target_url_headers.get('content-length', 0)) > 1024 * 1024 * 100:
                return HttpResponseBadRequest("Target page is too large (max size 1MB).")
        except ValueError:
            # Weird -- content-length header wasn't an integer. Carry on.
            pass

        return super(LinkResource, self).obj_create(bundle, created_by=bundle.request.user, submitted_url=target_url, submitted_title=target_title)

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
