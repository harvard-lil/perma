# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-01-07 16:52
from __future__ import unicode_literals

from django.db import migrations
from django.conf import settings


def premium_registrars_are_not_in_trial(apps, schema_editor):
    """
    Most Registrars are nonpaying; the rest are expected to
    have paid subscriptions and are accordingly not in their
    "trial" period.
    """
    Registrar = apps.get_model('perma', 'Registrar')
    paying_registrars = Registrar.objects.filter(nonpaying=False)
    paying_registrars.update(in_trial=False)


def revert_premium_registrars_to_default(apps, schema_editor):
    Registrar = apps.get_model('perma', 'Registrar')
    paying_registrars = Registrar.objects.filter(nonpaying=False)
    paying_registrars.update(in_trial=True)


def current_premium_users_are_not_in_trial(apps, schema_editor):
    """
    At this moment, all "unlimited" users have paid subscriptions,
    and no one else does. Use that as a proxy: every one else is
    in their "trial" period.
    """
    LinkUser = apps.get_model('perma', 'LinkUser')
    premium_users = LinkUser.objects.filter(unlimited=True)
    premium_users.update(in_trial=False)


def revert_premium_users_to_default(apps, schema_editor):
    LinkUser = apps.get_model('perma', 'LinkUser')
    premium_users = LinkUser.objects.filter(unlimited=True)
    premium_users.update(in_trial=True)


def grant_trial_users_ten_links(apps, schema_editor):
    """
    All trial LinkUsers should be allowed to create exactly 10 more Personal Links.
    """
    LinkUser = apps.get_model('perma', 'LinkUser')
    Link = apps.get_model('perma', 'Link')
    active_trial_users = LinkUser.objects.filter(is_confirmed=True, is_active=True, link_limit_period='once', in_trial=True)
    for user in active_trial_users.iterator():
        # N.B. model managers are not available in migrations unless explicitly enabled
        # https://docs.djangoproject.com/en/2.1/topics/migrations/#model-managers
        # I don't want to break anything, so not enabling the Link manager:
        # instead, manually excluding 'deleted' links from this count
        links_created = Link.objects.filter(created_by_id=user.id, organization_id=None, user_deleted=False).count()
        if links_created:
            user.link_limit = links_created + 10
            user.save(update_fields=['link_limit'])


def reset_trial_users_link_limits(apps, schema_editor):
    LinkUser = apps.get_model('perma', 'LinkUser')
    active_trial_users = LinkUser.objects.filter(is_confirmed=True, is_active=True, link_limit_period='once', in_trial=True)
    active_trial_users.update(link_limit=settings.DEFAULT_CREATE_LIMIT)


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0041_auto_20190109_1704'),
    ]

    operations = [
        migrations.RunPython(premium_registrars_are_not_in_trial, revert_premium_registrars_to_default),
        migrations.RunPython(current_premium_users_are_not_in_trial, revert_premium_users_to_default),
        migrations.RunPython(grant_trial_users_ten_links, reset_trial_users_link_limits),
    ]