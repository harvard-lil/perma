Perma - developer notes
========================

This document contains tips and tricks for working with Perma.

- [Installing Perma](#installing-perma)
  - [Dependencies](#dependencies)
  - [Hosts](#hosts)
  - [Shortcuts](#shortcuts)
  - [Installation](#installation)
- [Common tasks and commands](#common-tasks-and-commands)
  - [Run Perma](#run-perma)
  - [Run the tests](#run-the-tests)
  - [Run a particular test (Python only)](#run-a-particular-test-python-only)
  - [Update the Python dependencies](#update-the-python-dependencies)
  - [Update the Node dependencies](#update-the-node-dependencies)
  - [Migrate the database](#migrate-the-database)
  - [Reset the database](#reset-the-database)
  - [Run arbitrary commands](#run-arbitrary-commands)
- [Git and GitHub](#git-and-github)
- [Logs](#logs)
- [Code style and techniques](#code-style-and-techniques)
  - [User roles and permissions tests](#user-roles-and-permissions-tests)
  - [Sending email](#sending-email)
  - [Error reporting and personal data](#error-reporting-and-personal-data)
  - [Asset pipeline](#asset-pipeline)
  - [Front-end styles, Bootstrap, and browser support](#front-end-styles-bootstrap-and-browser-support)
  - [Managing static files and user-generated files](#managing-static-files-and-user-generated-files)
  - [Hosting fonts locally](#hosting-fonts-locally)
- [Schema and data migrations](#schema-and-data-migrations)
  - [Schema migrations and data migrations](#schema-migrations-and-data-migrations)
  - [Track migrations in Git and get started](#track-migrations-in-git-and-get-started)
  - [Visualize schema](#visualize-schema)
- [Testing and Test Coverage](#testing-and-test-coverage)
  - [Browsers, and how each one trusts the test server](#browsers-and-how-each-one-trusts-the-test-server)
  - [Hangs: the per-test timeout, and why the login fixtures wait](#hangs-the-per-test-timeout-and-why-the-login-fixtures-wait)
  - [Failure screenshots](#failure-screenshots)
  - [Visual snapshots](#visual-snapshots)
  - [Accessibility baselines](#accessibility-baselines)
  - [Before/after screenshot capture](#beforeafter-screenshot-capture)
  - [Linting with Flake8](#linting-with-flake8)
- [Working with Celery](#working-with-celery)
- [Working with Redis](#working-with-redis)
- [Running with DEBUG=False locally](#running-with-debugfalse-locally)
- [Perma Payments](#perma-payments)
- [Filecheck](#filecheck)
- [Scoop](#scoop)
- [Working with Superset](#working-with-superset)

Installing Perma
-------------------------

Perma is a Python application built on the [Django](https://www.djangoproject.com/) web framework.

Perma has a lot of moving pieces. We recommend using [Docker](https://docs.docker.com/get-started/) for local development. If you are new to Docker, it may take some time before you are comfortable with its vocabulary and commands, but it allows you to jump right into coding instead of spending a lot of time getting all the services running on your machine.

For advice about production deployments, [send us a note](mailto:info@perma.cc)!

### Dependencies

* [Git](https://git-scm.com/install/)
* [Docker](https://docs.docker.com/get-started/get-docker/)
* [mkcert](https://github.com/FiloSottile/mkcert)

### Hosts

Perma serves content at several hosts. To ensure that URLs resolve correctly, add the following domains to your computer's hosts file:

```
127.0.0.1 perma.test api.perma.test rejouer.perma.test perma.minio.test
```

For additional information on modifying your hosts file, [try this help doc](https://docs.rackspace.com/docs/modify-your-hosts-file).

### Shortcuts

Docker commands can be lengthy. To cut down on keystrokes, we recommend adding the following to your shell config (e.g. `~/.bash_profile` or `~/.zshrc`).

```
alias d="docker compose exec web"
```

### Installation

Then check out the code:

```
git clone https://github.com/harvard-lil/perma.git
cd perma
```

Pull the prebuilt services after fetching new code. The `web` and `filecheck`
images build locally (`pull_policy: build`), so `docker compose up` rebuilds
them when their build inputs change and reuses cached layers otherwise:

```
docker compose pull
```

Start up the Docker containers in the background:

```
docker compose up -d
```

The first time this runs, it may take several minutes. With up-to-date Docker images, it should only take a few seconds.

Finally, initialize the databases and generate the SSL certificates and keys required to access your local Perma over SSL:

```
bash init.sh
```

You should now have a working installation of Perma! See [common commands](./developer.md#common-tasks-and-commands) to explore what you can do, like [running the application](./developer.md#run-perma) and [running the tests](./developer.md#run-the-tests).

When you are finished, spin down Docker containers by running:

```
docker compose down
```

#### Making macOS trust a self-signed certificate if it doesn't

It _sometimes_ happens that `mkcert`'s setup is incomplete, and macOS doesn't trust the certificates it generated as a result.

**Here's how to fix it:**

- Go to `Applications > Utilities > Keychain Access`
- Click on the `login` filter
- Drag and drop the `rootCA.pem` file `mkcert` generated onto the UI
- Look for the certificate in the list: it should start with `mkcert` followed by the name of your machine
- Right-click on it and pick `Get Info`
- Unfold the `Trust` dropdown, and pick `Always Trust` for the relevant categories.

If you're still encountering issues, you may want to open these URLs in your browser and manually bypass the security alerts:

```
https://perma.test:8000
https://rejouer.perma.test:8080
https://perma.minio.test:9000
```

Common tasks and commands
-------------------------

These commands assume you have configured your shell with the alias defined in the [shortcuts](#shortcuts) section, and that Perma's Docker containers are up and running in the background:
-  run `docker compose up -d` to start the containers
-  run `docker compose down` to stop them when you are finished.

(If you are not running Perma inside Docker, most of the commands below should still work: just skip the `d`!)

### Run Perma

```
d invoke run
```

That's it! You should now be able to load Perma in your browser at `https://perma.test:8000/`. It will take a few seconds for the first page to load, while we wait for Perma's CSS, JS and other assets to be compiled.

(Note: if you ran `init.sh` when setting up this instance of Perma, the necessary
SSL certs and keys should already be present. If they are not, or if they have
expired, you can run `bash make_cert.sh` to generate new files.)

To log in and explore Perma, try logging in as one of our
[test users (the `linkuser` objects)](https://github.com/harvard-lil/perma/blob/main/perma_web/fixtures/users.json#L167). All test users have a password of "pass".

The server will automatically reload any time you make a change to the `perma_web` directory: just refresh the page to see your changes.

Press `CONTROL-C` to stop the server.

### Run the tests

```
d pytest
d npm test
```

`d pytest` runs the browser tests in Chromium. To run the UI contract suite in Firefox
or WebKit as well, as CI does:

```
d bash -c 'pytest functional_tests/test_ui_*.py --browser firefox'
d bash -c 'pytest functional_tests/test_ui_*.py --browser webkit'
```

The `bash -c` is needed so the glob expands inside the container.

`d pytest` deselects the slow tests marked `sweep` (the accessibility sweep, see [Accessibility baselines](#accessibility-baselines)); `d pytest --all` runs them too.

See [Testing and Test Coverage](#testing-and-test-coverage) for more information about testing Perma.

### Run a particular test (Python only)

Python tests are run via pytest. Pytest supports several ways to [select and run tests](https://docs.pytest.org/en/latest/how-to/usage.html#specifying-tests-selecting-tests), including a super-convenient keyword-matching option:

```
d pytest -k "name_of_a_test_that_failed"
d pytest -k "a_specific_test_module"
```

See [Testing and Test Coverage](#testing-and-test-coverage) for more information about testing Perma.

### Update the Python dependencies

We use [uv](https://docs.astral.sh/uv/) to manage Python dependencies. Requirements are stored in `pyproject.toml`. To add, remove, or modify a dependency, you can update that file. If you like, you may then run the following to generate lockfiles (`uv.lock` and `requirements.txt`):

```
d invoke lock
```

To upgrade a single requirement to the latest version:

```
d invoke lock --args "--upgrade-package package_name"
```

### Update the Node dependencies

The image supplies Node 24 LTS and the npm it ships with, copied from a
digest-pinned official Node image rather than installed from a setup script.
`package.json` declares matching `engines` and `packageManager`, and
`perma_web/.npmrc` sets `engine-strict=true`, so an install on an unsupported
Node or npm fails instead of silently proceeding.

`npm-shrinkwrap.json` is the lockfile. Image builds install from it with
`npm ci`; use `npm ci` yourself whenever you want a build to match the lockfile
exactly rather than resolve fresh versions.

Install new packages: `d npm install --save-dev package_name`
Uninstall packages: `d npm uninstall package_name`

Update a single package:
- if necessary, change the pinned version in package.json
- Run: `d npm update package_name`

Update all dependencies: `d npm update`

After changing dependencies, rebuild the image (`docker compose build web`) so
its baked `node_modules` matches, and recreate the `node_modules` volume if the
container needs to pick the change up.

#### The js-wacz worker has its own manifest

`services/js-wacz/` is a second, independent npm project holding only
`@harvard-lil/js-wacz`, which `perma/celery_tasks.py` shells out to for WARC
to WACZ conversion. It is **not** part of `perma_web`'s dependency tree and is
not covered by `npm-shrinkwrap.json`.

Upgrading it always requires an image rebuild. `services/` is not bind-mounted
into the `web` container, and `perma_web/Dockerfile` deletes both manifests
right after running `npm ci --prefix /perma/services/js-wacz/`, so the container
holds only the installed `node_modules` and editing the manifest alone changes
nothing you can run. Bump the version, then `docker compose build web`.

Note also that `docker-compose.override.yml`'s `x-hash-paths` — the file list
whose hashes drive the web image tag — does not include these manifests, so a
worker-only dependency change does not by itself cause CI to rebuild the image.

### Migrate the database

```
d ./manage.py makemigrations
d ./manage.py migrate
```

For more information on migrations, see [Schema and data migrations](#schema-and-data-migrations).

### Reset the database

1) `docker compose down` to delete your existing containers.
2) `docker volume rm perma_postgres_data` to delete the database.
3) `docker compose up -d` to spin up new containers.
4) `docker compose exec web invoke dev.init-db` to create a fresh database, pre-populated with test fixtures.

### Run arbitrary commands

You can run `d bash` to get a bash terminal in your container. Your Python environment will be activated and you will be logged in as root.

You can also prefix arbitrary commands with `d`:
-  `d which python` (output: the virtualenv's python)
-  `d ls` (output: /perma/perma_web)


## Git and GitHub

We use Git to track code changes and use [GitHub](https://github.com/harvard-lil/perma) to host the code publicly.

Create feature branches from `main` and open pull requests against `main`.
The required `test / Lint` and `test / Test` checks must pass, with the branch
up to date, before merging. A merge to `main` tests and publishes a versioned
container image; it does not deploy a serving environment.

Deploy through merge-commit PRs:

1. `main` → `staging`: require a successful main push build for the exact source
   commit, then merge to deploy the published image to staging.
2. QA staging, then `staging` → `prod`: require a successful staging push deploy
   for the exact source commit, then merge to promote the staged image to production.

The promotion checks reject other source branches and forks. If the upstream
build or deploy has not finished successfully, rerun the promotion check after
it succeeds. Do not squash or rebase promotion PRs: the workflows rely on merge
history. Deploy-time checks also verify the selected image and source tree.
Keep staging at the reviewed release until production promotion completes.

`develop` is retained but frozen against updates and deletion. New PRs belong
on `main`; coordinate with authors before retargeting older PRs. The old Salt
branches `stage` and `salt-prod` are retained for the transition, not used for
new releases. Production now runs on ECS. The initial `prod` branch was seeded
from the staged cutover release without dispatching a deployment; subsequent
promotions use the workflow above. Confirm a successful deployment run and its
image digest before treating a branch tip as proof of what is running.

Tags are not part of the release flow. The repository has one tag namespace,
`baselines/<name>`, which asks CI to render a set of visual baselines and nothing
else; see [Publishing a set](#publishing-a-set). Those tags are never moved or reused,
and only maintainers should create them.

GitHub's `staging` and `prod` environments are restricted to their matching
branches. Each needs `AWS_ROLE_TO_ASSUME`, `STATIC_BUCKET`,
`CLOUDFLARE_ZONE_ID`, `MAINTENANCE_SCRIPT`, `MAINTENANCE_HOSTNAMES`, and
`SITE_URL` variables, plus `CLOUDFLARE_API_TOKEN` and `SLACK_WEBHOOK_URL`
secrets. Infrastructure and maintenance-page controls live in
[lil-terraform](https://github.com/harvard-lil/lil-terraform/tree/main/perma).

Track issues using [GitHub Issues](https://github.com/harvard-lil/perma/issues).


## Logs

All of your logs will end up in `./services/logs`. As a convenience, you can tail -f all of them with `d invoke dev.logs`.


## Code style and techniques

### User roles and permissions tests

We have several types of users:

* Logged-in users are identified in the standard Django way: `user.is_authenticated`.
* Users may belong to organizations. You should test this with `user.is_organization_user`.
* Users may belong to a registrar (`user.registrar is not None`). You should test this with `user.is_registrar_user()`.
* Users might be sponsored by registrars. You should test this with: `user.is_sponsored_user()`.
* Admin users are identified in the standard Django way: `user.is_staff`.

Users that belong to organizations can belong to many, including organizations belonging to multiple registrars. Users who belong to a registrar may only belong to a single registrar. Users should not simultaneously belong to both organizations and to a registrar. Users can be sponsored by many registrars.

### Sending email

*All emails* should be sent using `perma.email.send_user_email` (for an email from us to a user) or `perma.email.send_admin_email` (for an email from a user to us). This makes sure that `from` and `reply-to` fields are configured so our MTA will actually transmit the email.

We recommend addressing the email to user.raw_email rather than user.email (which is downcased), just in case.

On the development server, emails are dumped to the standard out courtesy of EMAIL_BACKEND in settings_dev.py.

### Error reporting and personal data

Perma runs two Sentry SDKs — the Python SDK for Django and Celery, initialized
in `perma/settings/utils/post_processing.py`, and `@sentry/browser` for the
front end, initialized at the top of `static/js/global.js`. **Neither is
configured to send personally identifying data, and that is deliberate. Prefer
privacy over diagnostic richness when the two conflict.**

On the Python side this is explicit: `sentry_sdk.init()` is passed
`send_default_pii=settings['SENTRY_SEND_DEFAULT_PII']`, and
`SENTRY_SEND_DEFAULT_PII` defaults to `False` in `settings_common.py`. With it
off, Sentry does not attach the authenticated user or the request's client IP
to an event.

On the browser side the equivalent option, `sendDefaultPii`, is **deliberately
not set at all**. Two consequences are worth knowing before you change that
`Sentry.init` call:

- From `@sentry/browser` v9 onward, leaving `sendDefaultPii` unset also stops
  Sentry's *backend* from inferring the reporter's IP address from the incoming
  request. Earlier majors inferred it by default. We are on v10, so this is in
  effect: front-end error reports no longer carry IP addresses, where under the
  v7 SDK they did. That is a change we want, not a regression to work around —
  setting `sendDefaultPii: true` to restore the old inference would be a privacy
  decision, and the project's answer to it is no.
- `SENTRY_SEND_DEFAULT_PII` is **not** in `TEMPLATE_VISIBLE_SETTINGS`, so it
  never reaches the browser through `js_config.html`. Wiring the front end to a
  PII flag would mean widening that allow-list on purpose — a deliberate act,
  not something that can happen by accident while editing front-end code.

If you have a diagnostic problem that seems to need PII, raise it rather than
flipping the flag: the usual answer is more context on the event (a release
tag, a route name, an anonymous identifier) rather than the user's identity or
address.

### Asset pipeline

Front-end assets are processed and packaged by Webpack. Assets can be compiled with this command:

```
docker compose exec web npm run build
```

This is automatically run in the background by `d invoke run`, so there is usually no need to run it manually.

Vitest uses Vite only to transform test files; it does not replace Webpack or
generate application assets.

Webpack 5 handles fonts and images through asset modules, inlining anything
under 10 KB as a `data:` URI and emitting the rest as content-hashed files.
Bundle names and paths reach Django through `webpack-bundle-tracker`, which
writes `webpack-stats.json` for `django-webpack-loader` to read; the build
contract both sides depend on is covered by `spec/build/webpack-contract.spec.js`
and `perma/tests/test_asset_pipeline.py`.

Because the entry bundles use Vue's `esm-bundler` build, `webpack.config.js`
sets `optimization.nodeEnv` explicitly. Webpack 5 no longer shims Node globals,
so without it every page using the Vue app dies on `process is not defined`.

Compiled bundles (`perma_web/static/bundles/` and `perma_web/webpack-stats.json`) are build output and are not committed. `perma_web/frontend_assets.py` rebuilds them when their inputs change, and `d invoke run` and `d pytest` call it; `d invoke dev.build-frontend` runs it by hand. The container image ignores any local build and compiles its own in the Dockerfile's `assets` stage.



### Front-end styles, Bootstrap, and browser support

#### Supported browsers

`perma_web/browserslist` is the single declaration of what Perma supports:

```
last 3 versions
not ie < 10
```

Two tools read it, and nothing else should hard-code a browser assumption:
Autoprefixer (via `postcss-loader`) uses it to decide which CSS prefixes to
emit, and `@babel/preset-env` uses it to decide which JavaScript syntax to
transpile and which `core-js` polyfills to pull in. Widening or narrowing
support is therefore a one-line change here, followed by a rebuild — but it
also changes bundle size and output, so treat it as a product decision rather
than a cleanup.

This list is the yardstick for dropping legacy shims. A compatibility library
should not be kept without an identified browser in this range that needs it;
FastClick was removed on exactly those grounds.

The browser tests exercise the three rendering engines behind that range — Chromium
(Blink), Firefox (Gecko) and WebKit — as Playwright's Linux builds. That catches
engine-level CSS and JavaScript differences, but **Playwright's WebKit is not Safari**:
it has neither Safari's browser chrome nor iOS behavior, so real iOS Safari is not
covered.

#### Responsive breakpoints

Perma's own breakpoints live in `static/css/_vars-global.scss` and are built
from an 8-pixel base unit (`$grid`):

| Variable | Computed | Mixin |
| --- | --- | --- |
| `$width-mobile` | 320px | `respond-mobile` |
| `$width-xmobile` | 384px | `respond-xmobile` |
| `$width-tablet` | 768px | `respond-tablet` |
| `$width-desktop` | 990px | `respond-desktop` |
| `$width-wide` / `$width-max` | 1200px | `respond-wide` / `respond-max` |

Use the `respond-*` mixins from `_mixins-global.scss` rather than writing raw
media queries, so a breakpoint change stays a one-line edit. Note that some
trailing comments beside these declarations are stale and disagree with the
computed values — the arithmetic is authoritative.

#### Bootstrap

Perma retains **Bootstrap 3.4** (`bootstrap-sass` 3.4.3) while the ECS and
backend dependency updates are validated. The Bootstrap 5 migration is deferred
for a separate UI QA round. Templates, Vue components, stylesheets, and the
Bootstrap JavaScript plugins must move together when that migration resumes.

`_bootstrap-custom.scss` (main site) and `_bootstrap-custom-archive.scss`
(archive playback) import separate subsets of Bootstrap's Sass partials.
Test both entry points when changing shared layout rules. Bootstrap JavaScript
is imported through the `bootstrap-js` webpack alias in `static/js/global.js`;
its dropdown, collapse, and tab plugins use `data-toggle` attributes and jQuery
events such as `shown.bs.collapse`.

#### Sass

The stylesheets use Dart Sass with legacy `@import` partials and Compass
mixins. `sassOptions.quietDeps` suppresses dependency deprecations; warnings
from Perma's own styles remain visible. This works with the current locked
Sass version but does not eliminate the eventual Sass migration work.

#### jQuery and the remaining legacy libraries

Perma uses **jQuery 3.7.1** for Bootstrap 3 compatibility. Webpack's
`ProvidePlugin` injects `"jquery"` for `$`, `jQuery`, and `window.jQuery`.
jsTree's declared peer dependency accepts this version, so no override is
needed. After jQuery-adjacent changes, confirm `npm ls jquery` reports one
deduplicated instance. Moving back to jQuery 4 requires changing the injection
to `["jquery", "default"]` and reviewing both Bootstrap and jsTree compatibility.

**spin.js 4 needs its stylesheet imported.** `Spinner.vue` imports
`spin.js/spin.css` alongside the named `{ Spinner }` export, because v4 animates
via CSS `@keyframes` shipped in that file rather than from JavaScript. Drop the
import and the spinner still mounts and raises nothing — it just stops moving.
`spec/build/webpack-contract.spec.js` asserts the built `dashboard.css` contains
`@keyframes spinner-line-fade-default` for exactly this reason. For the same
reason `Spinner.vue` expresses reduced motion as `animation: 'none'` rather than
`speed: 0`, which merely emitted an invalid duration the browser discarded.

**Removed, with no replacement needed.** `jquery-form`, `waypoints`, and
`modernizr` were declared but imported by nothing; `resolve-url-loader` was
removed after building with and without it produced byte-identical CSS, source
maps, and emitted assets. It rewrites relative `url()`s to resolve against the
partial that wrote them rather than the entry, and every Perma `.scss` lives in
one directory, so the two resolutions agree. Restore it if SCSS ever moves into
subdirectories.

#### Accessibility and UI behavior are covered by tests

The Playwright suite in `functional_tests/` pins the front-end contract by
behavior and semantics — accessible name, role, `aria-expanded`, focus order,
computed geometry — rather than by framework class names, so that a future
framework upgrade has to preserve behavior instead of markup:

| File | Covers |
| --- | --- |
| `test_ui_navigation.py` | navbar disclosure, account dropdown, skip links, landmark roles |
| `test_ui_forms.py` | label association, readable errors, `aria-invalid` |
| `test_ui_components.py` | tabs, collapse panels, dialogs, pagination, table semantics |
| `test_ui_responsive.py` | breakpoint boundaries, grid stacking, no horizontal scroll |
| `test_ui_computed_style.py` | typography, link states, box model, button colour, z-index |
| `test_ui_archive.py` | archive details tray, view-mode toggle, playback structure |
| `test_ui_touch.py` | tap activation under mobile emulation |
| `test_ui_layout_parity.py` | column layout and archive header/frame geometry |

These files run in **Chromium, Firefox and WebKit**, locally with `--browser` and in CI
as separate steps (see
[Browsers, and how each one trusts the test server](#browsers-and-how-each-one-trusts-the-test-server)).
When changing UI markup, expect to keep these passing unmodified in all three engines. If an
assertion has to change, that is a product-visible behavior change and should
be treated as one. One test is currently red under Firefox on a known defect; the CI
section of that link says which and why.

Note that `test_ui_touch.py` builds its own browser contexts with an iOS Safari
user agent. That is not decoration: libraries that gate themselves on
`navigator.userAgent` can be entirely inert under the default Chromium UA, so a
touch test written without the override can pass whether or not the code under
test is even running.

### Managing static files and user-generated files

We use Django's built-in functions to manage static assets (JavaScript/CSS/etc.) and user-generated media (our link archives).

To make sure everything works smoothly in various environments (local dev, Linux servers, and cloud services), be sure to use the following settings when referring to disk locations and URLs in your code and templates:

* STATIC_ROOT: Absolute path to static assets (e.g. '/tmp/perma/static/')
* STATIC_URL: URL to retrieve static assets (e.g. '/static/')
* MEDIA_ROOT: Absolute path to user-generated assets (e.g. '/tmp/perma/generated/')
* MEDIA_URL: URL to retrieve user-generated assets (e.g. '/media/')

The \_ROOT settings may have different meanings depending on the storage backend. For example, if `STORAGES["default"]` is set to use the Amazon S3 storage backend, then `MEDIA_ROOT` would just be `/generated/` and would be relative to the root of the S3 bucket.

In templates, use the `{% static %}` tag and `MEDIA_URL`:

    {% load static %}
    <img src="{% static "img/header_image.jpg" %}">
    <img src="{{ MEDIA_URL }}{{ asset.image_capture }}">

Using the `{% static %}` tag instead of `{{ STATIC_URL }}` ensures that cache-busting and pre-compressed versions of the files will be served on production.

In code, use Django's `storage` to read and write user-generated files rather than accessing the filesystem directly:

    from django.core.files.storage import storages

    with storages['default'].open('some/path', 'rb') as image_file:
        do_stuff_with_image_file(image_file)

Paths for default storage are relative to `MEDIA_ROOT`.

In local development, the `s3` service keeps objects as plain files in the `s3_data` Docker volume: each bucket is a directory under `/data`, and each object is a file at its key's path. To look at them:

```
docker compose exec s3 ls -R /data/perma-storage
docker compose cp s3:/data/perma-storage ./perma-storage-copy
```

Read files this way, but add or change them through `storages` or an S3 client. The gateway keeps each object's ETag and content type in extended file attributes, which files written directly into the volume lack.

Further reading:

* [Django docs for file storage](https://docs.djangoproject.com/en/stable/topics/files/)
* [Django docs for serving static files](https://docs.djangoproject.com/en/stable/howto/static-files/)

### Hosting fonts locally

We like to host our fonts locally. If you're linking a font from Google Fonts and the licensing allows, check out [fontdump](https://pypi.org/project/fontdump/).


## Schema and data migrations

*** Before changing the schema or the data of your production database, make a backup! ***

If you make a change to a Django model (models are mapped directly to relational database tables), you need to create a [migration](https://docs.djangoproject.com/en/stable/topics/migrations/). Migrations come in two flavors: schema migrations and data migrations.


### Schema migrations and data migrations

Schema migrations are used when changing the model structure (adding, removing, editing fields) and data migrations are used when you need to ferry data between your schema changes (you renamed a field and need to move data from the old field name to the new field name).

The most straightforward schema change might be the addition of a new model or a new field on a model. When you make a straightforward change to the model, your command might look like this:

```
d ./manage.py makemigrations
```

This will create a migration file for you on disk, something like:

```
cat perma_web/perma/migrations/0003_auto__add_org__add_field_linkuser_org.py
```

Even though you've changed your models file and created a migration (just a Python file on disk), your database remains unchanged. You'll need to apply the migration to update your database:

```
d ./manage.py migrate
```

Now, your database, your model, and your migration should all be at the same point. You can list your migrations using the below command:

```
d ./manage.py showmigrations
```

Data migrations follow the same flow, but add a step in the middle. See the [Django docs](https://docs.djangoproject.com/en/stable/topics/migrations/#data-migrations) for details on how to perform a data migration.


### Import production-like data into the database

1) Obtain a database dump with the help of your friendly local DevOps engineer.
2) Make sure no containers are running: `docker compose down`.
3) Edit the `volumes` section of the `db` service of `docker-compose.yml`:
   - rename the `postgres_data` volume to something new like `prod_postgres_data`, and make the same change in the `volumes` section at the bottom of the file.
4) Run `docker compose up -d`.
5) Run `bash ingest.sh -f path-to-file.dump`. It will take several minutes to complete. Expect a single non-fatal error at the end of the process: the message `role "rdsadmin" does not exist`.

You should then be able to run as usual, and log into any account using the password "changeme".


### Track migrations in Git and get started

You should commit your migrations to your repository and push to GitHub.

```
git add perma_web/perma/migrations/0003_auto__add_org__add_field_linkuser_org.py
git commit -m "Added migration"
git push
```


### Visualize schema

In order to visualize the database schema and see all of the models, visit:

`/schema-viewer/`: This route renders the chart of db models, allows a few customization options such as app filtering and visuals.
`/schema-viewer/schema/`: This route displays the raw JSON data of the chart.


## Testing and Test Coverage

Python unit tests live in `perma/tests`, `api/tests`, etc.

Functional tests live in `functional_tests/`.

JavaScript tests live in `spec/`.

`npm test` runs the Vitest suite in JSDOM. Browser behavior remains covered by
the Playwright functional suite in `functional_tests/`; Vitest does not require
a local browser. JavaScript linting and type-checking are not currently
configured.

The `test_ui_*.py` files in `functional_tests/` are the front-end contract:
they pin UI behavior and accessibility semantics rather than framework markup,
so a CSS-framework upgrade has to preserve behavior. See
[Front-end styles, Bootstrap, and browser support](#front-end-styles-bootstrap-and-browser-support)
before changing them.

### Browsers, and how each one trusts the test server

The Playwright suite runs on Chromium unless told otherwise. Firefox and WebKit are
installed in the image too, and are selected per run; flags can be repeated:

```
d pytest functional_tests/test_ui_navigation.py --browser firefox
d pytest functional_tests/test_ui_navigation.py --browser chromium --browser webkit
```

Functional tests load pages from an HTTPS live server using the mkcert
certificate, and the engines trust it differently:

- **Chromium trusts it for real.** The `set_up_certs` fixture in `conftest.py` adds
  mkcert's root CA to `$HOME/.pki/nssdb`. Client-side archive playback needs a
  trusted secure context, so Chromium keeps this strict path.
- **Firefox and WebKit ignore certificate errors instead.** Neither reads that NSS
  database (Firefox uses a per-profile store, and Playwright gives it a fresh profile
  each launch; Playwright's Linux WebKit has no NSS store at all), so without help
  they reject every page. `browser_context_args` in `conftest.py` therefore sets
  `ignore_https_errors` for every engine except Chromium.

The consequence is that **a certificate problem is only caught under Chromium**. That
trade was made deliberately so the other engines could run at all; the history is in
`.plans/plan_browser-testing-and-vite.md` (finding F12).

In CI (`.github/workflows/lint_test.yml`), the full suite runs on Chromium with
coverage, then the `test_ui_*.py` contract suite runs again on Firefox and on WebKit,
each as its own step. The WebKit step fails the build like any other. The Firefox step
is marked `continue-on-error` for now: `test_skip_links_precede_the_navigation` fails
there on a known product defect (Firefox makes `<body>` a keyboard tab stop), left red
on purpose until the CSS is fixed. While that flag is set, *any* Firefox failure shows
as a red step without failing the build, so check the step's result when touching the
UI.

### Hangs: the per-test timeout, and why the login fixtures wait

Every test has a **180-second limit** (`pytest-timeout`, configured in
`[tool.pytest.ini_options]` in `pyproject.toml`). A test that exceeds it fails with a
stack dump instead of hanging the run. The limit is about six times the slowest test
measured. It uses the `thread` method, which kills the stuck pytest-xdist worker; xdist
replaces it and the run continues, reporting `worker 'gwN' crashed while running …`
for the test that hung. A hang inside Playwright's synchronous API is not reliably
interruptible by a signal, which is why the `signal` method is not used.

The limit exists because of a real hang, now fixed at its cause. `page.set_viewport_size`
is one of the few Playwright calls with **no timeout of its own**, and under Firefox it
can fail to return when called while a page is still settling after a navigation. The
login fixtures used to return while the
post-login page was still settling — `log_in_user` waited for nothing at all — so a test
that logged in and then resized could hang Firefox forever. Both `log_in` and
`log_in_user` now return only after:

1. the logout form is attached, which proves the login took; and
2. the network is idle. After login, `/manage/create/`'s folder tree rewrites the URL to
   `?folder=N` about 100 ms *after* the page's `load` event, and only for some users, so
   neither "page loaded" nor a single URL pattern is a reliable "settled" signal.

When writing a test that changes the viewport, prefer doing it before the first
navigation.

### Failure screenshots

When a browser test fails, pytest-playwright saves a full-page screenshot of the page under
`failed_test_files/` (the `--screenshot only-on-failure`, `--full-page-screenshot` and
`--output` options in `addopts` in `pyproject.toml`). In CI, the Firefox and WebKit steps
pass their own `--output`, `failed_test_files_firefox` and `failed_test_files_webkit`.

pytest-playwright empties its output directory at the start of every run. To keep a
screenshot, copy it out first, or pass `--output` to point the next run somewhere else.

A `page.screenshot()` call in a test is viewport-sized unless it passes `full_page=True`.

### Visual snapshots

The `assert_snapshot` fixture (in `conftest.py`) compares a page with a stored baseline
image. It settles the page (network idle, lazy images loaded, fonts ready), takes a
full-page screenshot with animations disabled, and compares it pixel by pixel. The
comparison itself is `functional_tests/image_diff.py`, which uses only Pillow.

```python
def test_landing_looks_the_same(page, ui_urls, assert_snapshot):
    page.set_viewport_size({"width": 1200, "height": 900})
    page.goto(ui_urls("landing"))
    assert_snapshot(page, "landing@1200")
```

- **Tolerance.** A pixel differs when any colour channel is off by more than
  `SNAPSHOT_TOLERANCE` (3, out of 255). A difference of exactly 3 passes. The size of the
  image must match exactly. Measured on 20 pages at 5 widths in all three engines:
  repeat renders on one machine were identical, and arm64 against amd64 differed by at
  most 2 per channel, with one exception (the archive page at 320 px, where a page script can leave a gap
  above the archive that depends on timing; a page defect, not rendering noise). A 1 px
  shift of one element differs by 200 or more, so the tolerance sits well clear of both.
- **Masks.** Pass Playwright locators, as in `mask=[page.locator("<selector>")]`. Their regions are painted over before
  the comparison, so use them for content that changes between runs. Locate regions by
  selector, not by coordinates: their position changes with the viewport width.
  - A mask hides pixels, not layout. Text whose length varies, such as a date or a name,
    can wrap and move what comes after it, and no mask stops that. Use fixed test data
    for such text instead.
  - Mask a block element rather than a line of inline text. The mask is drawn on whole
    pixels, and a glyph's anti-aliased edge at a fractional position can fall just
    outside it.
  - A mask whose selector matches nothing does nothing, so check that it matches.
- **Content that appears late.** The fixture waits for network idle, lazy images and
  fonts, but not for content drawn after that. An archive's replay frame is the example.
  Wait for that content before calling `assert_snapshot`, for example the replayed
  page's heading, as `check_playback` in `functional_tests/test_links.py` does.
- **Updating baselines.** `--update-snapshots` writes a baseline only when it is missing
  or the page differs from it beyond the tolerance, and those tests pass. A baseline
  within tolerance is left alone, so a run on another architecture doesn't rewrite every
  PNG over rendering noise. The PNGs are not tracked by git (see
  [Baseline sets](#baseline-sets)), so an update changes only the local working copy.
  Without the flag, a missing baseline fails the test; nothing is created silently.
- **Where baselines live.** In a working copy that git and `.dockerignore` both ignore:
  `functional_tests/baselines/<browser>/<test file>/<test function>/<name>.png`, one
  directory per engine. Its contents come from the baseline set that
  `functional_tests/BASELINE_SET` names (below); without that file, the directory is
  used as it is. Parametrized tests share a function name, so give each case its own
  `name`. A test can override the `snapshot_dir` fixture to use another directory (no
  set is then fetched), and `update_snapshots` to force the flag.
- **When a comparison fails.** The test fails with the number of pixels over tolerance,
  the worst channel difference, the bounding box and both sizes. `<name>-expected.png`,
  `<name>-actual.png` and `<name>-diff.png` are written to the test's directory under
  `failed_test_files/`, next to the failure screenshot. The diff is a faded copy of the
  actual image with differing pixels in red. If the sizes differ, the diff is as large
  as the bigger image, and the region only one of them covers is blue.

#### Baseline sets

Baseline PNGs are kept out of git, so the repository and the image never grow with
them. A set of baselines is one immutable tarball, named `YYYY-MM-DD-<slug>`. The
committed file `functional_tests/BASELINE_SET` names the set the code is tested
against, with the tarball's sha256, so every commit records its baselines:

```
set=2026-10-28-bootstrap3
sha256=<64 lowercase hex digits>
```

The `snapshot_dir` fixture depends on the session fixture `baseline_set`, which calls
`ensure_set` in `functional_tests/baseline_sets.py` once per pytest worker, before the
first test that reads a baseline:

- **No pointer file:** nothing happens; `functional_tests/baselines/` is used as it is.
  This is the state until a first set is named.
- **Stamp matches:** `functional_tests/baselines/.set` records the set the working copy
  holds. When it equals the pointer, nothing is downloaded.
- **Otherwise** it downloads `https://test-baselines.perma.cc/sets/<name>.tar`, checks
  the sha256 against the pointer, and extracts the tarball into
  `functional_tests/baselines.tmp/`. The working copy moves to
  `functional_tests/baselines.prev/` (replacing an older one), the new set takes its
  place, the stamp is written last, and one line goes to stderr (pytest captures it with
  the first test that needed it). A missing set (HTTP 403), a network failure or a hash
  mismatch fails those tests with a message saying what to check, and leaves the working
  copy as it was. Nothing is retried; the messages name the command below that retries or
  repairs it.
- **Workers.** Under `-n auto` every worker gets this far. A lock on
  `functional_tests/baselines.lock` lets one download while the others wait, then read
  the new stamp and skip the network.
- **Tarball contents.** The tarball holds the directory's contents, `<browser>/...` at its
  top level. Only regular files and directories are extracted; absolute paths, `..` and
  links are refused before anything is written.
- **Local edits are not kept.** Switching sets moves the working copy, including PNGs
  that `--update-snapshots` rewrote, to `baselines.prev/`, and the next switch discards
  it. Copy out anything you want to keep.
- **`PERMA_BASELINES_FETCH=0`** (or `false`, `no`) turns all of this off and uses the
  directory as it is: for working offline, or for rendering a set from an empty directory.
- **`PERMA_BASELINES_URL`** replaces the base URL. The default host is LIL's, read-only
  for everyone; a fork that stores its own sets points this at its own host.
- **The `visual` marker** (in `pyproject.toml`) is for tests that call `assert_snapshot`,
  so that they can be run alone with `-m visual`.

Two invoke tasks (`tasks/baselines.py`) manage the working copy and the pointer by hand.
`functional_tests/` is bind-mounted into the container, so `d invoke` and a pytest run on
the host see the same files; don't run them at the same time.

- **`d invoke baselines.fetch`** does what pytest does and prints one line: fetching is
  off (with the variable's value), legacy mode (no pointer file), the set is current
  (nothing downloaded), or the set was fetched, with its file count, size and whether the
  previous copy was kept. It doubles as a status check.
- **`--force`** downloads the set again even when the working copy already holds it, for
  a copy you no longer trust. It applies to the pointer's set (whose hash is still
  checked; a disabled fetch or a missing pointer file still does nothing) and to `--name`.
- **`--name NAME`** previews a set that no commit names yet. It downloads NAME and
  installs it as above, so the working copy moves to `baselines.prev/`, and the stamp
  records the sha256 of what was downloaded; there is no hash to check it against. If the
  working copy already holds NAME, nothing is downloaded. The preview lasts only until the
  next pytest run, which swaps the pointer's set back in unless NAME has been adopted.
- **`d invoke baselines.adopt NAME`** makes NAME the committed set. If the working copy
  already holds NAME (after a preview), its stamp's hash is reused; otherwise NAME is
  downloaded and installed as `--name` does. It writes `functional_tests/BASELINE_SET`,
  prints its two lines, counts the PNGs changed, added and removed against
  `baselines.prev/` (by path and sha256, naming the set that copy holds, or saying there
  is no previous copy), and ends by reminding you to commit `functional_tests/BASELINE_SET`;
  nothing is committed for you. Adopting the set the pointer names and the working copy
  holds is a no-op, and says so. After a hash mismatch, if the stored set is the right
  one, `adopt` rewrites the pointer from a fresh download.
- **Errors.** Both tasks exit with status 1 and the error's message, without a traceback,
  when a set is missing, a download fails, a hash differs or a name is malformed.
  `--name` and `adopt` ignore `PERMA_BASELINES_FETCH`: they name a set explicitly.
- **Which sets exist.** Every set has a `baselines/<name>` git tag; newest first:

  ```
  git fetch --tags && git tag -l 'baselines/*' --sort=-creatordate
  ```

  There is deliberately no `latest`. A commit names its set, so a newer set never
  changes what an older commit is tested against.

The module's unit tests, `functional_tests/test_baseline_sets.py`, and the tasks' tests,
`tasks/test_baselines.py`, use in-memory tarballs and a fake fetcher: no network, browser
or database.

#### Publishing a set

Sets are rendered and uploaded by the `Baselines` workflow
(`.github/workflows/baselines.yml`) and by nothing else. Nothing publishes from a
developer's machine, and no developer holds credentials that can write a set: pushing a
tag is how you ask for one.

1. **Make the pages right locally.** Run the `visual` tests against the committed set and
   fix what fails; `--update-snapshots` shows locally what a new set would hold. Those
   local PNGs are not what gets published: the workflow renders its own.
2. **Push a tag at the commit to render**, `baselines/` followed by the set name:

   ```
   git tag baselines/2026-11-02-new-header <commit>
   git push origin baselines/2026-11-02-new-header
   ```

   The name is `YYYY-MM-DD-<slug>`, lowercase, with no further `/`; the workflow refuses
   any other tag under `baselines/`. A tag can point at a branch commit, so a set can be
   made and reviewed before the branch is merged.
3. **The workflow renders and uploads.** It builds the test image as CI does and runs
   every `visual` test with `--update-snapshots` in Chromium, Firefox and WebKit, starting
   from an empty directory (`PERMA_BASELINES_FETCH=0`). It stops if any of those tests
   fails or none wrote a baseline. It then fetches the set that the commit's
   `functional_tests/BASELINE_SET` names and compares the new render with it (with no
   pointer file, every image counts as added), packs the set reproducibly, and uploads it
   once. An existing set is never overwritten: a re-run after a successful upload fails at
   that last step (HTTP 412) and changes nothing. A run that failed earlier uploaded
   nothing; re-run it, or, if the code has to change, tag the new commit with a new name.
4. **Review.** The run's artifact `baseline-report-<name>` holds `index.html`: counts per
   browser; for every changed baseline the expected, actual and diff images with the
   comparison's numbers (differing pixels, worst channel difference, bounding box, both
   sizes); thumbnails of the added images; and the removed paths. A baseline within
   `SNAPSHOT_TOLERANCE` of the previous one counts as unchanged. The job summary repeats
   the counts and gives the set's two pointer lines.
5. **Adopt and commit.** `d invoke baselines.adopt <name>` downloads the set, writes
   `functional_tests/BASELINE_SET` (the job summary's two lines), and counts the changes
   against your previous copy. Commit the pointer with the code it belongs to.

A tag is never moved or reused: it names an immutable set. To change a set, tag again
under a new name; a set that nothing adopts stays stored and unused.

**Forks.** The workflow uploads with the role that the repository variable
`BASELINES_AWS_ROLE_TO_ASSUME` names. A fork has none, so in a fork the workflow stops at
its first step and says why. A fork that wants its own sets stores the tarballs
somewhere of its own, as `<base>/<name>.tar`, and sets `PERMA_BASELINES_URL` to that base.

The report is `functional_tests/baseline_report.py`. Its tests,
`functional_tests/test_baseline_report.py`, draw their images with Pillow and use a fake
fetcher.

### Accessibility baselines

`functional_tests/test_accessibility.py` scans the same 20 pages at the same five widths
as the screenshot capture tool (they share `functional_tests/control_pages.py`) with
axe-core, in each engine, and compares what it finds with a stored baseline.

- **It is a sweep.** The 100 cases carry the `sweep` marker (registered in `pyproject.toml`),
  and `conftest.py` deselects them unless `--all`, `--update-a11y-baselines` or
  `--update-snapshots` is passed, so plain `pytest` stays fast: the sweep adds about two
  minutes in Chromium. The summary shows how many tests were deselected. CI's `pytest`
  step doesn't pass `--all` yet, so it doesn't run the sweep. Mark any future
  page-by-page test the same way.
- **What it checks.** The `assert_a11y_baseline` fixture (in `conftest.py`) runs
  `axe-playwright-python` with default options, in the top frame only, and keeps the
  `violations` result type only. An archive's replay frame holds someone else's page and
  isn't scanned. A violation is identified by its rule id and its target (axe's CSS
  selector path), so the gate sees which elements fail, not just how many. Impact, help
  text and the element's `html` are not compared; `html` is not even stored, because it
  holds capture times and ids that change from run to run. `color-contrast` is gated like
  every other rule.
- **Where baselines live.** `functional_tests/accessibility_baselines/<browser>/<test file>/<test function>/<name>.json`,
  one file per engine, page and width, laid out like the visual baselines. Each file
  holds the `axe_version` and the violations (rule, target, impact, help) sorted by
  rule and target, so a diff shows exactly which violations came or went. A test can
  override the `a11y_baseline_dir` fixture to use another directory.
- **Updating baselines.** `--update-a11y-baselines` writes a baseline that is missing or
  differs, and those tests pass; a matching baseline is left untouched. Without the
  flag, a missing baseline fails; nothing is created silently. The flag is separate from
  `--update-snapshots` on purpose: re-blessing pixels (Bootstrap work does that often)
  must not also bless new violations. Review the baseline diff like any other change.
- **When a check fails.** The gate is a ratchet: it fails on a **new** violation and on
  a **fixed** one, so that a fix is recorded and can't quietly come back. The message
  lists the two kinds separately (impact, rule, help, target and axe's failure summary
  for new ones), names the baseline file and says to re-run with
  `--update-a11y-baselines`. The full axe response of the failed scan is saved as
  `<name>-axe-response.json` in the test's directory under `failed_test_files/`.
- **axe versions.** The axe-core version comes from the `axe-playwright-python` package,
  so upgrading that package can change results without any change to a page. The version
  is in every baseline, and the failure message says when it differs from the current
  one. Re-record the baselines in the same change as such an upgrade.
- **The archive pages' GUID.** `test_accessibility.py` overrides `complete_link_with_warc`
  so the archive link has a fixed GUID (`ARCHIVE_GUID`). The GUID appears in a selector
  (`a[href="/<GUID>?type=image"]`), and a random one would make the baseline differ on
  every run. Setting `guid` up front skips `Link.save()`'s `if not self.pk` block,
  including the `archive_timestamp` default, so the override sets that itself; a test
  checks that the link is otherwise the same as one with a generated GUID.
- **`settings-usage-plan` is a 403 page.** The test user isn't allowed to view the usage
  plan, so that page (here and in the screenshot capture) shows "Permission Denied", and
  its baseline records that page. This is pending a decision.
- **Running it.**

  ```
  d pytest functional_tests/test_accessibility.py --browser firefox --all
  d pytest functional_tests/test_accessibility.py --browser firefox --update-a11y-baselines
  ```

  Record each engine in its own session. Chromium and WebKit currently produce the same
  violations; Firefox reports a few more `color-contrast` nodes.

### Before/after screenshot capture

`functional_tests/capture_control_screenshots.py` takes full-page screenshots of 20
representative pages at the five supported widths. It produced the Bootstrap 3 "before"
set for the browser-testing plan and is re-run unchanged for the "after" set. Its name
deliberately does not match `test_*.py`, so ordinary `pytest` runs skip it; run it
explicitly, once per engine:

```
d bash -c 'PERMA_CONTROL_SCREENSHOT_DIR=/perma/perma_web/control_shots pytest functional_tests/capture_control_screenshots.py --browser firefox'
```

PNGs land in `<dir>/<browser>/<page>@<width>.png`. Move them out of `perma_web/`
afterwards; they are evidence, not committed baselines.

Before each shot the tool settles the page with the helper in
`functional_tests/page_settling.py`, which `assert_snapshot` uses too. That includes
forcing the page's lazy-loaded images to load. A full-page
screenshot doesn't scroll, so without that some below-the-fold `loading="lazy"` images
stay blank, and which ones varies by engine.

See [Common tasks and commands](#common-tasks-and-commands) for commands to run the tests.


### Linting with Flake8

All code must show zero warnings or errors when running `uv run flake8 .` in `perma_web/`.

Flake8 is configured in `perma_web/pyproject.toml`.

If you want to automatically run Flake8 before pushing your code, you can add something like the following to `.git/hooks/pre-commit` or `.git/hooks/pre-push`:

```sh
#!/bin/bash
docker compose exec -T web uv run flake8 .
exit $?
```

Be sure to mark the hook as executable: `chmod u+x .git/hooks/pre-commit` or `chmod u+x .git/hooks/pre-push`.

(You have to have started the containers with `docker compose up -d` for this to work.)


## Working with Celery

Celery does two things in Perma.cc: it runs the capture tasks and it runs scheduled jobs (to gather things nightly like statistics, just like cron might).

In development, it is sometimes easier to run everything synchronously, without the additional layer of complexity a Celery worker adds. By default, Perma runs Celery tasks synchronously. To run asynchronously, set `CELERY_TASK_ALWAYS_EAGER = False` in `settings.py`. `CELERY_TASK_ALWAYS_EAGER` must be `False` if you are specifically testing or setting up a new Celery/Django interaction or if you are working with LinkBatches (otherwise, subtle bugs may not surface).


## Working with Redis

In our production environment we use Redis as a cache for our thumbnail data.
The `perma-redis` service in `docker-compose.yml` (with the `redis_data` volume) is available for this. To use Redis in development the way production does, add the `caches` setting from `settings_prod.py` to your `settings.py` (see the comment above `perma-redis` in `docker-compose.yml` for the Redis URL to use).


## Running with DEBUG=False locally

If you are running Perma locally for development using the default `settings_dev.py`, [DEBUG](https://docs.djangoproject.com/en/stable/ref/settings/#std-setting-DEBUG) is set to `True`. This is, in general, a big help, because Django displays a detailed error page any time your code raises an exception. However, it makes it impossible to test your app's error handling, to see your custom 404 or 500 pages, etc.

To run with `DEBUG=False` locally, first stop the web server if it is running. Set `DEBUG=False` in `settings.py` (or change `settings_dev.py`). Then run `d ./manage.py collectstatic`, which creates `./services/django/static_assets` (necessary for the CSS and other static assets to be served properly). Then run `d invoke run` as usual to start the web server.

__NB__: With `DEBUG=False`, the server will not automatically restart each time you save changes.

__NB__: If you make changes to static files, like CSS, while running with `DEBUG=False`, you must rerun `d ./manage.py collectstatic` and restart the server to see your changes.

## Perma Payments

Aspects of Perma's paid subscription service are handled by the companion application, [Perma Payments](https://github.com/harvard-lil/perma-payments-stripe).

For the most fruitful experimentation, configure Perma to interact with a locally-running instance of Perma Payments that is itself wired up to a Stripe sandbox. Head over to the Perma Payments repo for detailed installation instructions.

## Scoop

Perma's web archives are produced using [Scoop](https://github.com/harvard-lil/scoop): Perma capture requests call out to the [Scoop API](https://github.com/harvard-lil/perma-scoop-api/), which captures the requested website and returns a WARC/WACZ to Perma.

By default, Perma's `docker-compose.yml` file will spin up a local Scoop API for you to experiment with.

### Working with both repositories simultaneously

You may also decide to run both services by running `docker compose` in both repositories simultaneously, with a tweaked Perma network config.

First, head over to the [`Scoop API` repo](https://github.com/harvard-lil/perma-scoop-api/) for instructions on how to spin that up.

Once it's running, spin up Perma... but with a slightly different command than usual, so that it doesn't try to create its own Scoop API, but instead uses the already-running one:

```
docker compose -f docker-compose.yml up -d
```

Then, run Perma's dev server as usual:

```
docker compose exec web invoke run
```

When you are finished, take down the Perma containers by running:

```
docker compose -f docker-compose.yml down
```

Don't worry if you get the following error:

`ERROR: error while removing network: network perma-scoop-api_default id 1902203ed2ca5dee5b57462201db417638317baef142e112173ee300461eb527 has active endpoints`

The Scoop API is still running: the network is maintained until both projects are down. Head back over to the Scoop API repo and run `docker compose down` there... and you're done.

## Working with Superset

Superset is a data visualization tool that connects to the Perma database and allows users to create saved SQL queries, datasets, charts, and dashboards. To experiment with the service, run the following commands to stop the running Docker containers and build the service image.

```
docker compose down
docker compose up -d --build
```

Navigate to `http://localhost:8088/` and log in to the service using the credentials specified in `docker-compose.override.yml`. Once logged in, the existing objects should be imported into the local playground.

When you are done with local development, export the dashboards using the Bulk Select Dashboards button, and place the downloaded zip file at `services/docker/superset/dashboard_export.zip`.


Filecheck
---------

Compose builds Filecheck's `dev` target locally from its `main` branch.
`pull_policy: build` checks build inputs on every `docker compose up`, reusing
cached layers when unchanged; no `--build` flag is needed.
It shares the Dockerfile runtime used by Filecheck's `main` build, with local
reload support and test tools. No private registry login is needed for Filecheck.
Perma calls `http://filecheck:8080/scan/` inside Compose; the host endpoint remains
`http://127.0.0.1:8888/scan/`. Initial startup downloads ClamAV signatures, which
are cached in the `filecheck_clamav_data` volume for later restarts and rebuilds.

To build changes from a sibling Filecheck checkout:

```sh
FILECHECK_BUILD_CONTEXT=../perma-filecheck docker compose up -d filecheck
```

Run the same command after editing that checkout to rebuild. For automatic
reload, add a Compose
override mounting its `main.py` at `/app/main.py:ro`. Ordinary Perma work needs
no separate checkout. Each `up` follows the latest Filecheck `main`; use `FILECHECK_BUILD_CONTEXT`
with a Git URL ending in `#<commit>` to reproduce a specific version. Local
builds do not promote or deploy ECS images.
