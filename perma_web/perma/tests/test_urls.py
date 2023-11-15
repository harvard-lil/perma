from django.urls import reverse

from perma.urls import urlpatterns


def test_url_status_codes(client):
    """
    A really simple test for 500 errors. We test all views that don't
    take parameters (it's not easy to guess what params they want).
    """
    exclude = {
        'archive_error': 'because it returns 500 by default'
    }

    for urlpattern in urlpatterns:
        if '?P<' not in urlpattern.pattern._regex \
                 and urlpattern.name \
                 and urlpattern.name not in exclude:
            response = client.get(reverse(urlpattern.name))
            assert response.status_code != 500

            response = client.post(reverse(urlpattern.name))
            assert response.status_code != 500
