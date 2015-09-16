from django.test.client import MULTIPART_CONTENT
from tastypie.serializers import Serializer


class DefaultSerializer(Serializer):
    def format_datetime(self, data):
        """
            Correctly format iso 8601 dates with UTC timezone appended (Z).
            Via http://stackoverflow.com/a/15582620/307769
        """
        return data.strftime("%Y-%m-%dT%H:%M:%SZ")


class MultipartSerializer(DefaultSerializer):
    formats = Serializer.formats + ['multipart']
    content_types = dict(Serializer.content_types, multipart=MULTIPART_CONTENT)

    def to_multipart(self, data, options=None):
        # pass through
        return data
