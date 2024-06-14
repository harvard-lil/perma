Perma - developer notes
========================

This document contains tips and tricks for working with Perma.

See the [installation documentation](./install.md) to get up and running.

  - [Perma - developer notes](#perma---developer-notes)
   - [Common tasks and commands](#common-tasks-and-commands)
     - [Run Perma](#run-perma)
     - [Run the tests](#run-the-tests)
     - [Run a particular test (python only)](#run-a-particular-test-python-only)
     - [Update the python dependencies](#update-the-python-dependencies)
     - [Update the node dependencies](#update-the-node-dependencies)
     - [Migrate the database](#migrate-the-database)
     - [Reset the database](#reset-the-database)
     - [Run arbitrary commands](#run-arbitrary-commands)
   - [Git and GitHub](#git-and-github)
   - [Logs](#logs)
   - [Code style and techniques](#code-style-and-techniques)
     - [User roles and permissions tests](#user-roles-and-permissions-tests)
     - [Javascript templates](#javascript-templates)
     - [Sending email](#sending-email)
     - [Asset pipeline](#asset-pipeline)
     - [Managing static files and user-generated files](#managing-static-files-and-user-generated-files)
     - [Hosting fonts locally](#hosting-fonts-locally)
   - [Schema and data migrations](#schema-and-data-migrations)
     - [Schema migrations and data migrations](#schema-migrations-and-data-migrations)
     - [Track migrations in Git and get started](#track-migrations-in-git-and-get-started)
   - [Testing and Test Coverage](#testing-and-test-coverage)
     - [Linting with flake8](#linting-with-flake8)
   - [Working with Celery](#working-with-celery)
   - [Working with Redis](#working-with-redis)
   - [Running with DEBUG=False locally](#running-with-debugfalse-locally)
   - [Perma Payments](#perma-payments)
     - [Test Perma Interaction with Perma Payments](#test-perma-interaction-with-perma-payments)
   - [Scoop](#scoop)

Common tasks and commands
-------------------------

These commands assume you have configured your shell with the alias defined in
the [shortcuts](./install.md#shortcuts) section of the installation docs, and that
Perma's Docker containers are up and running in the background:
-  run `docker compose up -d` to start the containers
-  run `docker compose down` to stop them when you are finished.

(If you are not running Perma inside Docker, most of the commands below
should still work: just skip the `d`!)

### Run Perma

`d invoke run`

That's it! You should now be able to load Perma in your browser at
`https://perma.test:8000/`. It will take a few seconds for the first page
to load, while we wait for Perma's CSS, JS and other assets to be compiled.

(Note: if you ran `init.sh` when setting up this instance of Perma, the necessary
SSL certs and keys should already be present. If they are not, or if they have
expired, you can run `bash make_cert.sh` to generate new files.)

To log in and explore Perma, try logging in as one of our
[test users (the `linkuser` objects)](https://github.com/harvard-lil/perma/blob/develop/perma_web/fixtures/users.json#L167). All test users have a password of "pass".

The server will automatically reload any time you made a change to the
`perma_web` directory: just refresh the page to see your changes.

Press `CONTROL-C` to stop the server.

### Run the tests

`d pytest`
`d npm test`

See [Testing and Test Coverage](#testing-and-test-coverage) for more
information about testing Perma.

### Run a particular test (python only)

Python tests are run via pytest. Pytest supports several ways to
[select and run tests](https://docs.pytest.org/en/latest/usage.html#specifying-tests-selecting-tests),
including a super-convenient keyword-matching option:

`d pytest -k "name_of_a_test_that_failed"`

`d pytest -k "a_specific_test_module"`

See [Testing and Test Coverage](#testing-and-test-coverage) for more
information about testing Perma.

### Update the python dependencies

Top-level requirements are stored in `requirements.in`. After updating that file, you should run

`d invoke pip-compile`

to freeze all subdependencies into `requirements.txt`.

To upgrade a single requirement to the latest version:

`d invoke pip-compile --args "-P package_name"`

### Update the node dependencies

Install new packages: `d npm install --save-dev package_name`
Uninstall new packages: `d npm uninstall package_name`

Update a single package:
- if necessary, change the pinned version in package.json
- `d npm update package_name`

Update all dependencies: ``

### Migrate the database

`d ./manage.py makemigrations`

`d ./manage.py migrate`

For more information on migrations, see [Schema and data migrations](#schema-and-data-migrations)

### Reset the database

1) `docker compose down` to delete your existing containers.
2) `docker volume rm perma_postgres_data` to delete the database.
3) `docker compose up -d` to spin up new containers.
4) `docker compose exec web invoke dev.init-db` to create a fresh database, pre-populated with test fixtures.

### Run arbitrary commands

You can run `d bash` to get a bash terminal in your container. Your python
environment will be activated and you will be logged in as root.

You can also prefix arbitrary commands with `d`:
-  `d which python` (output: the virtualenv's python)
-  `d ls` (output: /perma/perma_web)


## Git and GitHub

We use git to track code changes and use [GitHub](https://github.com/harvard-lil/perma) to host the code publicly.

The Master branch always contains production code (probably the thing currently running at [Perma.cc](http://perma.cc)) while the develop branch contains the group's working version. We follow [Vincent Driessen's approach](http://nvie.com/posts/a-successful-git-branching-model/).

Fork our repo, then make a feature branch on your fork. Issue a pull request to merge your feature branch into harvard-lil's develop branch when your code is ready.

Track issues using [GitHub Issues](https://github.com/harvard-lil/perma/issues).


## Logs

All of your logs will end up in `./services/logs`. As a convenience, you can tail -f all of them with `d invoke dev.logs`.


## Code style and techniques

### User roles and permissions tests

We have several types of users:

* Logged in users are identified the standard Django way: `user.is_authenticated`
* Users may belong to organizations. You should test this with `user.is_organization_user`.
* Users may belong to a registrar (`user.registrar is not None`). You should test this with `user.is_registrar_member()`.
* Admin users are identified the standard Django way: `user.is_staff`

Users that belong to organizations can belong to many, including organizations belonging to multiple registrars. Users who belong to a registrar may only belong to a single registrar. Users should not simultaneously belong to both organizations and to a registrar.


### Javascript templates

Use [Handlebars](http://handlebarsjs.com/) when injecting markup using JavaScript.

Our templates are pre-compiled by webpack. The source files are in `perma_web > static > js > hbs`


### Sending email

*All emails* should be sent using `perma.email.send_user_email` (for an email from us to a user) or
`perma.utils.send_admin_email` (for an email "from" a user to us). This makes sure that `from` and `reply-to` fields
are configured so our MTA will actually transmit the email.

We recommend addressing the email to user.raw_email rather than user.email (which is downcased), just in case.

On the development server, emails are dumped to the standard out courtesy of EMAIL_BACKEND in settings_dev.py.

### Asset pipeline

Front-end assets are processed and packaged by Webpack. Assets can be compiled with this command:

    docker compose exec web npm build

This is automatically run in the background by `d invoke run`, so there is usually no need to run it manually.

Compiled bundles generated by Webpack will be added to the git repository by CI if you omit them.

### Managing static files and user-generated files

We use Django's built-in functions to manage static assets (Javascript/CSS/etc.) and user-generated media (our link archives).

To make sure everything works smoothly in various environments (local dev, Linux servers, and cloud services),
be sure to use the following settings when referring to disk locations and URLs in your code and templates:

* STATIC_ROOT: Absolute path to static assets (e.g. '/tmp/perma/static/')
* STATIC_URL: URL to retrieve static assets (e.g. '/static/')
* MEDIA_ROOT: Absolute path to user-generated assets (e.g. '/tmp/perma/generated/')
* MEDIA_URL: URL to retrieve user-generated assets (e.g. '/media/')

The \_ROOT settings may have different meanings depending on the storage backend. For example,
STORAGES["default"] is set to use the Amazon S3 storage backend,
then MEDIA_ROOT would just be '/generated/' and would be relative to the root of the S3 bucket.

In templates, use the `{% static %}` tag and MEDIA_URL:

    {% load static %}
    <img src="{% static "img/header_image.jpg" %}">
    <img src="{{ MEDIA_URL }}{{ asset.image_capture }}">

Using the `{% static %}` tag instead of `{{ STATIC_URL }}` ensures that cache-busting and
pre-compressed versions of the files will be served on production.

In code, use Django's `storage` to read and write user-generated files rather than accessing the filesystem directly:

    from django.core.files.storage import storages

    with storages['default'].open('some/path', 'rb') as image_file:
        do_stuff_with_image_file(image_file)

Paths for default storage are relative to MEDIA_ROOT.

Further reading:

* [Django docs for default_storage](https://docs.djangoproject.com/en/dev/topics/files/)
* [Django docs for serving static files](https://docs.djangoproject.com/en/dev/howto/static-files/)

### Hosting fonts locally

We like to host our fonts locally. If you're linking a font from Google fonts and the licensing allows, check out [fontdump](https://pypi.python.org/pypi/fontdump/1.2.0)


##  Schema and data migrations

*** Before changing the schema or the data of your production database, make a backup! ***

If you make a change to the Django model (models get mapped directly to relational database tables), you'll need to create a [migration](https://docs.djangoproject.com/en/1.7/topics/migrations/). Migrations come in two flavors: schema migrations and data migrations.


### Schema migrations and data migrations

Schema migrations are used when changing the model structure (adding, removing, editing fields) and data migrations are used when you need to ferry data between your schema changes (you renamed a field and need to move data from the old field name to the new field name).

The most straight forward data migration might be the addition of a new model or the addition of a field to a model. When you perform a straight forward change to the model, your command might look like this

    $ d ./manage.py makemigrations

This will create a migration file for you on disk, something like,

    $ cat perma_web/perma/migrations/0003_auto__add_org__add_field_linkuser_org.py

Even though you've changed your models file and created a migration (just a python file on disk), your database remains unchanged. You'll need to apply the migration to update your database,

    $ d manage.py migrate

Now, your database, your model, and your migration should all be at the same point. You can list your migrations using the list command,

    $ d manage.py migrate --list

Data migrations follow the same flow, but add a step in the middle. See the [Django docs](https://docs.djangoproject.com/en/1.7/topics/migrations/#data-migrations) for details on how to perform a data migration.


### Import production-like data into the database

1) Obtain a database dump with the help of your friendly local dev ops engineer.
2) Make sure no containers are running: `docker compose down`.
3) Edit the `volumes` section of the `db` service of `docker-compose.yml`:
   - rename the `postgres_data` volume to something new like `prod_postgres_data`, and make the same change down at the bottom of the file in the `volumes` stanza.
4) Run `docker compose up -d`.
5) Run `bash ingest.sh -f path-to-file.dump`. It will take several minutes to complete. Expect a single non-fatal error at the end of the process, "role "rdsadmin" does not exist".

You should then be able to run as usual, and log into any account using the password "changeme".


### Track migrations in Git and get started

You should commit your migrations to your repository and push to GitHub.

    $ git add perma_web/perma/migrations/0003_auto__add_org__add_field_linkuser_org.py
    $ git commit -m "Added migration"


## Testing and Test Coverage

Python unit tests live in `perma/tests`, `api/tests`, etc.

Functional tests live in `functional_tests/`.

Javascript tests live in `spec/`.

See the [Common tasks and commands](#common-tasks-and-commands) for the
common techniques for running the tests.


### Linting with flake8

All code must show zero warnings or errors when running `flake8 .` in `perma_web/`.

Flake8 settings are configured in `perma_web/setup.cfg`

If you want to automatically run flake8 before pushing your code, you can add something like this to `.git/hooks/pre-commit` or `.git/hooks/pre-push`:

    #!/usr/bin/env bash
    docker compose exec -T web flake8 .
    exit $?

Be sure to mark the hook as executable: `chmod u+x .git/hooks/pre-commit` or `chmod u+x .git/hooks/pre-push`.

(You have to have started the containers with `docker compose up -d` for this to work.)


## Working with Celery

Celery does two things in Perma.cc: it runs the capture tasks and it runs scheduled jobs (to gather things nightly like statistics, just like cron might).

In development, it's sometimes easier to run everything synchronously, without the additional layer of complexity a 
Celery worker adds. By default Perma will run celery tasks synchronously. To run asynchronously, set `CELERY_TASK_ALWAYS_EAGER = False`
in settings.py. `CELERY_TASK_ALWAYS_EAGER` must be `False` if you are specifically testing or setting up a new a Celery <-> Django 
interaction or if you are working with LinkBatches (otherwise subtle bugs may not surface).


## Working with Redis

In our production environment we use Redis as a cache for our thumbnail data.
If you want to simulate the production environment:
-  find the "redis" stanza of `docker-compose.yml`, currently commented out, and comment in it
-  find the "volumes" stanza of `docker-compose.yml` and comment in `redis_data`
-  add the caches setting found in `settings_prod.py` to your `settings.py`


## Running with DEBUG=False locally

If you are running Perma locally for development using the default settings_dev.py, [DEBUG](https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-DEBUG) is set to true. This is in general a big help, because Django displays a detailed error page any time your code raises an exception. However, it makes it impossible to test your app's error handing, see your custom 404 or 500 pages, etc.

To run with DEBUG=False locally, first stop the webserver, if it's running. Add ```DEBUG=False``` to settings.py or (to alter settings\_dev.py). Then, run ``` d ./manage.py collectstatic```, which creates ```./services/django/static_assets``` (necessary for the css and other static assets to be served properly). Then, run ```d invoke run``` as usual to start the web server.

__NB__: With DEBUG=False, the server will not automatically restart each time you save changes.

__NB__: If you make changes to static files, like css, while running with DEBUG=False, you must rerun  ``` d manage.py collectstatic``` and restart the server to see your changes.

## Perma Payments

Aspects of Perma's paid subscription service are handled by the companion application, [Perma Payments](https://github.com/harvard-lil/perma-payments).

By default, Perma's `docker-compose` file will spin up a local Perma Payments for you to experiment with. For more fruitful experimentation, configure this Perma Payments to interact with Cybersource's test tier, by running Payments with a custom settings.py that contains our credentials. See `docker-compose.yml` and `/services/docker/perma-payments/settings.py.example` for more information. CyberSource will not be able to communicate its responses back to your local instance, of course, but you can simulate active subscriptions using the Django admin.

### Test Perma Interaction with Perma Payments

You may also decide to run both services by running `docker compose` in both repositories simultaneously, with a tweaked Perma network config.

First, head over to the [`Perma Payments` repo](https://github.com/harvard-lil/perma-payments/blob/develop/README.md#running-locally) for instructions on how to spin that up.

Once it's running, spin up Perma... but with a slightly different command than usual, so that it doesn't try to create its own Perma Payments, but instead uses the already-running one:

- `docker compose -f docker-compose.yml up -d`

Then, run Perma's dev server as usual:

`docker compose exec web invoke run`

When you are finished, take down the Perma containers by running:

`docker compose -f docker-compose.yml down`

Don't worry if you get the following error:

`ERROR: error while removing network: network perma-payments_default id 1902203ed2ca5dee5b57462201db417638317baef142e112173ee300461eb527 has active endpoints`

It just means that Perma Payments is still running: the network is maintained until both projects are down. Head back over to the Perma Payments repo and run `docker compose down` there... and you're done.


## Scoop

Perma's web archives are produced using [Scoop](https://github.com/harvard-lil/scoop): Perma capture requests call out to the [Scoop API](https://github.com/harvard-lil/perma-scoop-api/), which capture the requested website and return a WARC/WACZ to Perma.

By default, Perma's `docker-compose` file will spin up a local Scoop API for you to experiment with.

### Working with both repositories simultaneously

You may also decide to run both services by running `docker compose` in both repositories simultaneously, with a tweaked Perma network config.

First, head over to the [`Scoop API` repo](https://github.com/harvard-lil/perma-scoop-api/) for instructions on how to spin that up.

Once it's running, spin up Perma... but with a slightly different command than usual, so that it doesn't try to create its own Scoop API, but instead uses the already-running one:

- `docker compose -f docker-compose.yml up -d`

Then, run Perma's dev server as usual:

`docker compose exec web invoke run`

When you are finished, take down the Perma containers by running:

`docker compose -f docker-compose.yml down`

Don't worry if you get the following error:

`ERROR: error while removing network: network perma-scoop-api_default id 1902203ed2ca5dee5b57462201db417638317baef142e112173ee300461eb527 has active endpoints`
The Scoop API is still running: the network is maintained until both projects are down. Head back over to the Scoop API repo and run `docker compose down` there... and you're done.
