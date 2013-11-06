Perma - developer notes
=====

This document does not cover installing Perma.cc. You should use the install doc for that.

There are a bunch of moving pieces in Perma.cc. This document provides some notes on common dances you might have to perform.


### Git and GitHub

We use git to track code changes and use [GitHub](https://github.com/harvard-lil/perma) to host the code publicly.

The Master branch always contains production code (probably the thing currently running at [Perma.cc](http://perma.cc)) while the develop branch contains the group's working version. We follow this [Vincent Driessen's approach](http://nvie.com/posts/a-successful-git-branching-model/)

Leverage [feature branches](http://nvie.com/posts/a-successful-git-branching-model/) in your local development flow. Merge your code back into the develop branch and push to GitHub often. Small, quick commits avoid nightmare merge problems.


###  Schema and data migrations using South

*** Before changing the schema or the data of your database, make a backup! ***

If you make a change to the Django model (models get mapped directly to relational database tables), you'll need to create a [South](http://south.aeracode.org/) migration. South migrations come in two flavors: schema migrations and data migrations.


#### Schema migrations and data migrations

Schema migrations are used when changing the model structure (adding, removing, editing fields) and data migrations are used when you need to ferry data between your schema changes (you renamed a field and need to move data from the old field name to the new field name).

The most straight forward data migration might be the addition of a new model or the addition of a field to a model. When you perform a straight forward change to the model, your South command might look like this

    $ ./manage.py schemamigration perma --auto

This will create a migration file for you on disk, something like,

    $ cat perma_web/perma/migrations/0003_auto__add_vestingorg__add_field_linkuser_vesting_org.py

Even though you've changed your models file and created a migration (just a python file on disk), your database remains unchanged. You'll need to apply the migration to update your database,

    $ ./manage.py migrate perma

Now, your database, your model, and your migration should all be at the same point. You can list your migrations using the list command,

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


### Debugging email-related issues

If you're working on an email related task, launch your own dumb SMTP server to capture and dump the content.

Start the dumb SMTP server like this,

    $ python -m smtpd -n -c DebuggingServer localhost:1025

And update the EMAIL_HOST and EMAIL_PORT variables in your config (if you're using the settings_dev.py, you should already see these set)
	
Now, when you send an email through Django, you'll see the contents dumped to the standard out.


### Working with Celery

Celery does two things in Perma.cc. It runs the indexing tasks (the things that accept a url and generate an archive) and it runs the scheduled jobs (to gather things nightly like statistics. just like cron might).

In your development environment, you probably want to start a dev version of Celery using manage.py,

    $ python manage.py celery worker --loglevel=info -B

The -B option also starts the Beat server. The Beat server is the thing that runs the scheudled jobs. You don't need the -B if you don't want to run the nightly scheduled jobs.

If you make changes to a Perma.cc Celery task, you'll need to stop and start the Celery server.

If you don't want to run Celery as a daemon (like you might in prod), create a something like /etc/init.d/celery and place this in it,

	#!/bin/sh -e
	# ============================================
	#  celeryd - Starts the Celery worker daemon.
	# ============================================
	#
	# :Usage: /etc/init.d/celeryd {start|stop|force-reload|restart|try-restart|status}
	# :Configuration file: /etc/default/celeryd
	#
	# See http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html#generic-init-scripts


	### BEGIN INIT INFO
	# Provides:          celeryd
	# Required-Start:    $network $local_fs $remote_fs
	# Required-Stop:     $network $local_fs $remote_fs
	# Default-Start:     2 3 4 5
	# Default-Stop:      0 1 6
	# Short-Description: celery task worker daemon
	### END INIT INFO

	# some commands work asyncronously, so we'll wait this many seconds
	SLEEP_SECONDS=5

	DEFAULT_PID_FILE="/var/run/celery/%n.pid"
	DEFAULT_LOG_FILE="/var/log/celery/%n.log"
	DEFAULT_LOG_LEVEL="INFO"
	DEFAULT_NODES="celery"
	DEFAULT_CELERYD="-m celery.bin.celeryd_detach"

	CELERY_DEFAULTS=${CELERY_DEFAULTS:-"/etc/default/celery"}

	test -f "$CELERY_DEFAULTS" && . "$CELERY_DEFAULTS"

	# Set CELERY_CREATE_DIRS to always create log/pid dirs.
	CELERY_CREATE_DIRS=${CELERY_CREATE_DIRS:-0}
	CELERY_CREATE_RUNDIR=$CELERY_CREATE_DIRS
	CELERY_CREATE_LOGDIR=$CELERY_CREATE_DIRS
	if [ -z "$CELERYD_PID_FILE" ]; then
	    CELERYD_PID_FILE="$DEFAULT_PID_FILE"
	    CELERY_CREATE_RUNDIR=1
	fi
	if [ -z "$CELERYD_LOG_FILE" ]; then
	    CELERYD_LOG_FILE="$DEFAULT_LOG_FILE"
	    CELERY_CREATE_LOGDIR=1
	fi

	CELERYD_LOG_LEVEL=${CELERYD_LOG_LEVEL:-${CELERYD_LOGLEVEL:-$DEFAULT_LOG_LEVEL}}
	CELERYD_MULTI=${CELERYD_MULTI:-"celeryd-multi"}
	CELERYD=${CELERYD:-$DEFAULT_CELERYD}
	CELERYD_NODES=${CELERYD_NODES:-$DEFAULT_NODES}

	export CELERY_LOADER

	if [ -n "$2" ]; then
	    CELERYD_OPTS="$CELERYD_OPTS $2"
	fi

	CELERYD_LOG_DIR=`dirname $CELERYD_LOG_FILE`
	CELERYD_PID_DIR=`dirname $CELERYD_PID_FILE`

	# Extra start-stop-daemon options, like user/group.
	if [ -n "$CELERYD_USER" ]; then
	    DAEMON_OPTS="$DAEMON_OPTS --uid=$CELERYD_USER"
	fi
	if [ -n "$CELERYD_GROUP" ]; then
	    DAEMON_OPTS="$DAEMON_OPTS --gid=$CELERYD_GROUP"
	fi

	if [ -n "$CELERYD_CHDIR" ]; then
	    DAEMON_OPTS="$DAEMON_OPTS --workdir=$CELERYD_CHDIR"
	fi


	check_dev_null() {
	    if [ ! -c /dev/null ]; then
	        echo "/dev/null is not a character device!"
	        exit 75  # EX_TEMPFAIL
	    fi
	}


	maybe_die() {
	    if [ $? -ne 0 ]; then
	        echo "Exiting: $* (errno $?)"
	        exit 77  # EX_NOPERM
	    fi
	}

	create_default_dir() {
	    if [ ! -d "$1" ]; then
	        echo "- Creating default directory: '$1'"
	        mkdir -p "$1"
	        maybe_die "Couldn't create directory $1"
	        echo "- Changing permissions of '$1' to 02755"
	        chmod 02755 "$1"
	        maybe_die "Couldn't change permissions for $1"
	        if [ -n "$CELERYD_USER" ]; then
	            echo "- Changing owner of '$1' to '$CELERYD_USER'"
	            chown "$CELERYD_USER" "$1"
	            maybe_die "Couldn't change owner of $1"
	        fi
	        if [ -n "$CELERYD_GROUP" ]; then
	            echo "- Changing group of '$1' to '$CELERYD_GROUP'"
	            chgrp "$CELERYD_GROUP" "$1"
	            maybe_die "Couldn't change group of $1"
	        fi
	    fi
	}


	check_paths() {
	    if [ $CELERY_CREATE_LOGDIR -eq 1 ]; then
	        create_default_dir "$CELERYD_LOG_DIR"
	    fi
	    if [ $CELERY_CREATE_RUNDIR -eq 1 ]; then
	        create_default_dir "$CELERYD_PID_DIR"
	    fi
	}

	create_paths() {
	    create_default_dir "$CELERYD_LOG_DIR"
	    create_default_dir "$CELERYD_PID_DIR"
	}

	export PATH="${PATH:+$PATH:}/usr/sbin:/sbin"


	_get_pid_files() {
	    [ ! -d "$CELERYD_PID_DIR" ] && return
	    echo `ls -1 "$CELERYD_PID_DIR"/*.pid 2> /dev/null`
	}

	stop_workers () {
	    $CELERYD_MULTI stopwait $CELERYD_NODES --pidfile="$CELERYD_PID_FILE"
	    sleep $SLEEP_SECONDS
	}


	start_workers () {
	    $CELERYD_MULTI start $CELERYD_NODES $DAEMON_OPTS        \
	                         --pidfile="$CELERYD_PID_FILE"      \
	                         --logfile="$CELERYD_LOG_FILE"      \
	                         --loglevel="$CELERYD_LOG_LEVEL"    \
	                         --cmd="$CELERYD"                   \
	                         $CELERYD_OPTS
	    sleep $SLEEP_SECONDS
	}


	restart_workers () {
	    $CELERYD_MULTI restart $CELERYD_NODES $DAEMON_OPTS      \
	                           --pidfile="$CELERYD_PID_FILE"    \
	                           --logfile="$CELERYD_LOG_FILE"    \
	                           --loglevel="$CELERYD_LOG_LEVEL"  \
	                           --cmd="$CELERYD"                 \
	                           $CELERYD_OPTS
	    sleep $SLEEP_SECONDS
	}

	check_status () {
	    local pid_files=
	    pid_files=`_get_pid_files`
	    [ -z "$pid_files" ] && echo "celery not running (no pidfile)" && exit 1

	    local one_failed=
	    for pid_file in $pid_files; do
	        local node=`basename "$pid_file" .pid`
	        local pid=`cat "$pid_file"`
	        local cleaned_pid=`echo "$pid" | sed -e 's/[^0-9]//g'`
	        if [ -z "$pid" ] || [ "$cleaned_pid" != "$pid" ]; then
	            echo "bad pid file ($pid_file)"
	        else
	            local failed=
	            kill -0 $pid 2> /dev/null || failed=true
	            if [ "$failed" ]; then
	                echo "celery (node $node) (pid $pid) is stopped, but pid file exists!"
	                one_failed=true
	            else
	                echo "celery (node $node) (pid $pid) is running..."
	            fi
	        fi
	    done

	    [ "$one_failed" ] && exit 1 || exit 0
	}


	case "$1" in
	    start)
	        check_dev_null
	        check_paths
	        start_workers
	    ;;

	    stop)
	        check_dev_null
	        check_paths
	        stop_workers
	    ;;

	    reload|force-reload)
	        echo "Use restart"
	    ;;

	    status)
	        check_status
	    ;;

	    restart)
	        check_dev_null
	        check_paths
	        restart_workers
	    ;;
	    try-restart)
	        check_dev_null
	        check_paths
	        restart_workers
	    ;;
	    create-paths)
	        check_dev_null
	        create_paths
	    ;;
	    check-paths)
	        check_dev_null
	        check_paths
	    ;;
	    *)
	        echo "Usage: /etc/init.d/celery {start|stop|restart|kill|create-paths}"
	        exit 64  # EX_USAGE
	    ;;
	esac

	exit 0


