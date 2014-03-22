import os
import subprocess
from urllib import quote as urlquote
import urlparse

from twisted.web.server import NOT_DONE_YET
from twisted.internet import reactor
from twisted.web import proxy, server, vhost

from django.core.management.base import BaseCommand


class ForwardedReverseProxyResource(proxy.ReverseProxyResource):
    def getChild(self, path, request):
        return self.__class__(self.host, self.port, self.path + '/' + urlquote(path, safe=""), self.reactor)

    def render(self, request):
        request.content.seek(0, 0)
        qs = urlparse.urlparse(request.uri)[4]
        if qs:
            rest = self.path + '?' + qs
        else:
            rest = self.path
        clientFactory = self.proxyClientFactoryClass(
            request.method, rest, request.clientproto,
            request.getAllHeaders(), request.content.read(), request)
        self.reactor.connectTCP(self.host, self.port, clientFactory)
        return NOT_DONE_YET

class Command(BaseCommand):
    args = ''
    help = 'Runs main server and mirror server.'

    def handle(self, *args, **options):
        main_server = None
        mirror_server = None
        try:
            print "Launching main server ..."
            mirror_server = subprocess.Popen(['python', 'manage.py', 'runserver', '8001'],
                                             env=dict(os.environ,
                                                      PERMA_MIRRORING_ENABLED='True',))

            print "Launching mirror server ..."
            mirror_server = subprocess.Popen(['python', 'manage.py', 'runserver', '8002'],
                                             env=dict(os.environ,
                                                      PERMA_MIRRORING_ENABLED='True',
                                                      DJANGO_SETTINGS_MODULE='perma.settings.settings_mirror_dev',))

            print "Launching reverse proxy ..."
            root = vhost.NameVirtualHost()
            root.addHost('users.perma.dev', ForwardedReverseProxyResource('127.0.0.1', 8001, ''))
            root.addHost('perma.dev', ForwardedReverseProxyResource('127.0.0.1', 8002, ''))
            site = server.Site(root)
            reactor.listenTCP(8000, site)
            reactor.run()

        finally:
            if main_server:
                main_server.terminate()
            if mirror_server:
                mirror_server.terminate()
