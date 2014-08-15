import os
import subprocess
from urllib import quote as urlquote
import urlparse
from django.conf import settings
import sys
import tempdir

try:
    from twisted.web.server import NOT_DONE_YET
    from twisted.internet import reactor
    from twisted.web import proxy, server, vhost
except ImportError:
    sys.exit("ERROR: You must install Twisted before running the mirror server with the command: pip install twisted")

from django.core.management.base import BaseCommand


class ForwardedReverseProxyResource(proxy.ReverseProxyResource):
    """
        Here we override the default Twisted reverse proxy
        to forward all request headers to the proxied resource,
        so Django gets the headers it needs to figure out its response.
    """
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
    """
        In this command, we're going to set up a whole virtual mirror network running locally.
        The upshot of the following steps is that you can access the mirror network at http://perma.dev:8000/

        NOTES:
            - If you make changes that affect this file or the celery servers, you'll have to manually restart the server.
            - Because we have multiple subprocesses, pdb can't read input. Instead use:
                  from celery.contrib import rdb; rdb.set_trace()
              and then telnet into the rdb console as instructed.
            - The mirror database will be a newly cloned copy of the main database each time.
            - The mirror server will *not* have a copy of the existing generated files; it stores files in a temp folder.

        First we'll launch two Django servers:

            Main server: http://users.perma.dev:8001/
            Mirror server: http://perma.dev:8002/

        Then we'll launch a celery worker for each server, using the queues 'runmirror_main_queue' and 'runmirror_mirror_queue'.

        Finally we'll launch a Twisted frontend server listening at port :8000. This simulates a DNS round-robin like Dyn,
        proxying http://users.perma.dev:8000/ to be handled by the main server, and http://perma.dev:8000/
        to be handled by the mirror server.
    """
    args = ''
    help = 'Runs main server and mirror server.'

    def handle(self, *args, **options):

        # setup
        running_processes = []
        main_server_port = 8001
        mirror_server_port = 8002
        main_server_address = 'http://users.perma.dev:%s' % main_server_port
        mirror_server_address = 'http://perma.dev:%s' % mirror_server_port
        temp_dir = tempdir.TempDir()

        try:
            print "Creating mirror database ..."
            main_database = settings.DATABASES['default']['NAME']
            mirror_database = main_database+"_mirror"
            mysql_credentials = [
                "-u"+settings.DATABASES['default']['USER'],
                "-p" + settings.DATABASES['default']['PASSWORD'],
            ]
            empty_tables = ['perma_linkuser','perma_link','perma_asset']
            mysqldump_command = "mysqldump %(user)s %(password)s %%(options)s %(main_database)s %%(tables)s | mysql %(user)s %(password)s %(mirror_database)s" % {
                'user':mysql_credentials[0], 'password':mysql_credentials[1], 'main_database':main_database, 'mirror_database':mirror_database,
            }
            subprocess.call(["mysql"]+mysql_credentials+[main_database, "-e", "DROP DATABASE IF EXISTS %s;" % mirror_database])
            subprocess.call(["mysql"]+mysql_credentials+[main_database, "-e", "CREATE DATABASE %s CHARACTER SET utf8;" % mirror_database])
            subprocess.call(mysqldump_command % {
                'options':" ".join(["--ignore-table=%s.%s" % (main_database, table) for table in empty_tables]),
                'tables':''
            }, shell=True)
            subprocess.call(mysqldump_command % {
                'options': '-d',
                'tables': " ".join(empty_tables),
            }, shell=True)

            print "Launching main server ..."
            main_server_env = dict(
                DJANGO__MIRRORS__0__address=mirror_server_address,
                DJANGO__MIRRORING_ENABLED='True',
                DJANGO__CELERY_DEFAULT_QUEUE='runmirror_main_queue',
            )
            running_processes.append(subprocess.Popen(['python', 'manage.py', 'runserver', str(main_server_port)],
                                             env=dict(os.environ, **main_server_env)))
            running_processes.append(subprocess.Popen(
                ['celery', '-A', 'perma', 'worker', '--loglevel=info', '-Q', 'runmirror_main_queue', '--hostname=runmirror_main_queue'],
                env=dict(os.environ, **main_server_env)))

            print "Launching mirror server ..."
            mirror_server_env = dict(
                DJANGO__CELERY_DEFAULT_QUEUE='runmirror_mirror_queue',
                DJANGO__MIRRORING_ENABLED='True',
                DJANGO__DATABASES__default__NAME=mirror_database,
                DJANGO__MIRROR_SERVER='True',
                DJANGO__UPSTREAM_SERVER__address=main_server_address,
                #DJANGO__RUN_TASKS_ASYNC='False',
                DJANGO__MEDIA_ROOT=temp_dir.name,
                DJANGO__CDX_SERVER_URL=mirror_server_address+'/cdx',
            )
            running_processes.append(subprocess.Popen(['python', 'manage.py', 'runserver', str(mirror_server_port)],
                                             env=dict(os.environ, **mirror_server_env)))
            running_processes.append(subprocess.Popen(
                ['celery', '-A', 'perma', 'worker', '--loglevel=info', '-Q', 'runmirror_mirror_queue', '--hostname=runmirror_mirror_queue'],
                env=dict(os.environ, **mirror_server_env)))

            print "Syncing contents ..."
            running_processes.append(subprocess.Popen(['python', 'manage.py', 'shell'],
                            env=dict(os.environ, **mirror_server_env)))

            print "Launching reverse proxy ..."
            root = vhost.NameVirtualHost()
            root.addHost('users.perma.dev', ForwardedReverseProxyResource('127.0.0.1', main_server_port, ''))
            root.addHost('perma.dev', ForwardedReverseProxyResource('127.0.0.1', mirror_server_port, ''))
            site = server.Site(root)
            reactor.listenTCP(8000, site)
            reactor.run()

        finally:
            # make sure all our subprocesses are killed on exit
            for process in running_processes:
                process.terminate()

            # remove temp files
            temp_dir.dissolve()