This Celery service will look for a config file at /etc/default/celery and that file might look like,

	# Name of nodes to start
	CELERYD_NODES="w1"

	# Where to chdir at start.
	CELERYD_CHDIR="/your perma home/"

	# How to call "manage.py celeryd_multi"
	CELERYD_MULTI="$CELERYD_CHDIR/manage.py celeryd_multi"

	# How to call "manage.py celeryctl"
	CELERYCTL="$CELERYD_CHDIR/manage.py celeryctl"

	# Extra arguments to celeryd
	CELERYD_OPTS="--loglevel=info --time-limit=7200"

	# %n will be replaced with the nodename.
	CELERYD_LOG_FILE="/var/log/celery/%n.log"
	CELERYD_PID_FILE="/var/run/celery/%n.pid"

	# Workers should run as an unprivileged user.
	CELERYD_USER="celery"
	CELERYD_GROUP="dev-group"

	# Name of the projects settings module.
	export DJANGO_SETTINGS_MODULE="perma.settings"


Now you can start and stop Celery as a service. Something like,

    $ sudo service celery stop; sudo service celery start; 

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


### Other bits

Use [Handlebars](http://handlebarsjs.com/) when injecting markup using JavaScript.

Track issues using [GitHub Issues](https://github.com/harvard-lil/perma/issues?milestone=15&state=open).

Issue pull requests when you've got a commit ready.