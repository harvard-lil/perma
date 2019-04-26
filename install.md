Installing Perma
================

Perma is a Python application built on the [Django](https://www.djangoproject.com/)
web framework.

Perma has a lot of moving pieces. We recommend using [Docker](https://www.docker.com/what-docker) for local development. If you are new to Docker, it may take some
time before you are comfortable with its vocabulary and commands, but it allows you
to jump right into coding instead of spending a lot of time getting all the services
running on your machine.

If you prefer to install Perma locally, see our [legacy installation instructions](#manual-installation-legacy).

For advice about production deployments, [send us a note](mailto:info@perma.cc)!

Be sure to check out [the developer documentation](./developer.md)
for a list of command commands and other tips and tricks for working with Perma.


Dependencies
------------

* [Git](http://git-scm.com/downloads)
* [Docker](https://docs.docker.com/install/)


Hosts
-----

Perma serves content at several hosts. To ensure that URLs resolve correctly,
add the following domains to your computer's hosts file:

    127.0.0.1 perma.test api.perma.test perma-archives.test

For additional information on modifying your hosts file,
[try this help doc](http://www.rackspace.com/knowledge_center/article/how-do-i-modify-my-hosts-file).


Shortcuts
---------

Docker commands can be lengthy. To cut down on keystrokes, we recommend
adding the following to your `.bash_profile`.

```
alias d="docker-compose exec web pipenv run"
```


Installation
------------

Then check out the code:

    $ git clone https://github.com/harvard-lil/perma.git
    $ cd perma

Start up the Docker containers in the background:

    $ docker-compose up -d

The first time this runs, it will build the 1.4GB Docker image, which
may take several minutes. (After the first time, it should only take
1-3 seconds.)

Finally, initialize the databases:

    $ bash init_perma.sh
    $ bash init_wr.sh

You should now have a working installation of Perma! See [common commands](./developer.md#common-tasks-and-commands) to explore what you can do, like [running
the application](./developer.md#run-perma) and [running the tests](/developer.md#run-all-the-tests).

When you are finished, spin down Docker containers by running:

    $ docker-compose down


Manual Installation (Legacy)
----------------------------

If you want to set up a server from scratch instead of using Docker, this should
get you started.


### Python, Django, and other Python modules

To run Perma, you will need [Python 3.5](https://www.python.org/downloads/release/python-350/) and the Python package manager [Pipenv](https://docs.pipenv.org/).

The [Hitchhiker's Guide](http://docs.python-guide.org/en/latest/starting/installation/)
has instructions for installing python on most systems; take care to install python 3.5 rather than 3.6, 3.7, etc. You may prefer to use [pyenv](https://github.com/pyenv/pyenv),
a fantastic tool allowing you to install and run multiple versions of python on
the same computer.

The required modules are found in `Pipfile` and `Pipfile.lock`. Install them using:

    $ pipenv --python 3.5 install --ignore-pipfile

During installation, you may find that your system lacks certain dependencies,
resulting in error messages and a failed build. Install any system packages required,
and run pipenv again, repeating until installation completes without errors.

Our Dockerfile contains a list of dependencies required on Debian Stretch.

You may need to install MySQL first, in a manner appropriate for your platform.

If you're running OS X, you may need to add the MySQL binaries to your PATH:

    $ export PATH=$PATH:/usr/local/mysql/bin

If you're running Ubuntu or another Linux distro, you might need to install mysql_config using:

    $ apt-get install libmysqlclient-dev

Sometimes LXML can be a little difficult to install. Using static dependencies can help (especially if you're using OS X).

    $ STATIC_DEPS=true pipenv install lxml


### Database installation

Perma requires two databases, one to keep track of the URLs in its archives
(CDXLines) and one for everything else.

Something like the following can be used to create a new user and new databases:

    $ mysql -u root -psomepasshere
    mysql> create database perma character set utf8; grant all on perma.* to perma@'localhost' identified by 'perma';
    mysql> create database perma_cdxline character set utf8; grant all on perma_cdxline.* to perma@'localhost' identified by 'perma';
    mysql -u perma -p perma
    mysql> show databases;


### Create your tables

    $ pipenv run python manage.py migrate
    $ pipenv run python manage.py migrate --database=perma-cdxline

For deployments, you should set an index on the urlkey field in the perma_cdxline table (this will make cdxline lookups faster):

    $ mysql -u perma -pperma perma_cdxline
    mysql> alter table perma_cdxline add key perma_cdxline_urlkey (urlkey(255));

If you like, load the test data fixtures:

    $ pipenv run python manage.py loaddata fixtures/sites.json fixtures/users.json fixtures/folders.json

The password for all test users is "pass".


### Celery and RabbitMQ

Perma passes off capture tasks to workers for improved performance.
Celery manages the queue and RabbitMQ acts as the message broker.

Celery and its dependencies are installed via Pipenv along with Perma's
other python dependencies. You'll need to manually install [RabbitMQ](http://www.rabbitmq.com/).

Once you've installed RabbitMQ, start it with something similar to:

    $ cd rabbitmq_server-3.1.3/sbin; ./rabbitmq-server start

(You'll probably want to start RabbitMQ as a service on your prod instance)

You'll need to start Celery. If you're working in a development environment, do something like:

    $ celery -A perma worker --loglevel=info

If you're setting up a production machine, be sure to [start Celery as a daemon](http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html#daemonizing).


### PhantomJS

We use PhantomJS to generate our archives. [Install PhantomJS](http://phantomjs.org/download.html), and then make sure it's in your path:

    $ phantomjs
    phantomjs>

(If you don't want to put PhantomJS in your path, you can put it in perma_web/lib/ and set PHANTOMJS_BINARY as demonstrated in settings.py.example.)


### ImageMagick and Wand

We use ImageMagick (through [Wand](http://docs.wand-py.org/)) to create thumbnails from our PDFs and other images. Something like this should get you started on Debian:

    apt-get install imagemagick

If you're on OS X you might need to adjust an [environment variable](http://docs.wand-py.org/en/0.3.8/guide/install.html#install-imagemagick-on-mac):

    export MAGICK_HOME=/opt/local


### Node and npm

Frontend assets are compiled with [Webpack](https://webpack.js.org/), which depends on Node and npm.

First [install Node and npm](https://nodejs.org/en/download/).

Then install the npm packages for perma:

    $ npm install


### Hosts

[Configure your hosts](#hosts) as per above.


### Settings

Perma settings are held in the settings module file. See `perma_web > perma > settings > README.md` for more details.


### Run the server

Toss in a WSGI config and wire it to your webserver and you should be ready to roll.

Or, use Fabric to spin up Django's development server and launch Webpack (which will automatically regenerate assets on changes to existing js and scss files):

    $ pipenv run fab run

With the development server running, Perma should be available at http://perma.test:8000
