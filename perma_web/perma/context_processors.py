from django.conf import settings


def template_visible_settings(request):
    """Return only settings explicitly approved for Django templates."""
    return {
        setting_name: getattr(settings, setting_name)
        for setting_name in settings.TEMPLATE_VISIBLE_SETTINGS
    }
