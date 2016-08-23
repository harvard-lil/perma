Installing Perma
=====

## Initial Setup

Perma is a Python application built on the [Django](https://www.djangoproject.com/) web framework.

To get up and running, read through the [Quick Start](#quick-start) or
[Manual Install](#install) instructions, but first you'll need add the
following domains to your hosts file:

    127.0.0.1 perma.dev api.perma.dev dashboard.perma.dev user-content.perma.dev

For additional information on modifying your hosts file,
[try this help doc](http://www.rackspace.com/knowledge_center/article/how-do-i-modify-my-hosts-file).

## Quick Start

If you are running Perma locally for development, we recommend using
our pre-built [Vagrant](http://docs.vagrantup.com/v2/getting-started/)
virtual machine. This will take more disk space (~1.4GB), but will let
you jump into coding instead of trying to get all the services running
on your machine.

First you'll need some dependencies:

* [Git](http://git-scm.com/downloads)
* [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
* [Vagrant](http://www.vagrantup.com/downloads.html)

Then check out the code:

    $ git clone https://github.com/harvard-lil/perma.git
    $ cd perma

Start up the vagrant virtual machine in the background:

    $ vagrant up

The first time this runs it will have to download the ~1.4GB disk image.

Connect to the virtual machine:

    $ vagrant ssh
    ...
    (perma)vagrant@perma:/vagrant/perma_web$

You are now logged into the VM. The prompt you see means you have the
`(perma)` virtualenv activated, you are logged in as the user
`vagrant`, you are using the `perma` VM, and you are in the
`/vagrant/perma_web` folder.

`/vagrant` is a shared folder in the guest machine that maps to the
`perma` repo you just checked out on your host machine, so any changes
you make on your local computer will appear inside `/vagrant` and vice
versa.

Now you're in the Django project folder and can develop like
normal. Although the requirements are already installed in the image,
you may have to update them if there have been subsequent changes:

    (perma)vagrant@perma:/vagrant/perma_web$ pip install -r requirements.txt

The database has also been installed, but if you drop it and want to
start over, run this, which will call `syncdb`, apply migrations, and
load fixtures:

    (perma)vagrant@perma:/vagrant/perma_web$ fab dev.init_db

Then you can run the server:

    (perma)vagrant@perma:/vagrant/perma_web$ fab run
    [localhost] local: python manage.py runserver 0.0.0.0:8000
    ...
    Starting development server at http://0.0.0.0:8000/
    Quit the server with CONTROL-C.

That's it! You should now be able to load Perma in your browser at `http://perma.dev:8000/`. The celery workers should already be running, but if you need to stop or start them, try

    (perma)vagrant@perma:/vagrant/perma_web$ sudo systemctl stop celery
    (perma)vagrant@perma:/vagrant/perma_web$ sudo systemctl start celery

You can do the same thing for `celerybeat` and `celery_background`, but these are not started by default.

Finally, you can run the tests like this:

    (perma)vagrant@perma:/vagrant/perma_web$ fab test

(You may have to answer "yes" to two questions about deleting the test database the first time you run the tests.)

## Install

If you want to set up a server from scratch instead of using our VM, here's how to do it.

### Python, Django, and modules

To develop Perma, install Python and the Python package manager, `pip`.

The required modules are found in `requirements.txt`. Install them using `pip`:

    $ pip install -r requirements.txt

If you're running OS X Mountain Lion, you may need to add the MySQL
binaries to your PATH:

    $ export PATH=$PATH:/usr/local/mysql/bin

If you're running Ubuntu or Linux distro you might need to install mysql_config using:

    $ apt-get install libmysqlclient-dev

Sometimes LXML can be a little difficult to install. Using static dependencies can help (especially if you're using OS X).

    $ STATIC_DEPS=true pip install lxml


### Database installation

You'll need a Django friendly database. SQLite is not currently supported. We recommend MySQL.

If you want to use MySQL, something like the following can be used to create a new user and a new database:

    mysql -u root -psomepasshere
    mysql> create database perma character set utf8; grant all on perma.* to perma@'localhost' identified by 'perma';
    mysql> create database perma_cdxline character set utf8; grant all on perma_cdxline.* to perma@'localhost' identified by 'perma';
    mysql -u perma -pperma
    mysql> show databases;

### Settings

Perma settings are held in the settings module file. Copy the example and fill in as you see fit.

    cd settings; cp ./settings.example.py ./settings.py

Set a `SECRET_KEY` in `settings.py`.

A lot of the settings you need won't change much, so we keep them in a module and load them in. You'll probably want settings_dev, so uncomment that line in `settings.py`:

    # Choose one of these:
    from settings_dev import *
    # from settings_prod import *

### Create your tables and fire up Django

You should have the pieces in place. Let's apply migrations:

    $ python manage.py migrate
    $ python manage.py migrate --database=perma-cdxline

For deployments, you should set an index on the urlkey field in the perma_cdxline table (this will make cdxline lookups faster):

    mysql -u perma -pperma perma_cdxline
    mysql> alter table perma_cdxline add key perma_cdxline_urlkey (urlkey(255));

If you want to play with the admin views, load the user data fixtures:

    $ python manage.py loaddata fixtures/users.json fixtures/folders.json

The password for all test users is "pass".

### Celery and RabbitMQ

Perma manages the indexing workload by passing off the indexing tasks to workers. Celery manages the messages and RabbitMQ acts as the broker.

RabbitMQ can be installed on Ubuntu with:

    $ sudo apt-get install rabbitmq-server

You should have already installed the Celery requirements (they were in the requirements.txt). You'll need to install [RabbitMQ](http://www.rabbitmq.com/).

Once you've installed RabbitMQ, start it:

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

We use ImageMagick (through [Wand](http://docs.wand-py.org/)) to create thumbnails from our PDFs and other images. Something like this should get you started on Redhat

    yum install ImageMagick-devel

If you're on OS X you might need to adjust an [environment variable](http://docs.wand-py.org/en/0.3.8/guide/install.html#install-imagemagick-on-mac):

	export MAGICK_HOME=/opt/local


### Run the server

Toss in a WSGI config and wire it to your webserver, or use the built-in Django webserver and you should be ready to roll:

    $ python manage.py runserver

### Developer notes

[The developer doc](https://github.com/harvard-lil/perma/blob/develop/developer.md) has lots of tips and tricks. Be sure to give it a look-see.
