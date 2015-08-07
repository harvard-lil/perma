# Tests for the django admin:

import django_admin_smoke_tests.tests
from perma.models import LinkUserManager, LinkUser
from .utils import PermaTestCase

class AdminTestCase(django_admin_smoke_tests.tests.AdminSiteSmokeTest, PermaTestCase):
    def setUp(self):
        # monkey-patch create_superuser, which is relied on by the django_admin_smoke_tests package
        LinkUserManager.create_superuser = lambda *args, **kwargs: LinkUser.objects.get(pk=1)
        return super(AdminTestCase, self).setUp()