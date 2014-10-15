Perma - developer notes
=====

This document does not cover installing Perma.cc. You should use the install doc for that.

There are a bunch of moving pieces in Perma.cc. This document provides some notes on common dances you might have to perform.


### Git and GitHub

We use git to track code changes and use [GitHub](https://github.com/harvard-lil/perma) to host the code publicly.

The Master branch always contains production code (probably the thing currently running at [Perma.cc](http://perma.cc)) while the develop branch contains the group's working version. We follow this [Vincent Driessen's approach](http://nvie.com/posts/a-successful-git-branching-model/)

Leverage [feature branches](http://nvie.com/posts/a-successful-git-branching-model/) in your local development flow. Merge your code back into the develop branch and push to GitHub often. Small, quick commits avoid nightmare merge problems.


### Logs

If you are using Vagrant, all of your logs will end up in /vagrant/services/logs. As a convenience, you can tail -f all of them with `fab logs`.


### Managing static files and user-generated files

We use Django's built-in functions to manage static assets (Javascript/CSS/etc.) and user-generated media (our link archives).

To make sure everything works smoothly in various environments (local dev, Linux servers, and cloud services),
be sure to use the following settings when referring to disk locations and URLs in your code and templates:

* STATIC_ROOT: Absolute path to static assets (e.g. '/tmp/perma/static/')
* STATIC_URL: URL to retrieve static assets (e.g. '/static/')
* MEDIA_ROOT: Absolute path to user-generated assets (e.g. '/tmp/perma/generated/')
* MEDIA_URL: URL to retrieve user-generated assets (e.g. '/media/')

The \_ROOT settings may have different meanings depending on the storage backend. For example,
if DEFAULT_FILE_STORAGE is set to use the Amazon S3 storage backend,
then MEDIA_ROOT would just be '/generated/' and would be relative to the root of the S3 bucket.

In templates, use STATIC_URL and MEDIA_URL:

    <img src="{{ STATIC_URL }}img/header_image.jpg">

    <img src="{{ MEDIA_URL }}{{ asset.image_capture }}">

In code, use Django's default_storage to read and write user-generated files rather than accessing the filesystem directly:

    from django.core.files.storage import default_storage

    with default_storage.open('some/path', 'rb') as image_file:
        do_stuff_with_image_file(image_file)

Paths for default_storage are relative to MEDIA_ROOT.

Further reading:

* [Django docs for default_storage](https://docs.djangoproject.com/en/dev/topics/files/)
* [Django docs for serving static files](https://docs.djangoproject.com/en/dev/howto/static-files/)

### Using Sass to manage CSS

We use Compass to translate Sass to CSS. A command like the following is likely helpful when you're developing
    
    $ cd perma_web
    $ compass watch --sass-dir static/css/ --css-dir static/css


### Hosting fonts locally

We like to host our fonts locally. If you're liking a font from Google fonts and the licesning allows, check out[fontdump](https://pypi.python.org/pypi/fontdump/1.2.0)


###  Schema and data migrations using South

*** Before changing the schema or the data of your database, make a backup! ***

If you make a change to the Django model (models get mapped directly to relational database tables), you'll need to create a [South](http://south.aeracode.org/) migration. South migrations come in two flavors: schema migrations and data migrations.


#### Schema migrations and data migrations

Schema migrations are used when changing the model structure (adding, removing, editing fields) and data migrations are used when you need to ferry data between your schema changes (you renamed a field and need to move data from the old field name to the new field name).

The most straight forward data migration might be the addition of a new model or the addition of a field to a model. When you perform a straight forward change to the model, your South command might look like this

    $ ./manage.py schemamigration perma --auto

(Or use our shortcut, `fab south_out` ) This will create a migration file for you on disk, something like,

    $ cat perma_web/perma/migrations/0003_auto__add_vestingorg__add_field_linkuser_vesting_org.py

Even though you've changed your models file and created a migration (just a python file on disk), your database remains unchanged. You'll need to apply the migration to update your database,

    $ ./manage.py migrate perma

(Or use our shortcut, `fab south_in` ) Now, your database, your model, and your migration should all be at the same point. You can list your migrations using the list command,

    $ ./manage.py migrate --list

Data migrations follow the same flow, but add a step in the middle. See the [South docs](http://south.readthedocs.org/en/latest/tutorial/part3.html) for details on how to perform a data migration.


#### Track migrations in Git and get started

You should commit your migrations to your repository and push to GitHub.

    $ git add perma_web/perma/migrations/0003_auto__add_vestingorg__add_field_linkuser_vesting_org.py
    $ git commit -m "Added migration"


If you've just installed Perma.cc, you'll want to make sure to convert your app to a south-based app

	$ ./manage.py convert_to_south perma
	
If you've been developing Perma without using South, you might need to apply the first migration as a "fake" migration
	
    $ ./manage.py migrate perma 0001 --fake


### Testing and Test Coverage

If you add or change a feature, be sure to add a test for it in perma/tests/. Tests are run like this:

    $ fab test

You should always run the tests before committing code.

The `fab test` command also generates handy coverage information. You can access it with the `coverage` command.


#### Sauce Browser Tests

We also use Sauce Labs to do functional testing of the site in common browsers before deploying. If you have a Sauce account,
you can set SAUCE_USERNAME and SAUCE_ACCESS_KEY in settings.py, and then run our Sauce tests with
 
    $ fab test_sauce
    
By default `fab test_sauce` is pointed at 127.0.0.1:8000, which Sauce can't reach from outside, so you'll have to set
up a tunnel first by running

    $ fab sauce_tunnel
    
in the background or in another terminal window.

The Sauce tests live in services/sauce/run_tests.py. If you are developing new tests in that file, it may be more
convenient to change to that directory and run `python run_tests.py`, rather than the full-blown parallel testing
kicked off by `fab test_sauce`.


### Debugging email-related issues

If you're working on an email related task, the contents of emails should be dumped to the standard out courtesy of EMAIL_BACKEND in settings_dev.py.


### Mirroring

Perma uses a mirroring system in which one server handles logged-in users and content creation, and a set of mirrors help to serve archived content.
A load balancer routes traffic between them. The net effect is that http://users.perma.cc is served by one server,
while http://perma.cc may be served by any randomly selected mirror.

For development, we simulate Perma's network by running a simple load balancer on the local machine at \*.perma.dev:8000.
The load balancer routes requests to users.perma.dev:8000 to the main Django dev server running on port :8001,
and requests to perma.dev:8000 to a mirror Django dev server running on port :8002.

To set that up, first edit your hosts file (/etc/hosts or \system32\drivers\etc\hosts) to add the following line:

    127.0.0.1    *.perma.dev

(If you're using Vagrant, this should happen on your host machine. The rest happens in the guest machine.)

Install Twisted:

    pip install twisted
    
Launch the simple load balancer and two Django dev servers:

    python manage.py runmirror

You can edit the codebase normally and each server will incorporate your changes.

To see how the mirror emulation works, check out perma_web/mirroring/management/commands/runmirror.py


### Working with Celery

Celery does two things in Perma.cc. It runs the indexing tasks (the things that accept a url and generate an archive) and it runs the scheduled jobs (to gather things nightly like statistics. just like cron might).

In your development environment (if you are not using Vagrant, where the celery service should be running by default), you probably want to start a dev version of Celery like this:

    $ celery -A perma worker --loglevel=info -B

The -B option also starts the Beat server. The Beat server is the thing that runs the scheduled jobs. You don't need the -B if you don't want to run the nightly scheduled jobs.

If you make changes to a Perma.cc Celery task, you'll need to stop and start the Celery server.

If you want to run Celery as a daemon (like you might in prod), there is an example upstart script in services/celery/celery.conf.
This is the script that is used to run the daemon for Vagrant.

Once installed in /etc/init/, you can start and stop Celery as a service. Something like,

    $ sudo stop celery; sudo start celery 

Find more about daemonizing Celery in the [in the Celery docs](http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html#daemonizing).


### Working with RabbitMQ

RabbitMQ is the message broker. In Perma.cc's case, it accepts message from Celery, tosses them in a queue, and dolls them out to Celery worker tasks as needed.

If you've installed RabbitMQ through something like MacPorts (sudo port install), you can start RabbitMQ using something like, 

    $ sudo rabbitmq-server -detached

If you don't want to run RabbitMQ as a daemon (like you might in prod), create a something like /etc/init.d/rabbitmq-server and place this in it,

	#!/bin/sh
	#
	# rabbitmq-server RabbitMQ broker
	#
	# chkconfig: - 80 05
	# description: Enable AMQP service provided by RabbitMQ
	#

	### BEGIN INIT INFO
	# Provides:          rabbitmq-server
	# Required-Start:    $remote_fs $network
	# Required-Stop:     $remote_fs $network
	# Description:       RabbitMQ broker
	# Short-Description: Enable AMQP service provided by RabbitMQ broker
	### END INIT INFO

	# Source function library.
	. /etc/init.d/functions

	PATH=/sbin:/usr/sbin:/bin:/usr/bin
	NAME=rabbitmq-server
	DAEMON=/usr/sbin/${NAME}
	CONTROL=/usr/sbin/rabbitmqctl
	DESC=rabbitmq-server
	USER=rabbitmq
	ROTATE_SUFFIX=
	INIT_LOG_DIR=/var/log/rabbitmq
	PID_FILE=/var/run/rabbitmq/pid

	START_PROG="daemon"
	LOCK_FILE=/var/lock/subsys/$NAME

	test -x $DAEMON || exit 0
	test -x $CONTROL || exit 0

	RETVAL=0
	set -e

	[ -f /etc/default/${NAME} ] && . /etc/default/${NAME}

	ensure_pid_dir () {
	    PID_DIR=`dirname ${PID_FILE}`
	    if [ ! -d ${PID_DIR} ] ; then
	        mkdir -p ${PID_DIR}
	        chown -R ${USER}:${USER} ${PID_DIR}
	        chmod 755 ${PID_DIR}
	    fi
	}

	remove_pid () {
	    rm -f ${PID_FILE}
	    rmdir `dirname ${PID_FILE}` || :
	}

	start_rabbitmq () {
	    status_rabbitmq quiet
	    if [ $RETVAL = 0 ] ; then
	        echo RabbitMQ is currently running
	    else
	        RETVAL=0
	        ensure_pid_dir
	        set +e
	        RABBITMQ_PID_FILE=$PID_FILE $START_PROG $DAEMON \
	            > "${INIT_LOG_DIR}/startup_log" \
	            2> "${INIT_LOG_DIR}/startup_err" \
	            0<&- &
	        $CONTROL wait $PID_FILE >/dev/null 2>&1
	        RETVAL=$?
	        set -e
	        case "$RETVAL" in
	            0)
	                echo SUCCESS
	                if [ -n "$LOCK_FILE" ] ; then
	                    touch $LOCK_FILE
	                fi
	                ;;
	            *)
	                remove_pid
	                echo FAILED - check ${INIT_LOG_DIR}/startup_\{log, _err\}
	                RETVAL=1
	                ;;
	        esac
	    fi
	}

	stop_rabbitmq () {
	    status_rabbitmq quiet
	    if [ $RETVAL = 0 ] ; then
	        set +e
	        $CONTROL stop ${PID_FILE} > ${INIT_LOG_DIR}/shutdown_log 2> ${INIT_LOG_DIR}/shutdown_err
	        RETVAL=$?
	        set -e
	        if [ $RETVAL = 0 ] ; then
	            remove_pid
	            if [ -n "$LOCK_FILE" ] ; then
	                rm -f $LOCK_FILE
	            fi
	        else
	            echo FAILED - check ${INIT_LOG_DIR}/shutdown_log, _err
	        fi
	    else
	        echo RabbitMQ is not running
	        RETVAL=0
	    fi
	}

	status_rabbitmq() {
	    set +e
	    if [ "$1" != "quiet" ] ; then
	        $CONTROL status 2>&1
	    else
	        $CONTROL status > /dev/null 2>&1
	    fi
	    if [ $? != 0 ] ; then
	        RETVAL=3
	    fi
	    set -e
	}

	rotate_logs_rabbitmq() {
	    set +e
	    $CONTROL rotate_logs ${ROTATE_SUFFIX}
	    if [ $? != 0 ] ; then
	        RETVAL=1
	    fi
	    set -e
	}

	restart_running_rabbitmq () {
	    status_rabbitmq quiet
	    if [ $RETVAL = 0 ] ; then
	        restart_rabbitmq
	    else
	        echo RabbitMQ is not runnning
	        RETVAL=0
	    fi
	}

	restart_rabbitmq() {
	    stop_rabbitmq
	    start_rabbitmq
	}

	case "$1" in
	    start)
	        echo -n "Starting $DESC: "
	        start_rabbitmq
	        echo "$NAME."
	        ;;
	    stop)
	        echo -n "Stopping $DESC: "
	        stop_rabbitmq
	        echo "$NAME."
	        ;;
	    status)
	        status_rabbitmq
	        ;;
	    rotate-logs)
	        echo -n "Rotating log files for $DESC: "
	        rotate_logs_rabbitmq
	        ;;
	    force-reload|reload|restart)
	        echo -n "Restarting $DESC: "
	        restart_rabbitmq
	        echo "$NAME."
	        ;;
	    try-restart)
	        echo -n "Restarting $DESC: "
	        restart_running_rabbitmq
	        echo "$NAME."
	        ;;
	    *)
	        echo "Usage: $0 {start|stop|status|rotate-logs|restart|condrestart|try-restart|reload|force-reload}" >&2
	        RETVAL=1
	        ;;
	esac

	exit $RETVAL


Now you can start and stop RabbitMQ as a service. Something like,

    $ sudo service rabbitmq-server stop; sudo service rabbitmq-server start;


### ImageMagick and Wand

If you're on OS X you should might need to do adjust and [environment variable](http://docs.wand-py.org/en/0.3.8/guide/install.html#install-imagemagick-on-mac)

	export MAGICK_HOME=/opt/local

### Other bits

Use [Handlebars](http://handlebarsjs.com/) when injecting markup using JavaScript.

Track issues using [GitHub Issues](https://github.com/harvard-lil/perma/issues?milestone=15&state=open).

Issue pull requests when you've got a commit ready.
