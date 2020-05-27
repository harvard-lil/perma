from django import template

register = template.Library()


@register.filter
def short_page_range(page, padding=2):
    """
        Return just the page numbers we want to display from a Django Page object returned by a Paginator.
        E.g., assuming we are on page 10 of 20:
            {% for num in page|short_page_range %}num, {% endfor %}
        Will output:
            1, 2, ..., 8, 9, 10, 11, 12, ..., 19, 20
    """
    paginator = page.paginator
    show_ellipsis = True
    for i in paginator.page_range:
        if i <= 2 or abs(i - page.number) <= padding or i >= paginator.num_pages - 1:
            yield i
            show_ellipsis = True
        elif show_ellipsis:
            show_ellipsis = False
            yield '...'
