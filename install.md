Installing Perma
=====

## Install

Perma is a Python application running in Django.

### Python, Django, and modules

To develop Perma, install Python and the Python package manager, pip.

The required modules are found in requirements.txt. Install them using pip:

    $ pip install -r requirements.txt

Perma requires are at least one module that cannot be installed with pip. 
    
    warcprox -  https://github.com/internetarchive/warcprox

If you're running OS X Mountain Lion, you may need to add the MySQL binaries 
to your PATH:

    $ export PATH=$PATH:/usr/local/mysql/bin

If you're running Ubuntu or Linux distro you might need to install mysql_config using:
    $ apt-get install libmysqlclient-dev

### MySQL

You'll need a Django friendly database. If you want to use MySQL, something like the following can be used to create a new user and a new database:

	mysql -u root -psomepasshere
	mysql> create database perma character set utf8; grant all on perma.* to perma@'localhost' identified by 'perma';
	mysql -u perma -pperma perma

### Settings

Perma settings are held in the settings module file. Copy the example and fill in as you see fit.

    cd settings; cp ./settings.example.py ./settings.py

A lot of the settings you need won't change much, so we keep them in a module and load them in. You'll probably want settings_dev, so uncomment that line:

    # Choose one of these:
    from settings_dev import *
    # from settings_prod import *

### Celery and RabbitMQ

Perma manages the indexing workload by passing off the indexing tasks to workers. Celery manages the messages and RabbitMQ acts as the broker.

RabbitMQ can be installed on Ubuntu with:
    $ sudo apt-get install rabbitmq-server`

You should have already installed the Celery requirements (they were in the requirements.txt). You'll need to install [RabbitMQ](http://www.rabbitmq.com/).



Once you've installed RabbitMQ, start it:

    $ cd rabbitmq_server-3.1.3/sbin; ./rabbitmq-server start

(You'll probably want to start RabbitMQ as a service on your prod instance)


You'll need to start Celery. If you're working a development env, do something like:

    $ python manage.py celery worker --loglevel=info

If you're setting up a production machine, be sure to [start Celery as a daemon](http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html#daemonizing).


### PhantomJS

We use PhantomJS to generate our images. Download [PhantomJS](http://phantomjs.org/) and place the binary in your lib directory. Your lib directory might look something like this:

    $ ls lib
    __init__.py phantomjs rasterize.js

### warcprox

We use warcprox to make WARC (Web ARChive) files. We have tested with version 1.1.

    $ pip install warcprox


### Create your tables and fire up Django

You should have the pieces in place. Let's create the tables in your database using the syncdb command.:

    $ python manage.py syncdb --noinput

You'll need to convert your local Perma app to use South,

    $ python manage.py convert_to_south myapp

See where you are with your migrations,
    $ python manage.py migrate --list

If you haven't migrated to the latest version, apply migrate
    $ python manage.py migrate perma

If you want to play with the admin views, load the user and group data fixtures:

    $ python manage.py loaddata fixtures/users.json fixtures/groups.json

The password for all test users is "pass".

Toss in a wsgi config and wire it to your webserver, or use the built-in Django webserver and you should be ready to roll:

    $ python manage.py runserver


### Developer notes

[The developer doc](https://github.com/harvard-lil/perma/blob/develop/developer.md) has lots of tips and tricks. Be sure to give it a look-see.