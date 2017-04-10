from perma.models import Folder
from perma.utils import ip_in_allowed_ip_range
from requests import TooManyRedirects
from tastypie.validation import Validation
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
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

def validate_pdf(f):
    return '%PDF-' in f.read(10)

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
        'valid_file': validate_pdf,
    }
}

def get_mime_type(file_name):
    """ Return mime type (for a valid file extension) or None if file extension is unknown. """
    file_extension = file_name.rsplit('.', 1)[-1].lower()
    return file_extension_lookup.get(file_extension)


class DefaultValidation(Validation):
    pass


class LinkValidation(DefaultValidation):

    def is_valid_size(self, headers):
        # preemptively reject URLs that report a size over settings.MAX_ARCHIVE_FILE_SIZE
        try:
            if int(headers.get('content-length', 0)) > settings.MAX_ARCHIVE_FILE_SIZE:
                return False
        except ValueError:
            # Weird -- content-length header wasn't an integer. Carry on.
            pass
        return True

    def is_valid(self, bundle, request=None):
        errors = super(LinkValidation, self).is_valid(bundle, request)

        if not bundle.data:
            errors['__all__'] = 'No data provided.'
            return errors

        # Make sure a limited user has links left to create
        if not bundle.obj.pk:  # if it's a new entry
            if not bundle.data.get('folder').organization:
                links_remaining = bundle.request.user.get_links_remaining()
                if links_remaining < 1:
                    errors['__all__'] = "You've already reached your limit."
                    return errors
                bundle.data['links_remaining'] = links_remaining - 1
            else:
                bundle.data['links_remaining'] = 'unlimited'

        errors = {}
        if bundle.data.get('url', '') == '':
            if not bundle.obj.pk:  # if it's a new entry
                errors['url'] = "URL cannot be empty."
        elif bundle.obj.tracker.has_changed('submitted_url'):  # url is aliased to submitted_url in the API
            try:
                validate = URLValidator()
                validate(bundle.obj.safe_url)

                # Don't force URL resolution validation if a file is provided
                if not bundle.data.get('file', None):
                    if not bundle.obj.ip:
                        errors['url'] = "Couldn't resolve domain."
                    elif not ip_in_allowed_ip_range(bundle.obj.ip):
                        errors['url'] = "Not a valid IP."
                    elif not bundle.obj.headers:
                        errors['url'] = "Couldn't load URL."
                    elif not self.is_valid_size(bundle.obj.headers):
                        errors['url'] = "Target page is too large (max size 1MB)."
            except UnicodeError:
                # see https://github.com/harvard-lil/perma/issues/1841
                errors['url'] = "Unicode error while processing URL."
            except ValidationError:
                errors['url'] = "Not a valid URL."
            except TooManyRedirects:
                errors['url'] = "URL caused a redirect loop."

        uploaded_file = bundle.data.get('file')
        if bundle.data.get('file_required', '') and not uploaded_file:
            errors['file'] = "File cannot be blank."
        if uploaded_file:
            mime_type = get_mime_type(uploaded_file.name)

            # Get mime type string from tuple
            if not mime_type or not mime_type_lookup[mime_type]['valid_file'](uploaded_file):
                errors['file'] = "Invalid file."
            elif uploaded_file.size > settings.MAX_ARCHIVE_FILE_SIZE:
                errors['file'] = "File is too large."

        # Moving folder when not organization
        #elif bundle.data.get("folder", None):
            #if bundle.obj.organization_id and bundle.obj.organization_id != bundle.data['folder'].organization_id:
                #errors['folder'] = "Archives belonging to an organization cannot be moved out of the organization's shared folder."

        return errors


class FolderValidation(DefaultValidation):
    def is_valid(self, bundle, request=None):
        errors = super(FolderValidation, self).is_valid(bundle, request)

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

        # Check for duplicate names
        if bundle.obj.parent_id:
            if Folder.objects.filter(parent_id=bundle.obj.parent_id, name=bundle.obj.name).exclude(pk=bundle.obj.pk).exists():
                errors['name'] = "A folder with that name already exists at that location."

        return errors
