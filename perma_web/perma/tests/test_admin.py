# Tests for the django admin:

# First monkey-patch LinkUser to have a create_superuser method, which is expected by django-admin-smoke-tests ...
from perma.models import LinkUser
superuser = LinkUser.objects.get(pk=1)
LinkUser.objects.create_superuser = lambda *args, **kwargs: superuser

# ... then run the django-admin-smoke-tests test suite:
from django_admin_smoke_tests.tests import AdminSiteSmokeTest

class AdminTestCase(AdminSiteSmokeTest):
    def setUp(self):
        return super(AdminTestCase, self).setUp()