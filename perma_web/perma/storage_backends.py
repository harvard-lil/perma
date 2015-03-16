# alternate storage backends
import cStringIO as StringIO
import os

from django.contrib.staticfiles.storage import CachedFilesMixin
from django.core.files.storage import FileSystemStorage as DjangoFileSystemStorage
from django.core.files import File
from django.conf import settings
import django.dispatch

from pipeline.storage import PipelineMixin
from storages.backends.s3boto import S3BotoStorage

from perma.utils import ReadOnlyException

file_saved = django.dispatch.Signal(providing_args=["instance", "path", "overwrite"])

class StorageHelpersMixin(object):
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


class FileSystemStorage(StorageHelpersMixin, DjangoFileSystemStorage):
    pass


class StaticRootS3BotoStorage(PipelineMixin, CachedFilesMixin, S3BotoStorage):
    location = settings.STATIC_ROOT


class MediaRootS3BotoStorage(StorageHelpersMixin, StaticRootS3BotoStorage):
    location = settings.MEDIA_ROOT