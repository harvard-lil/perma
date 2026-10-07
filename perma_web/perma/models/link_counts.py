"""
Maintains the link counts of users, organizations, and registrars: 
LinkUser.link_count, Organization.link_count, Registrar.link_count and Registrar.sponsored_link_count.
"""
from django.db.models import F


def link_created(link):
    """ Count a newly created link. """
    adjust_user_link_count(link.created_by_id, 1)
    adjust_owner_link_counts(1, new_org_id=link.organization_id)


def link_deleted(link):
    """ Stop counting a link that has just been marked user_deleted. """
    adjust_user_link_count(link.created_by_id, -1)
    adjust_owner_link_counts(1, old_org_id=link.organization_id, old_sponsored_by_id=link._sponsored_by_id())


def adjust_owner_link_counts(num_links, old_org_id=None, new_org_id=None, old_sponsored_by_id=None, new_sponsored_by_id=None):
    """
    Adjust the link counts of the links' owners: their organization, that organization's registrar,
    and their sponsoring registrar. num_links are subtracted from the old owners and added to the new ones. 
    To count new links, pass new_* ids, and to subtract deleted links, pass old_* ids.
    """
    if not num_links:
        return

    from .organization import Organization
    from .registrar import Registrar

    if old_org_id != new_org_id:
        _transfer(Organization.objects, 'link_count', old_org_id, new_org_id, num_links)
        registrar_ids_by_org = dict(Organization.objects.filter(pk__in=(old_org_id, new_org_id)).values_list('pk', 'registrar_id'))
        _transfer(Registrar.objects, 'link_count', registrar_ids_by_org.get(old_org_id), registrar_ids_by_org.get(new_org_id), num_links)

    _transfer(Registrar.objects, 'sponsored_link_count', old_sponsored_by_id, new_sponsored_by_id, num_links)


def org_registrar_changed(org_id, old_registrar_id, new_registrar_id):
    """ Transfer an organization's link_count to its new registrar. """
    if old_registrar_id == new_registrar_id:
        return

    from .organization import Organization
    from .registrar import Registrar

    num_links = Organization.objects.filter(pk=org_id).values_list('link_count', flat=True).first()
    _transfer(Registrar.objects, 'link_count', old_registrar_id, new_registrar_id, num_links)


def adjust_user_link_count(user_id, diff):
    """ Add the count difference to a user's link_count. """
    from .user import LinkUser

    users = LinkUser.objects.filter(pk=user_id)
    if diff < 0:
        users = users.filter(link_count__gte=-diff)
    users.update(link_count=F('link_count') + diff)


def _transfer(queryset, field, old_id, new_id, num_links):
    """ Update the link count of the organization or registrar. """
    if not num_links or old_id == new_id:
        return

    if old_id:
        queryset.filter(pk=old_id, **{f'{field}__gte': num_links}).update(**{field: F(field) - num_links})
    if new_id:
        queryset.filter(pk=new_id).update(**{field: F(field) + num_links})
