import logging
from django import template

logger = logging.getLogger(__name__)
register = template.Library()


from perma.models import Registrar

@register.simple_tag(takes_context=True)
def set_carousel_partners(context):
    """
        Here we check out the width and height dimensions for all our partner logos, and group them into lines
        to show in the carousel.

        We keep one line going for long-thin logos and another line going for squarish logos, and whenever
        a line gets long enough we add it to the list of logo_groups and start a new one.
    """

    partners = context.get('partners') or Registrar.objects.filter(show_partner_status=True).exclude(logo=None)
    wide_logo_line = []
    wide_logo_line_width = 0
    narrow_logo_line = []
    narrow_logo_line_width = 0
    logo_groups = [wide_logo_line, narrow_logo_line]

    for partner in partners:
        if not partner.logo:
            continue
        try:
            proportion = float(partner.logo.width) / partner.logo.height
        except:
            # Can't read width/height for this image for some reason -- probably messed up file. Just skip it.
            continue

        # logo is wider than it is tall
        if proportion > 1.5:
            # with long-thin logos, we start a new line when the current one is 50 times as wide as tall
            if wide_logo_line_width + proportion > 50:
                wide_logo_line = []
                logo_groups.append(wide_logo_line)
                wide_logo_line_width = 0
            wide_logo_line.append(partner)
            wide_logo_line_width += proportion
            partner.logo_class = ""
            partner.thumbnail_geometry = "x50"

        # logo is taller than it is wide
        else:
            # with squarish logos, we start a new line when the current one is eight times as wide as tall
            if narrow_logo_line_width + proportion > 8:
                narrow_logo_line = []
                logo_groups.append(narrow_logo_line)
                narrow_logo_line_width = 0
            narrow_logo_line.append(partner)
            narrow_logo_line_width += proportion
            partner.logo_class = "square"
            partner.thumbnail_geometry = "x130"

    context['carousel_logo_groups'] = logo_groups

    return ""