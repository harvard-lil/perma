from django.urls import reverse

from perma.urls import urlpatterns

def test_public_views(client):
    # test static template views
    for urlpattern in urlpatterns:
        if urlpattern.callback.__name__ == 'DirectTemplateView':
            response = client.get(
                reverse(urlpattern.name),
                secure=True
            )
            assert response.status_code == 200
