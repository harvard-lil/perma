import requests
import os

from django.conf import settings

from .utils import PermaTestCase


SETTINGS_DIR = os.path.join(settings.PROJECT_ROOT, "perma/settings")

class CloudflareCacheTestCase(PermaTestCase):
    """
        Ensure that our local cache of Cloudflare IP addresses is up to date.
    """
    message = """
Cloudflare has updated its list of IP addresses since we last grabbed a
copy. We rely on an up-to-date list of IP addresses for rate limiting,
LOCKSS security, and other purposes. Please get updated lists AND please
update settings_prod.py accordingly. (Settings are NOT automatically
populated from the cached files.)
"""

    def test_cloudflare_ip4_cache(self):
        ip4 = requests.get('https://www.cloudflare.com/ips-v4').text

        with open(os.path.join(SETTINGS_DIR, 'cloudflare_ips-v4.txt')) as ip4_cache:
            self.assertEqual(ip4, ip4_cache.read(), msg=self.message)

    def test_cloudflare_ip6_cache(self):
        ip6 = requests.get('https://www.cloudflare.com/ips-v6').text

        with open(os.path.join(SETTINGS_DIR, 'cloudflare_ips-v6.txt')) as ip6_cache:
            self.assertEqual(ip6, ip6_cache.read(), msg=self.message)
