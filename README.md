Perma - indelible links
=====

## Install

Perma is a Python application running in Django.

### Python, Django, and modules

To develop Perma, install Python and the Python package manager, pip.

The required modules are found in requirements.txt. Install them using pip:

    $ pip install -r requirements.txt

If you're running OS X Mountain Lion, you may need to add the MySQL binaries 
to your PATH:

    $ export PATH=$PATH:/usr/local/mysql/bin

### MySQL

You'll need a Django friendly database. If you want to use MySQL, something like the following can be used to create a new user and a new database:

	mysql -u root -psomepasshere
	mysql> create database perma character set utf8; grant all on perma.* to perma@'%' identified by 'perma';
	mysql -u perma -pperma perma

### Settings

Perma settings are held in the settings.py file. Copy the example and fill in as you see fit.

    cp ./settings.example.py ./settings.py

### Celery and RabbitMQ

Perma manages the indexing workload by passing off the indexing tasks to workers. Celery manages the messages and RabbitMQ acts as the broker.

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

### Wget

We use [GNU Wget](http://www.gnu.org/software/wget/) to download the source -- the markup, CSS, JS, images, and other assets. We've tested with version 1.12. If you're on a mac, something like this should get you close:

    # port install wget

### Create your tables and fire up Django

You should have the pieces in place. Let's create the tables in your database using the syncdb command.:

    $ python manage.py syncdb --noinput

You may need to apply South migrations (e.g., for `djcelery`):

    $ python manage.py migrate

If you want to play with the admin views, load the user and group data fixtures:

    $ python manage.py loaddata fixtures/users.json fixtures/groups.json

The password for all test users is "pass".

Toss in a wsgi config and wire it to your webserver, or use the built-in Django webserver and you should be ready to roll:

    $ python manage.py runserver
