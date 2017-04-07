from datetime import datetime
from django.utils import timezone

from perma.models import *

from .utils import PermaTestCase


class ModelsTestCase(PermaTestCase):

    def test_link_count_in_time_period_no_links(self):
        '''
            If no links in period, should return 0
        '''
        no_links = Link.objects.none()
        self.assertEqual(link_count_in_time_period(no_links), 0)

    def test_link_count_period_invalid_dates(self):
        '''
            If end date is before start date, should raise an exception
        '''
        no_links = Link.objects.none()
        now = timezone.make_aware(datetime(timezone.now().year, 1, 1))
        later = timezone.make_aware(datetime(timezone.now().year + 1, 1, 1))
        with self.assertRaises(ValueError):
            link_count_in_time_period(no_links, later, now)

    def test_link_count_period_equal_dates(self):
        '''
            If end date = start date, links are only counted once
        '''
        now = timezone.make_aware(datetime(timezone.now().year, 1, 1))
        user = LinkUser()
        user.save()
        link = Link(creation_timestamp=now, guid="AAAA-AAAA", created_by=user)
        link.save()

        links = Link.objects.filter(pk=link.pk)
        self.assertEqual(len(links), 1)
        self.assertEqual(link_count_in_time_period(links, now, now), len(links))

    def test_link_count_valid_period(self):
        '''
            Should include links created only in the target year
        '''
        now = timezone.make_aware(datetime(timezone.now().year, 1, 1))
        two_years_ago = timezone.make_aware(datetime(now.year - 2, 1, 1))
        three_years_ago = timezone.make_aware(datetime(now.year - 3, 1, 1))
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD", "EEEE-EEEE"]
        older= Link(creation_timestamp=three_years_ago, guid=link_pks[0], created_by=user)
        older.save()
        old = Link(creation_timestamp=two_years_ago, guid=link_pks[1], created_by=user)
        old.save()
        now1 = Link(creation_timestamp=now, guid=link_pks[2], created_by=user)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[3], created_by=user)
        now2.save()
        now3 = Link(creation_timestamp=now, guid=link_pks[4], created_by=user)
        now3.save()

        links = Link.objects.filter(pk__in=link_pks)
        self.assertEqual(len(links), 5)
        self.assertEqual(link_count_in_time_period(links, three_years_ago, two_years_ago), 2)

    def test_org_link_count_this_year(self):
        '''
            Should include links created this year and exclude links
            older than that.
        '''
        r = Registrar()
        r.save()
        o = Organization(registrar=r)
        o.save()
        self.assertEqual(o.link_count_this_year(), 0)

        now = timezone.make_aware(datetime(timezone.now().year, 1, 1))
        two_years_ago = timezone.make_aware(datetime(now.year - 2, 1, 1))
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC"]
        too_early = Link(creation_timestamp=two_years_ago, guid=link_pks[0], created_by=user, organization=o)
        too_early.save()
        now1 = Link(creation_timestamp=now, guid=link_pks[1], created_by=user, organization=o)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[2], created_by=user, organization=o)
        now2.save()

        links = Link.objects.filter(pk__in=link_pks)
        self.assertEqual(len(links), 3)
        self.assertEqual(o.link_count_this_year(), 2)

    def test_registrar_link_count_this_year(self):
        '''
            Should include links created this year and exclude links
            older than that. Should work across all its orgs.
        '''
        r = Registrar()
        r.save()
        o1 = Organization(registrar=r)
        o1.save()
        o2 = Organization(registrar=r)
        o2.save()

        now = timezone.make_aware(datetime(timezone.now().year, 1, 1))
        two_years_ago = timezone.make_aware(datetime(now.year - 2, 1, 1))
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD"]
        too_early = Link(creation_timestamp=two_years_ago, guid=link_pks[0], created_by=user, organization=o1)
        too_early.save()
        now1 = Link(creation_timestamp=now, guid=link_pks[1], created_by=user, organization=o1)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[2], created_by=user, organization=o1)
        now2.save()
        now3 = Link(creation_timestamp=now, guid=link_pks[3], created_by=user, organization=o2)
        now3.save()

        links = Link.objects.filter(pk__in=link_pks)
        self.assertEqual(len(links), 4)
        self.assertEqual(r.link_count_this_year(), 3)

    def test_most_active_org_in_time_period_no_links(self):
        '''
            If no orgs with links in period, should return None
        '''
        r = Registrar()
        r.save()
        o1 = Organization(registrar=r)
        o1.save()
        o2 = Organization(registrar=r)
        o2.save()
        self.assertEqual(type(most_active_org_in_time_period(r.organizations)), type(None))

    def test_most_active_org_in_time_period_invalid_dates(self):
        '''
            If end date is before start date, should raise an exception
        '''
        r = Registrar()
        r.save()
        now = timezone.make_aware(datetime(timezone.now().year, 1, 1))
        later = timezone.make_aware(datetime(now.year + 1, 1, 1))
        with self.assertRaises(ValueError):
            most_active_org_in_time_period(r.organizations, later, now)

    def test_most_active_org_in_time_period_valid_period(self):
        '''
            Should include links created only in the target year
        '''
        now = timezone.make_aware(datetime(timezone.now().year, 1, 1))
        two_years_ago = timezone.make_aware(datetime(now.year - 2, 1, 1))
        three_years_ago = timezone.make_aware(datetime(now.year - 3, 1, 1))

        r = Registrar()
        r.save()
        o1 = Organization(registrar=r)
        o1.save()
        o2 = Organization(registrar=r)
        o2.save()
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD", "EEEE-EEEE"]

        too_early1 = Link(creation_timestamp=three_years_ago, guid=link_pks[0], organization=o1, created_by=user)
        too_early1.save()
        too_early2 = Link(creation_timestamp=three_years_ago, guid=link_pks[1], organization=o1, created_by=user)
        too_early2.save()

        now1 = Link(creation_timestamp=now, guid=link_pks[2], organization=o1, created_by=user)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[3], organization=o2, created_by=user)
        now2.save()
        now3 = Link(creation_timestamp=now, guid=link_pks[4], organization=o2, created_by=user)
        now3.save()

        # organization 1 was more active in the past
        self.assertEqual(most_active_org_in_time_period(r.organizations, three_years_ago, two_years_ago), o1)
        # but organization 2 was more active during the period in question
        self.assertEqual(most_active_org_in_time_period(r.organizations, two_years_ago), o2)
        # with a total of three links, organization 1 has been more active over all
        self.assertEqual(most_active_org_in_time_period(r.organizations), o1)

    def test_registrar_most_active_org_this_year(self):
        '''
            Should return the org (whole object)with the most links
            created this year, or None if it has no orgs with links
            created this year.
        '''
        r = Registrar()
        r.save()
        self.assertEqual(type(r.most_active_org_this_year()), type(None))

        o1 = Organization(registrar=r)
        o1.save()
        o2 = Organization(registrar=r)
        o2.save()

        now = timezone.make_aware(datetime(timezone.now().year, 1, 1))
        two_years_ago = timezone.make_aware(datetime(now.year - 2, 1, 1))
        user = LinkUser()
        user.save()
        link_pks = ["AAAA-AAAA", "BBBB-BBBB", "CCCC-CCCC", "DDDD-DDDD", "EEEE-EEEE", "FFFF-FFFF"]
        too_early = Link(creation_timestamp=two_years_ago, guid=link_pks[0], created_by=user, organization=o1)
        too_early.save()
        self.assertEqual(type(r.most_active_org_this_year()), type(None))

        now1 = Link(creation_timestamp=now, guid=link_pks[1], created_by=user, organization=o1)
        now1.save()
        now2 = Link(creation_timestamp=now, guid=link_pks[2], created_by=user, organization=o1)
        now2.save()
        now3 = Link(creation_timestamp=now, guid=link_pks[3], created_by=user, organization=o2)
        now3.save()

        self.assertEqual(r.most_active_org_this_year(), o1)

        now4 = Link(creation_timestamp=now, guid=link_pks[4], created_by=user, organization=o2)
        now4.save()
        now5 = Link(creation_timestamp=now, guid=link_pks[5], created_by=user, organization=o2)
        now5.save()

        self.assertEqual(r.most_active_org_this_year(), o2)

