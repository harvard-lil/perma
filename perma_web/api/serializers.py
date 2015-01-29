from django.test.client import MULTIPART_CONTENT
from tastypie.serializers import Serializer


class MultipartSerializer(Serializer):
    formats = Serializer.formats + ['multipart']
    content_types = dict(Serializer.content_types, multipart=MULTIPART_CONTENT)

    def to_multipart(self, data, options=None):
        # pass through
        return data
