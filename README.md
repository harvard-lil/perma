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
	mysql> create database linky character set utf8; grant all on linky.* to linky@'%' identified by 'linky';
	mysql -u linky -plinky linky

### Settings

Perma uses two settings files. You'll find example files in the codebase. Copy these, removing the '.example' characters and edit.

    cp ./settings.example.py ./settings.py
    cp ./local_settings.py ./local_settings.py

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

### Create your tables and fire up Django

You should have the pieces in place. Let's create the tables in your database:

    $ python manage.py syncdb

If you want to play with the admin views, load the user, group, and registrar data fixture:

    $ python manage.py loaddata test/fixtures/usersandgroups.json 

Toss in a wsgi config and wire it to your webserver, or use the built-in Django webserver and you should be ready to roll:

    $ python manage.py runserver
