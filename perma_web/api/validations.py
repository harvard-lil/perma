from requests import TooManyRedirects
from tastypie.validation import Validation
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from netaddr import IPAddress, IPNetwork
from PyPDF2 import PdfFileReader
import imghdr

from django.conf import settings

# Map allowed file extensions to mime types.
# WARNING: If you change this, also change `accept=""` in create-link.html
file_extension_lookup = {
    'jpg':'image/jpeg',
    'jpeg':'image/jpeg',
    'pdf':'application/pdf',
    'png':'image/png',
    'gif':'image/gif',
}

# Map allowed mime types to new file extensions and validation functions.
# We manually pick the new extension instead of using MimeTypes().guess_extension,
# because that varies between systems.
mime_type_lookup = {
    'image/jpeg':{
        'new_extension':'jpg',
        'valid_file': lambda f: imghdr.what(f) == 'jpeg',
    },
    'image/png': {
        'new_extension': 'png',
        'valid_file': lambda f: imghdr.what(f) == 'png',
    },
    'image/gif': {
        'new_extension': 'gif',
        'valid_file': lambda f: imghdr.what(f) == 'gif',
    },
    'application/pdf': {
        'new_extension': 'pdf',
        'valid_file': lambda f: PdfFileReader(f).numPages >= 0,
    }
}

def get_mime_type(file_name):
    """ Return mime type (for a valid file extension) or None if file extension is unknown. """
    file_extension = file_name.rsplit('.', 1)[-1].lower()
    return file_extension_lookup.get(file_extension)

class LinkValidation(Validation):

    def is_valid_ip(self, ip):
        for banned_ip_range in settings.BANNED_IP_RANGES:
            if IPAddress(ip) in IPNetwork(banned_ip_range):
                return False
        return True

    def is_valid_size(self, headers):
        # If we get a PDF, check its file size as we download it
        # and don't worry about what the header tells us about size
        if headers.get('content-type', '').lower() == 'application/pdf':
            return True

        try:
            # If it's not a PDF trust the value in the header
            if int(headers.get('content-length', 0)) > settings.MAX_HTTP_FETCH_SIZE:
                return False
        except ValueError:
            # Weird -- content-length header wasn't an integer. Carry on.
            pass
        return True

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
                validate(bundle.data.get('url').replace(' ', '%20'))

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
            except TooManyRedirects:
                errors['url'] = "URL caused a redirect loop."

        uploaded_file = bundle.data.get('file')
        if uploaded_file:
            mime_type = get_mime_type(uploaded_file.name)

            # Get mime type string from tuple
            if not mime_type or not mime_type_lookup[mime_type]['valid_file'](uploaded_file):
                errors['file'] = "Invalid file."
            elif uploaded_file.size > settings.MAX_ARCHIVE_FILE_SIZE:
                errors['file'] = "File is too large."

        # Vesting
        if bundle.data.get('vested', None) and bundle.obj.tracker.has_changed('vested'):
            if not bundle.obj.organization:
                errors['organization'] = "organization can't be blank"
            elif not bundle.obj.folders.filter(organization=bundle.obj.organization):
                # if not currently in the org's folder, the folder needs to be supplied
                if not bundle.data.get("folder", None):
                    errors['folder'] = "This archive is not currently in the org's folder. Please specify a folder belonging to the org when vesting."
                else:
                    if bundle.data['folder'].organization != bundle.obj.organization:
                        errors['folder'] = "the folder must belong to the organization"

        # Moving folder when not organization
        elif bundle.data.get("folder", None):
            if bundle.obj.vested and bundle.obj.organization_id != bundle.data['folder'].organization_id:
                errors['folder'] = "Vested archives cannot be moved out of the organization's shared folder."

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
                errors['parent'] = "Can't move organization's shared folder."
            elif bundle.obj.is_root_folder:
                errors['parent'] = "Can't move user's main folder."
            elif bundle.obj.organization_id and bundle.obj.organization_id != bundle.obj.parent.organization_id and bundle.obj.contained_links().filter(vested=True).exists():
                errors['parent'] = "Can't move folder with vested links out of organization's shared folder."

        return errors
