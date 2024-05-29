from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
import requests
from rest_framework import serializers

from perma.exceptions import ScoopAPIException
from perma.models import LinkUser, Folder, CaptureJob, Capture, Link, Organization, LinkBatch
from perma.utils import send_to_scoop

from .utils import get_mime_type, mime_type_lookup, reverse_api_view

import logging
logger = logging.getLogger(__name__)

class BaseSerializer(serializers.ModelSerializer):
    """ Base serializer from which all of our serializers inherit. """

    def update(self, instance, validated_data):
        """
            When updating, requiring that our serializers provide a whitelist of fields that can be updated.
            This is a safety check that avoids implementation errors where users can update fields that should only be set on create.
        """
        assert hasattr(self.Meta, 'allowed_update_fields'), "Serializers that are used for update must set Meta.allowed_update_fields"
        if set(validated_data.keys()) - set(self.Meta.allowed_update_fields):
            raise serializers.ValidationError(f'Only updates on these fields are allowed: {", ".join(self.Meta.allowed_update_fields)}')
        return super(BaseSerializer, self).update(instance, validated_data)


### LINKUSER ###

class LinkUserSerializer(BaseSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')
    short_name = serializers.ReadOnlyField(source='get_short_name')
    top_level_folders = serializers.SerializerMethodField()

    class Meta:
        model = LinkUser
        fields = ('id', 'first_name', 'last_name', 'full_name', 'short_name', 'top_level_folders')

    def get_field_names(self, *args, **kwargs):
        # Exclude the top_level_folders field when this serializer is nested inside another serializer.
        # This lets us use the same serializer at /user and also to embed created_by user info in /archives
        field_names = super(LinkUserSerializer, self).get_field_names(*args, **kwargs)
        if self.parent:
            field_names = [i for i in field_names if i != 'top_level_folders']
        return field_names

    def get_top_level_folders(self, user):
        serializer = FolderSerializer(user.top_level_folders(), many=True)
        return serializer.data


### FOLDER ###

class FolderSerializer(BaseSerializer):
    has_children = serializers.SerializerMethodField()
    path = serializers.CharField(source='cached_path', read_only=True)

    class Meta:
        model = Folder
        fields = ('id', 'name', 'parent', 'has_children', 'path', 'organization', 'sponsored_by', 'is_sponsored_root_folder', 'read_only')
        extra_kwargs = {'parent': {'required': True, 'allow_null': False}}
        allowed_update_fields = ['name', 'parent']

    def get_has_children(self, folder):
        return not folder.is_leaf_node()

    def validate_name(self, name):
        if self.instance:
            # renaming
            if self.instance.is_root_folder or \
               self.instance.is_shared_folder or \
               self.instance.is_sponsored_root_folder or \
               (self.instance.parent and self.instance.parent.is_sponsored_root_folder):
                raise serializers.ValidationError("Top-level folders cannot be renamed.")
        return name

    def validate_parent(self, parent):
        if self.instance:
            # moving
            if self.instance.is_shared_folder:
                raise serializers.ValidationError("You can't move organization's shared folder.")
            if self.instance.is_sponsored_root_folder:
                raise serializers.ValidationError("You can't move Sponsored Links folder.")
            if parent.is_sponsored_root_folder:
                raise serializers.ValidationError("You can't make top-level sponsored folders.")
            if self.instance.sponsorship and self.instance.parent == self.instance.sponsorship.user.sponsored_root_folder:
                raise serializers.ValidationError("You can't move top-level sponsored folders.")
            if self.instance.is_root_folder:
                raise serializers.ValidationError("You can't move Personal Links folder.")
            if self.instance.id == parent.id:
                raise serializers.ValidationError("A node may not be made a child of itself.")
            if parent.id in list(self.instance.get_descendants().tree_filter(tree_root__id=self.instance.tree_root_id).values_list('id', flat=True)):
                raise serializers.ValidationError("A node may not be made a child of any of its descendants.")
        return parent

    def validate(self, data):
        if 'name' in data:
            # make sure folder name is unique in this location
            parent_id = data['parent'].pk if 'parent' in data else self.instance.parent_id if self.instance else None
            if parent_id:
                unique_query = Folder.objects.filter(parent_id=parent_id, name=data['name'])
                if self.instance:
                    unique_query = unique_query.exclude(pk=self.instance.pk)
                if unique_query.exists():
                    raise serializers.ValidationError({'name':"A folder with that name already exists at that location."})
        return data


### ORGANIZATION ###

class OrganizationSerializer(BaseSerializer):
    registrar = serializers.StringRelatedField()
    shared_folder = FolderSerializer()

    class Meta:
        model = Organization
        fields = ('id', 'name', 'registrar', 'default_to_private', 'shared_folder')


### CAPTUREJOB ###

class CaptureJobSerializer(BaseSerializer):
    guid = serializers.PrimaryKeyRelatedField(source='link', read_only=True)
    title = serializers.SerializerMethodField()
    user_deleted = serializers.SerializerMethodField()

    class Meta:
        model = CaptureJob
        fields = ('guid', 'status', 'message', 'submitted_url', 'attempt', 'step_count', 'step_description', 'capture_start_time', 'capture_end_time', 'queue_position', 'title', 'user_deleted')

    def get_title(self, capture_job):
        if capture_job.link is None:
            return ""
        else:
            return capture_job.link.submitted_title

    def get_user_deleted(self, capture_job):
        return capture_job.link and capture_job.link.user_deleted

### CAPTURE ###

class CaptureSerializer(BaseSerializer):
    class Meta:
        model = Capture
        fields = ('role', 'status', 'url', 'record_type', 'content_type', 'user_upload')


### LINK ###

class LinkSerializer(BaseSerializer):
    url = serializers.CharField(source='submitted_url', max_length=2100, required=False, allow_blank=True)
    title = serializers.CharField(source='submitted_title', max_length=2100, required=False)
    description = serializers.CharField(source='submitted_description', allow_blank=True, allow_null=True, max_length=300, required=False)

    captures = CaptureSerializer(many=True, read_only=True)
    queue_time = serializers.SerializerMethodField()
    capture_time = serializers.SerializerMethodField()
    warc_download_url = serializers.SerializerMethodField()

    class Meta:
        model = Link
        fields = ('guid', 'creation_timestamp', 'url', 'title', 'description', 'warc_size', 'warc_download_url', 'captures', 'queue_time', 'capture_time')

    def get_queue_time(self, link):
        try:
            delta = link.capture_job.capture_start_time - link.creation_timestamp
            return delta.seconds
        except (ObjectDoesNotExist, TypeError):
            return None

    def get_capture_time(self, link):
        try:
            delta = link.capture_job.capture_end_time - link.capture_job.capture_start_time
            return delta.seconds
        except (ObjectDoesNotExist, TypeError):
            return None

    def get_warc_download_url(self, link):
        if link.warc_size:
            return reverse_api_view('public_archives_download', kwargs={'guid': link.guid}, request=self.context['request'])
        return None


class AuthenticatedLinkSerializer(LinkSerializer):
    """
        Subclass of LinkSerializer with extra fields for users who own the link.
    """
    created_by = LinkUserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)

    class Meta(LinkSerializer.Meta):
        fields = LinkSerializer.Meta.fields + ('notes', 'created_by', 'is_private', 'private_reason', 'user_deleted', 'archive_timestamp', 'organization', 'default_to_screenshot_view')
        allowed_update_fields = ['submitted_title', 'submitted_description', 'notes', 'is_private', 'private_reason', 'default_to_screenshot_view']

    def get_warc_download_url(self, link):
        if link.warc_size:
            return reverse_api_view('archives_download', kwargs={'guid': link.guid}, request=self.context['request'])
        return None

    def validate_url(self, url):
        # Clean up the user submitted url
        url = url.strip()
        if url and url[:4] != 'http':
            url = 'http://' + url
        return url

    def validate(self, data):
        user = self.context['request'].user
        errors = {}

        # since 'file' is not a field on the model, we have to access it through request.data rather than data
        uploaded_file = self.context['request'].data.get('file')

        # handle is_private and private_reason:
        if self.instance:
            if not user.is_staff:
                # only staff can manually change private_reason in all cases
                data.pop('private_reason', None)

                # if updating privacy, make sure user is allowed to change private status
                if 'is_private' in data and self.instance.is_private != bool(data['is_private']):
                    if self.instance.private_reason and self.instance.private_reason not in ['user', 'meta']:
                        errors['is_private'] = 'Cannot change link privacy.'
                    else:
                        data['private_reason'] = 'user' if data['is_private'] else None
        else:
            # for new links, set private_reason based on is_private
            data['private_reason'] = 'user' if data.get('is_private') else None

        # check submitted URL for new link
        if not self.instance:
            if not data.get('submitted_url'):
                errors['url'] = "URL cannot be empty."
            else:
                if uploaded_file:
                    # Validate, but don't force URL validation if a file is provided
                    validate = URLValidator()
                    temp_link = Link(submitted_url=data['submitted_url'])
                    validate(temp_link.ascii_safe_url)
                else:
                    # Ask the Scoop API to validate and resolve the URL
                    try:
                        _, response_data = send_to_scoop(
                            method="post",
                            path="validate",
                            json={"url": Link.get_ascii_safe_url(data['submitted_url'])},
                            timeout=settings.RESOURCE_LOAD_TIMEOUT,
                            valid_if=lambda code, data: code == 200 and "valid" in data,
                        )
                        if not response_data["valid"]:
                            errors['url'] = response_data["message"]
                        elif content_length := response_data.get('content_length'):
                            if content_length > settings.MAX_ARCHIVE_FILE_SIZE:
                                errors['url'] = f"Target page is too large (max size {settings.MAX_ARCHIVE_FILE_SIZE / 1024 / 1024}MB)."
                    except ScoopAPIException:
                        logger.exception("Scoop validation attempt failed.")
                        errors['url'] = "We encountered a network error: please try again."

        # check uploaded file
        if uploaded_file == '':
            errors['file'] = "File cannot be blank."
        elif uploaded_file:

            if self.instance and self.instance.is_permanent():
                errors['file'] = "Archive contents cannot be replaced after 24 hours"

            else:
                mime_type = get_mime_type(uploaded_file.name)

                # Get mime type string from tuple
                if not mime_type or not mime_type_lookup[mime_type]['valid_file'](uploaded_file):
                    errors['file'] = "Invalid file."
                elif uploaded_file.size > settings.MAX_ARCHIVE_FILE_SIZE:
                    errors['file'] = "File is too large."

                elif not errors.get('file') and settings.SCAN_UPLOADS:
                    uploaded_file.file.seek(0)
                    try:
                        r = requests.post(
                            settings.SCAN_URL,
                            files={'file': (uploaded_file.name, uploaded_file.file.read())}
                        )
                        assert r.ok, r.status_code
                        scan_results = r.json()
                    except (requests.RequestException, AssertionError) as e:
                        scan_results = {"safe": False, "reason": f"Communication with filecheck API failed: {str(e)}"}

                    if not scan_results['safe']:
                        if scan_results['reason'].startswith("Communication with filecheck API failed"):
                            # Report the error, but pass the file through.
                            logger.error(scan_results['reason'])
                        elif scan_results['reason'] in ["clamav not running", "clamav out of date"]:
                            # Report the error, but pass the file through.
                            msg = f"Filecheck service reports: {scan_results['reason']}"
                            logger.error(msg)
                        else:
                            # Report the error and block the file.
                            msg = f"Unsafe file upload attempt by user {user.id}: {scan_results['reason']}"
                            logger.warning(msg)
                            errors['file'] = "Validation failed."

        if errors:
            raise serializers.ValidationError(errors)

        return data


### LINKBATCH ###

class LinkBatchSerializer(BaseSerializer):
    capture_jobs = CaptureJobSerializer(many=True, read_only=True)

    class Meta:
        model = LinkBatch
        fields = ('id', 'started_on', 'created_by', 'capture_jobs', 'target_folder')


class DetailedLinkBatchSerializer(LinkBatchSerializer):
    target_folder = FolderSerializer(read_only=True)
