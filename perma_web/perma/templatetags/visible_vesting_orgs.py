from django import template

register = template.Library()

@register.filter
def visible_vesting_orgs(vesting_user, viewing_user):
    """
        Return just the vesting orgs that viewing_user is allowed to know about.
    """
    if viewing_user.is_staff:
        return vesting_user.vesting_org.all()
    elif viewing_user.is_registrar_member():
        return vesting_user.vesting_org.filter(registrar_id=viewing_user.registrar_id)
    elif viewing_user.is_vesting_org_member:
        return vesting_user.vesting_org.filter(id__in=[v.pk for v in viewing_user.vesting_org.all()])
    return []