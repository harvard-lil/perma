# Tests for the django admin:

from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin
from perma.models import LinkUserManager, LinkUser
from .utils import PermaTestCase

class AdminTestCase(AdminSiteSmokeTestMixin, PermaTestCase):
    fixtures = PermaTestCase.fixtures

    def setUp(self):
        # monkey-patch create_superuser, which is relied on by the django_admin_smoke_tests package
        LinkUserManager.create_superuser = lambda *args, **kwargs: LinkUser.objects.get(pk=1)
        return super(AdminTestCase, self).setUp()
