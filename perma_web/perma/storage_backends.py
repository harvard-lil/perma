# alternate storage backends
import cStringIO as StringIO
import os

from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from django.core.files.storage import FileSystemStorage as DjangoFileSystemStorage
from django.core.files import File
from django.conf import settings
import django.dispatch

from pipeline.storage import PipelineMixin
from storages.backends.s3boto import S3BotoStorage
from whitenoise.django import GzipStaticFilesMixin

from perma.utils import ReadOnlyException

file_saved = django.dispatch.Signal(providing_args=["instance", "path", "overwrite"])


### Static files config

class StaticStorage(GzipStaticFilesMixin, PipelineMixin, ManifestStaticFilesStorage):
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
        if settings.READ_ONLY_MODE:
            raise ReadOnlyException("Read only mode enabled.")

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


class S3MediaStorage(BaseMediaStorage, S3BotoStorage):
    location = settings.MEDIA_ROOT
    
    
class S3BackedUpFileSystemMediaStorage(FileSystemMediaStorage):
    """
        Storage backend that reads and writes from the local filesystem, but also puts a copy up on S3 for every save.
        Before using, be sure to set BACKUP_MEDIA_ROOT, AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY.
    """
    def __init__(self, *args, **kwargs):
        # on init, create a second storage for writing to S3
        class BackupS3MediaStorage(S3MediaStorage):
            location = settings.BACKUP_MEDIA_ROOT
        self.backup_s3_storage = BackupS3MediaStorage(*args, **kwargs)

        # otherwise act normally
        super(S3BackedUpFileSystemMediaStorage, self).__init__()
        
    def save(self, *args, **kwargs):
        # on save, write a copy to S3
        self.backup_s3_storage.save(*args, **kwargs)

        # otherwise act normally
        return super(S3BackedUpFileSystemMediaStorage, self).save(*args, **kwargs)