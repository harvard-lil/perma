from tastypie.validation import Validation
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
from django.core.exceptions import ValidationError

HEADER_CHECK_TIMEOUT = 10
# This the is the PhantomJS default agent
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/534.34 (KHTML, like Gecko) PhantomJS/1.9.0 (development) Safari/534.34"

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


class Page(object):
    def __init__(self,
                 url=None,
                 title=None,
                 ip=None,
                 headers=None,
                 details=None):
        self._url = None
        self._title = None
        self._ip = None
        self._headers = None
        self._details = None

        self.url = url
        self.title = title

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        if value:
            value = value.strip()
            if value[:4] != 'http':
                value = 'http://' + value
            validate = URLValidator()
            validate(value) # throw an exception if the it's not a valid url
        if value != self._url:
            # Reset derived values if the url changes
            self._url = value
            self._title = None
            self._details = None
            self._ip = None
            self._headers = None

    @property
    def title(self):
        # By default, use the domain as title
        return self._title or self.details.netloc

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def details(self):
        if not self._details:
            self._details = urlparse(self.url)

        return self._details

    @property
    def ip(self):
        if self._ip is None:
            try:
                self._ip = socket.gethostbyname(self.details.netloc.split(':')[0])
            except socket.gaierror:
                self._ip = False

        return self._ip

    @property
    def headers(self):
        if self._headers is None:
            try:
                self._headers = requests.head(
                    self.url,
                    verify=False, # don't check SSL cert?
                    headers={'User-Agent': USER_AGENT, 'Accept-Encoding':'*'},
                    timeout=HEADER_CHECK_TIMEOUT
                ).headers
            except (requests.ConnectionError, requests.Timeout):
                self._headers = False

        return self._headers

class LinkValidation(Validation):
    def is_valid_ip(self, ip):
        for banned_ip_range in settings.BANNED_IP_RANGES:
            if IPAddress(ip) in IPNetwork(banned_ip_range):
                return False
        return True

    def is_valid_size(self, headers):
        try:
            if int(headers.get('content-length', 0)) > 1024 * 1024 * 100:
                return False
        except ValueError:
            # Weird -- content-length header wasn't an integer. Carry on.
            pass
        return True

    def is_valid(self, bundle, request=None):
        # We've received a request to archive a URL. That process is managed here.
        # We create a new entry in our datastore and pass the work off to our indexing
        # workers. They do their thing, updating the model as they go. When we get some minimum
        # set of results we can present the user (a guid for the link), we respond back.

        if not bundle.data:
            return {'__all__': 'No data provided.'}
        errors = {}

        if bundle.data.get('url', '') == '':
            errors['url'] = "URL cannot be empty."
        else:
            try:
                page = Page(url=bundle.data["url"])
                if not page.ip:
                    errors['url'] = "Couldn't resolve domain."
                elif not self.is_valid_ip(page.ip):
                    errors['url'] = "Not a valid IP."
                elif not page.headers:
                    errors['url'] = "Couldn't load URL."
                elif not self.is_valid_size(page.headers):
                    errors['url'] = "Target page is too large (max size 1MB)."
                else:
                    # Assign the vals to the bundle
                    bundle.obj.submitted_url = page.url
                    bundle.obj.submitted_title = page.title
            except ValidationError:
                errors['url'] = "Not a valid URL."

        return errors

class LinkResource(ModelResource):
    created_by = fields.ForeignKey(LinkUserResource, 'created_by', full=True, null=True, blank=True)
    vested_by_editor = fields.ForeignKey(LinkUserResource, 'vested_by_editor', full=True, null=True, blank=True)
    vesting_org = fields.ForeignKey(VestingOrgResource, 'vesting_org', full=True, null=True)

    class Meta:
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
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
        return super(LinkResource, self).obj_create(bundle, created_by=bundle.request.user)

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
