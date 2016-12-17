from perma.models import *

from .utils import PermaTestCase

class LinkCountCachingTestCase(PermaTestCase):

    fixtures = [
        'fixtures/users.json',
        'fixtures/folders.json',
    ]

    def setUp(self):
        super(LinkCountCachingTestCase, self).setUp()

        self.regular_user = LinkUser.objects.get(pk=4)
        self.org_user = LinkUser.objects.get(pk=3)
        self.registrar_user = LinkUser.objects.get(pk=2)

    ### TESTS ###

    def test_link_count_regular_user(self):
        """ We do some link count tallying on save """

        link_count = self.regular_user.link_count
        link = Link(created_by=self.regular_user, submitted_url="http://example.com")
        link.save()

        self.regular_user.refresh_from_db()
        self.assertEqual(link_count + 1, self.regular_user.link_count)

        link.safe_delete()
        link.save()

        self.regular_user.refresh_from_db()
        self.assertEqual(link_count, self.regular_user.link_count)


    def test_link_count_for_orgs(self):
        """ We do some link count tallying on save. Let's make sure
        we're adjusting the counts on the orgs """

        org_to_which_user_belongs = self.org_user.organizations.all().first()
        link_count = org_to_which_user_belongs.link_count
        link = Link(created_by=self.org_user, submitted_url="http://example.com", organization=org_to_which_user_belongs)
        link.save()

        org_to_which_user_belongs.refresh_from_db()
        self.assertEqual(link_count + 1, org_to_which_user_belongs.link_count)

        link.safe_delete()
        link.save()

        org_to_which_user_belongs.refresh_from_db()
        self.assertEqual(link_count, org_to_which_user_belongs.link_count)

    def test_link_count_for_registrars(self):
        """ We do some link count tallying on save. Let's make sure
        we're adjusting the counts on the registrars """

        registrar_to_which_user_belongs = self.registrar_user.registrar
        link_count = registrar_to_which_user_belongs.link_count
        org_managed_by_registrar = registrar_to_which_user_belongs.organizations.all().first()
        link = Link(created_by=self.registrar_user, submitted_url="http://example.com", organization=org_managed_by_registrar)
        link.save()

        registrar_to_which_user_belongs.refresh_from_db()
        self.assertEqual(link_count + 1, registrar_to_which_user_belongs.link_count)

        link.safe_delete()
        link.save()

        registrar_to_which_user_belongs.refresh_from_db()
        self.assertEqual(link_count, registrar_to_which_user_belongs.link_count)
