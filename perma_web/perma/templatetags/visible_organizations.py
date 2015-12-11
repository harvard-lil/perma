from django import template

register = template.Library()

@register.filter
def visible_organizations(user, viewing_user):
    """
        Return just the orgs that viewing_user is allowed to know about.
    """
    if viewing_user.is_staff:
        return user.organizations.all()
    elif viewing_user.is_registrar_member():
        return user.organizations.filter(registrar_id=viewing_user.registrar_id)
    elif viewing_user.is_organization_member:
        return user.organizations.filter(id__in=[v.pk for v in viewing_user.organizations.all()])
    return []