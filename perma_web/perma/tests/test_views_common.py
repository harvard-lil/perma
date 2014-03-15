from perma.urls import urlpatterns

from .utils import PermaTestCase

class CommonViewsTestCase(PermaTestCase):

    def test_public_views(self):
        # test static template views
        for urlpattern in urlpatterns:
            if urlpattern.callback.func_name == 'DirectTemplateView':
                resp = self.get(urlpattern.name)
