from fabric.api import *

import os
import shutil
import tempfile

from django.conf import settings
from django.utils.crypto import get_random_string


@task
def configure_app(app_name, s3_storage_bucket=None, s3_path='/'):
    """
        Set up a new Heroku Perma app.
    """
    def heroku(cmd, capture=False):
        return local("heroku %s --app %s" % (cmd, app_name), capture=capture)

    #heroku("apps:create %s" % app_name)
    existing_addons = heroku("addons", capture=True)
    for addon in ('cloudamqp', 'rediscloud'):
        if addon not in existing_addons:
            heroku("addons:add %s" % addon)

    # Django config
    if not s3_storage_bucket:
        s3_storage_bucket = app_name
    s3_url = '//%s.s3.amazonaws.com%s' % (s3_storage_bucket, s3_path)

    django_config_vars = {
        'AWS_STORAGE_BUCKET_NAME':s3_storage_bucket,
        'HOST':'%s.herokuapp.com' % app_name,
        'MEDIA_ROOT':'/generated/',
        'MEDIA_URL':s3_url+'media/',
        'SECRET_KEY':get_random_string(50, 'abcdefghijklmnopqrstuvwxyz0123456789'),
        'STATIC_URL':s3_url+'static/',
    }
    heroku("config:set %s" % " ".join("DJANGO__%s=%s" % (key, val) for key, val in django_config_vars.items()))

    django_blank_vars = ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'GPG_PRIVATE_KEY', 'GPG_PUBLIC_KEY')
    heroku("config:set %s" % " ".join("DJANGO__%s=MISSING" % key for key in django_blank_vars))

    heroku("config:set BUILDPACK_URL=https://github.com/heroku/heroku-buildpack-multi.git")

    print "Heroku app setup completed. Remember to set the following config vars: %s" % (django_blank_vars,)

@task
def push(app_name='perma', project_dir=os.path.join(settings.PROJECT_ROOT, '..')):
    """
        Push code to Heroku.
    """
    # where we'll get files from to set up the heroku deployment
    heroku_files_dir = os.path.join(project_dir, "services", "heroku")

    # copy perma_web to a temp dir for deployment
    dest_dir = tempfile.mkdtemp()
    local("cp -r %s/* %s" % (os.path.join(project_dir, "perma_web"), dest_dir))

    with lcd(dest_dir):

        # set up heroku files
        local("cp %s ." % os.path.join(heroku_files_dir, "Procfile"))
        local("cp %s ." % os.path.join(heroku_files_dir, "amazon-rds-combined-ca-bundle.pem"))
        local("cp %s ." % os.path.join(heroku_files_dir, "runtime.txt"))
        local("cp %s .buildpacks" % os.path.join(heroku_files_dir, "buildpacks"))
        local("cp %s perma/" % os.path.join(heroku_files_dir, "wsgi_heroku.py"))
        local("cp %s perma/settings/settings.py" % os.path.join(heroku_files_dir, "heroku_settings.py"))
        local("cat %s >> requirements.txt" % os.path.join(heroku_files_dir, "extra_requirements.txt"))

        # set up git
        local(r'sed "s/perma_web\/perma\/settings\/settings.py|perma_web\///g" %s/%s > %s' % (project_dir, '.gitignore', '.gitignore'))
        local("git init")
        local("git add -A")
        local("git commit -m 'heroku push `date`'")
        local("heroku git:remote -a %s" % app_name)

        # push to heroku
        local("git push --force heroku master")

    # delete temp dir
    shutil.rmtree(dest_dir)