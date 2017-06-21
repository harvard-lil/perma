import os

def get_cloudflare_ips(CLOUDFLARE_DIR):
    """
        Load IPs into list from services/cloudflare.
    """
    ips = []
    for ip_filename in ('ips-v4', 'ips-v6'):
        with open(os.path.join(CLOUDFLARE_DIR, ip_filename)) as ip_file:
            ips += ip_file.read().strip().split()
    return ips
