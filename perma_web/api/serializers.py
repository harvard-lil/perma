from django.test.client import MULTIPART_CONTENT
from tastypie.serializers import Serializer

class MultipartSerializer(Serializer):
    formats = Serializer.formats
    formats.append('multipart')

    content_types = Serializer.content_types
    content_types['multipart'] = MULTIPART_CONTENT

    def to_multipart(self, data, options=None):
        return data
