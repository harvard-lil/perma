from fabric.api import *

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

    print("Heroku app setup completed. Remember to set the following config vars: %s" % (django_blank_vars,))
