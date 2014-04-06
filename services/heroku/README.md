This directory contains files that will be used when pushing Perma to Heroku.

Files are copied to the appropriate places during deployment by `fab heroku_push`

settings.py will import arbitrary settings from the environment, e.g.:

    export DJANGO__SECRET_KEY=foo
    export DJANGO__INT__SITE_ID=1
    export DJANGO__DATABASES__default__NAME=perma