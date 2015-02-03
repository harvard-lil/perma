from tastypie.validation import Validation
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from netaddr import IPAddress, IPNetwork
from mimetypes import MimeTypes
from PyPDF2 import PdfFileReader
import imghdr

from django.conf import settings
from perma.models import Folder


class LinkValidation(Validation):

    def is_valid_ip(self, ip):
        for banned_ip_range in settings.BANNED_IP_RANGES:
            if IPAddress(ip) in IPNetwork(banned_ip_range):
                return False
        return True

    def is_valid_size(self, headers):
        try:
            if int(headers.get('content-length', 0)) > settings.MAX_HTTP_FETCH_SIZE:
                return False
        except ValueError:
            # Weird -- content-length header wasn't an integer. Carry on.
            pass
        return True

    def is_valid_file(self, upload, mime_type):
        # Make sure files are not corrupted.
        if mime_type == 'image/jpeg':
            return imghdr.what(upload) == 'jpeg'
        elif mime_type == 'image/png':
            return imghdr.what(upload) == 'png'
        elif mime_type == 'image/gif':
            return imghdr.what(upload) == 'gif'
        elif mime_type == 'application/pdf':
            doc = PdfFileReader(upload)
            if doc.numPages >= 0:
                return True
        return False

    def is_valid(self, bundle, request=None):
        if not bundle.data:
            return {'__all__': 'No data provided.'}
        errors = {}

        if bundle.data.get('url', '') == '':
            if not bundle.obj.pk:  # if it's a new entry
                errors['url'] = "URL cannot be empty."
        elif bundle.obj.tracker.has_changed('submitted_url'):  # url is aliased to submitted_url in the API
            try:
                validate = URLValidator()
                validate(bundle.data.get('url'))

                # Don't force URL resolution validation if a file is provided
                if not bundle.data.get('file', None):
                    if not bundle.obj.ip:
                        errors['url'] = "Couldn't resolve domain."
                    elif not self.is_valid_ip(bundle.obj.ip):
                        errors['url'] = "Not a valid IP."
                    elif not bundle.obj.headers:
                        errors['url'] = "Couldn't load URL."
                    elif not self.is_valid_size(bundle.obj.headers):
                        errors['url'] = "Target page is too large (max size 1MB)."
            except ValidationError:
                errors['url'] = "Not a valid URL."

        if bundle.data.get('file', None):
            mime = MimeTypes()
            mime_type = mime.guess_type(bundle.data.get('file').name)[0]

            # Get mime type string from tuple
            if not mime_type or not self.is_valid_file(bundle.data.get('file'), mime_type):
                errors['file'] = "Invalid file."
            elif bundle.data.get('file').size > settings.MAX_ARCHIVE_FILE_SIZE:
                errors['file'] = "File is too large."

        # Vesting
        if bundle.data.get('vested', None) and bundle.obj.tracker.has_changed('vested'):
            if not bundle.obj.vesting_org:
                errors['vesting_org'] = "vesting_org can't be blank"
            elif not bundle.obj.folders.filter(vesting_org=bundle.obj.vesting_org):
                # if not currently in the vesting org's folder, the folder needs to be supplied
                if not bundle.data.get("folder", None):
                    errors['folder'] = "This archive is not currently in the vesting org's folder. Please specify a folder belonging to the vesting org when vesting."
                else:
                    if bundle.data['folder'].vesting_org != bundle.obj.vesting_org:
                        errors['folder'] = "the folder must belong to the vesting_org"

        # Moving folder when not vesting
        elif bundle.data.get("folder", None):
            if bundle.obj.vested and bundle.obj.vesting_org_id != bundle.data['folder'].vesting_org_id:
                errors['folder'] = "Vested archives cannot be moved out of the vesting organization's shared folder."

        return errors


class FolderValidation(Validation):
    def is_valid(self, bundle, request=None):
        errors = {}

        # For renaming
        if bundle.obj.tracker.has_changed("name"):
            if bundle.obj.is_shared_folder:
                errors['name'] = "Shared folders cannot be renamed."
            elif bundle.obj.is_root_folder:
                errors['name'] = "User's main folder cannot be renamed."

        # For moving
        if bundle.obj.tracker.has_changed("parent_id"):
            if not bundle.obj.parent_id:
                errors['parent'] = "Can't move folder to top level."
            elif bundle.obj.is_shared_folder:
                errors['parent'] = "Can't move vesting organization's shared folder."
            elif bundle.obj.is_root_folder:
                errors['parent'] = "Can't move user's main folder."
            elif bundle.obj.vesting_org_id and bundle.obj.vesting_org_id != bundle.obj.parent.vesting_org_id and bundle.obj.contained_links().filter(vested=True).exists():
                errors['parent'] = "Can't move folder with vested links out of organization's shared folder."

        return errors
