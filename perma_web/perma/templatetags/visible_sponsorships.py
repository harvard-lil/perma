from django import template

register = template.Library()

@register.filter
def visible_sponsorships(user, viewing_user):
    """
        Return just the registrars that viewing_user is allowed to know about.
    """
    if viewing_user.is_staff:
        return user.sponsorships.all()
    elif viewing_user.is_registrar_user():
        return user.sponsorships.filter(registrar_id=viewing_user.registrar_id)
    return []
