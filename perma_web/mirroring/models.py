from django.core import serializers
from perma.models import LinkUser


class FakeLinkUser(LinkUser):
    """
        This is a fake user for use on mirror servers.
        It will be created from a serialized user object put in a cookie by the upstream server.
    """

    @classmethod
    def init_from_serialized_user(cls, serialized_user):
        serialized_user = serialized_user.replace('perma.linkuser', 'mirroring.fakelinkuser')
        return serializers.deserialize("json", serialized_user).next().object

    class Meta:
        proxy = True

    def is_authenticated(self):
        return True

    def save(self, *args, **kwargs):
        raise NotImplementedError("FakeLinkUser should never be saved.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("FakeLinkUser should never be deleted.")