# alternate storage backends

from storages.backends.s3boto import S3BotoStorage
from django.conf import settings


class StaticRootS3BotoStorage(S3BotoStorage):
    location = settings.STATIC_ROOT


class MediaRootS3BotoStorage(S3BotoStorage):
    location = settings.MEDIA_ROOT