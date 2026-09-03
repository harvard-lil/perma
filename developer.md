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
  - [Linting with Flake8](#linting-with-flake8)
- [Working with Celery](#working-with-celery)
- [Working with Redis](#working-with-redis)
- [Running with DEBUG=False locally](#running-with-debugfalse-locally)
- [Perma Payments](#perma-payments)
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

Using `pull` first after fetching new code will avoid rebuilding images locally:

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
[test users (the `linkuser` objects)](https://github.com/harvard-lil/perma/blob/develop/perma_web/fixtures/users.json#L167). All test users have a password of "pass".

The server will automatically reload any time you make a change to the `perma_web` directory: just refresh the page to see your changes.

Press `CONTROL-C` to stop the server.

### Run the tests

```
d pytest
d npm test
```

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

The `prod` branch contains production code (likely what is running at [Perma.cc](https://perma.cc/)) while the `develop` branch contains the group's working version. We follow [Vincent Driessen's approach](https://nvie.com/posts/a-successful-git-branching-model/).

Fork our repo, then make a feature branch on your fork. Issue a pull request to merge your feature branch into Perma's develop branch when your code is ready.

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

Compiled bundles generated by Webpack will be added to the Git repository by CI if you omit them.


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

Perma uses **Bootstrap 5.3** (`bootstrap`, with `@popperjs/core` as its
declared peer), compiled from source rather than consumed as a prebuilt CSS
file. Three things about the setup are non-obvious:

**Bootstrap 3's grid tiers are deliberately restored.** Bootstrap 5 ships
`sm`/`md`/`lg` at 576/768/992px; `_bootstrap-custom.scss` overrides
`$grid-breakpoints` and `$container-max-widths` back to 768/992/1200px so
`.col-sm-*` keeps meaning what Perma's markup has always meant by it. Those
overrides **must** precede `@import "~bootstrap/scss/variables"`, which
declares the defaults with `!default`.

**Only the components Perma uses are imported.** `_bootstrap-custom.scss`
(main site) and `_bootstrap-custom-archive.scss` (archive playback pages) each
import an explicit list of Bootstrap partials. Accordion, badge, breadcrumb,
button-group, card, carousel, list-group, offcanvas, placeholders, popover,
spinners, toasts and tooltip are all omitted because nothing uses them; adding
markup that needs one means adding its `@import` too. The archive entry also
omits `transitions`, which is intentional and pinned by a test — the archive
pages have never animated their collapse panels.

**`_bootstrap-mod.scss` carries shims for classes Bootstrap 5 dropped.**
`.hidden`, `.caret`, `.dl-horizontal` and `.btn-default` are reproduced from
Bootstrap 3's compiled output so that markup and inline JavaScript still
depending on them keeps working. Each has a comment saying who depends on it.
Prefer migrating a caller to a Bootstrap 5 equivalent over adding a new shim.

Bootstrap's JavaScript is pulled in as individual ES modules in
`static/js/global.js` (`bootstrap/js/dist/dropdown`, `collapse`, `tab`), which
register their own `data-bs-*` data-API. Note that these dispatch **native**
events, not jQuery ones: a listener for `shown.bs.collapse` must be registered
with `addEventListener`, because jQuery would parse that name as event `shown`
in namespaces `bs` and `collapse` and never fire.

#### Sass

Perma's own partials use the Sass module system (`@use` / `@forward`), with
`_perma-imports.scss` as the aggregator. Two constraints are worth knowing
before refactoring:

- **`@extend` cannot cross a `@use` module boundary.** Perma `@extend`s
  Bootstrap classes such as `.container`, so the entry stylesheets must reach
  Bootstrap through `@import`, not `@use`. Switching them compiles cleanly and
  silently changes the generated rules.
- **`sassOptions.quietDeps` is still set** in `webpack.config.js`. Bootstrap
  5.3's own SCSS is written with `@import` throughout, so without the flag the
  build reports far more deprecations from inside `node_modules` than from
  Perma's code. `quietDeps` silences dependency files only, so Perma-owned
  deprecations still surface and should still be fixed. The flag can go when
  Bootstrap moves to `@use`.

Use `color.adjust($c, $lightness: $n)` to replace a deprecated `lighten()`.
Sass's own deprecation message suggests `color.scale()`, which computes a
different colour.

#### jQuery and the remaining legacy libraries

Perma is on **jQuery 4**. Nothing imports it by name: `webpack.ProvidePlugin`
injects `$`, `jQuery`, and `window.jQuery` into every module that references
them.

**That injection must name the default export** — `jQuery: ["jquery", "default"]`,
not `jQuery: "jquery"`. jQuery 4 added an `exports` map to its package, so
webpack now resolves the injection to the ESM build, and a bare module name
provides the *module namespace object* rather than jQuery itself. The symptom is
`$.ajaxSetup is not a function` thrown from `global.js` on every page, with a
green build and no warning. jsTree's own CommonJS `require("jquery")` resolves
through jQuery's `bundler-require-wrapper` to the same single instance, so both
entry points share one jQuery.

**jQuery 4 also throws when imported without a DOM.** jQuery 3 exported a
factory in that case; jQuery 4 does not, so `import "jquery"` in a Node-environment
test fails at module load with `jQuery requires a window with a document`. That
is why `spec/vitest.setup.js` imports it only when `document` exists — the
Webpack build contract runs under `@vitest-environment node`.

**`package.json` carries an `overrides` entry** forcing `jstree`'s `jquery`
peer to the top-level version. jsTree 3.3.x declares `jquery: ^3.5.0`, which
excludes jQuery 4. Without the override npm does not fail — it silently nests a
second jQuery 3 under `node_modules/jstree`, and jsTree then registers
`$.fn.jstree` on a different instance from the one the application holds. The
override is safe because jsTree's source uses none of the APIs jQuery 4 removed;
recheck that if jsTree is upgraded. After any jQuery-adjacent change, confirm
`npm ls jquery` reports a single deduped instance.

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

When changing UI markup, expect to keep these passing unmodified. If an
assertion has to change, that is a product-visible behavior change and should
be treated as one.

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
