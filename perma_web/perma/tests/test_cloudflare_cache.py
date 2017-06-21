import requests
import os

from django.conf import settings

from .utils import PermaTestCase


class CloudflareCacheTestCase(PermaTestCase):
    """
        Ensure that our local cache of Cloudflare IP addresses is up to date.
    """
    message = """
Cloudflare has updated its list of IP addresses since we last grabbed a
copy. We rely on an up-to-date list of IP addresses for rate limiting,
LOCKSS security, and other purposes. Please run `fab dev.update_cloudflare_cache`
and commit the updated files.
"""

    def test_cloudflare_ip4_cache(self):
        ip4 = requests.get('https://www.cloudflare.com/ips-v4').text

        with open(os.path.join(settings.CLOUDFLARE_DIR, 'ips-v4')) as ip4_cache:
            self.assertEqual(ip4, ip4_cache.read(), msg=self.message)

    def test_cloudflare_ip6_cache(self):
        ip6 = requests.get('https://www.cloudflare.com/ips-v6').text

        with open(os.path.join(settings.CLOUDFLARE_DIR, 'ips-v6')) as ip6_cache:
            self.assertEqual(ip6, ip6_cache.read(), msg=self.message)
