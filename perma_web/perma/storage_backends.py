# alternate storage backends
import cStringIO as StringIO
import os

from django.core.files.storage import FileSystemStorage as DjangoFileSystemStorage
from django.core.files import File
from django.conf import settings
import django.dispatch
from django.utils.module_loading import import_string

from storages.backends.s3boto3 import S3Boto3Storage
from storages.backends.sftpstorage import SFTPStorage
from whitenoise.storage import CompressedManifestStaticFilesStorage

# used only for suppressing INFO logging in S3Boto3Storage
import logging


file_saved = django.dispatch.Signal(providing_args=["instance", "path", "overwrite"])


### Static files config

class StaticStorage(CompressedManifestStaticFilesStorage):
    pass


### Media files config

class BaseMediaStorage(object):
    """
        This mixin provides some helper functions for working with files
        in both local disk and remote storage.
    """
    def store_file(self, file_object, file_path, overwrite=False, send_signal=True):
        """
            Given an open file_object ready for reading,
            and the file_path to store it to,
            save the file and return the new file name.

            File name will only change if file_path conflicts with an existing file.
            If overwrite=True, existing file will instead be deleted and overwritten.
        """

        if overwrite:
            if self.exists(file_path):
                self.delete(file_path)
        new_file_path = self.save(file_path, File(file_object))
        if send_signal:
            file_saved.send(sender=self.__class__, instance=self, path=new_file_path, overwrite=overwrite)
        return new_file_path.split('/')[-1]

    def store_data_to_file(self, data, file_path, overwrite=False, send_signal=True):
        file_object = StringIO.StringIO()
        file_object.write(data)
        file_object.seek(0)
        return self.store_file(file_object, file_path, overwrite=overwrite, send_signal=send_signal)

    def walk(self, top='/', topdown=False, onerror=None):
        """
            An implementation of os.walk() which uses the Django storage for
            listing directories.

            via https://gist.github.com/btimby/2175107
        """
        try:
            dirs, nondirs = self.listdir(top)
        except os.error as err:
            if onerror is not None:
                onerror(err)
            return

        if topdown:
            yield top, dirs, nondirs
        for name in dirs:
            new_path = os.path.join(top, name)
            for x in self.walk(new_path):
                yield x
        if not topdown:
            yield top, dirs, nondirs


class FileSystemMediaStorage(BaseMediaStorage, DjangoFileSystemStorage):
    pass


class S3MediaStorage(BaseMediaStorage, S3Boto3Storage):
    location = settings.MEDIA_ROOT
    # suppress boto3's INFO logging per https://github.com/boto/boto3/issues/521
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)


class SFTPMediaStorage(BaseMediaStorage, SFTPStorage):
    pass


if settings.DEFAULT_FILE_STORAGE.endswith('RedundantMediaStorage'):
    PrimaryStorageClass = import_string(settings.PRIMARY_FILE_STORAGE)
    SecondaryStorageClass = import_string(settings.SECONDARY_FILE_STORAGE)
    class RedundantMediaStorage(PrimaryStorageClass):
        """
            Storage backend that reads and writes to a primary storage class, but also performs redundant writes
            to a secondary storage class.

            Required settings:
                - PRIMARY_FILE_STORAGE
                - SECONDARY_FILE_STORAGE

            Optional settings:
                - SECONDARY_MEDIA_ROOT (defaults to MEDIA_ROOT)
        """
        def __init__(self, *args, **kwargs):
            # on init, create a secondary storage
            kwargs['location'] = getattr(settings, 'SECONDARY_MEDIA_ROOT', settings.MEDIA_ROOT)
            # SFTP storage won't accept the location argument, so:
            try:
                self.secondary_storage = SecondaryStorageClass(*args, **kwargs)
            except TypeError:
                del kwargs['location']
                self.secondary_storage = SecondaryStorageClass(*args, **kwargs)

            # otherwise act normally
            super(RedundantMediaStorage, self).__init__()

        def save(self, file_path, *args, **kwargs):
            # on save, write a copy to secondary storage
            if self.secondary_storage.exists(file_path):
                self.secondary_storage.delete(file_path)
            self.secondary_storage.save(file_path, *args, **kwargs)

            # otherwise act normally
            return super(RedundantMediaStorage, self).save(file_path, *args, **kwargs)
