#!/bin/bash
set -eo pipefail

# if command starts with an option, prepend uwsgi
if [ "${1:0:1}" = '-' ]; then
	set -- uwsgi "$@"
fi

# Drop root privileges if we are running uwsgi
# allow the container to be started with `--user`
if [ "$1" = 'uwsgi' -a "$(id -u)" = '0' ]; then

    if [ ! -f "/tmp/uwsgi_first_run" ]; then

        # Invoke extra commands
        echo
        for f in /docker-entrypoint-init-uwsgi.d/*; do
            case "$f" in
                *.sh)     echo "$0: running $f"; . "$f" ;;
                *)        echo "$0: ignoring $f" ;;
            esac
            echo
        done

        touch "/tmp/uwsgi_first_run"

        echo
        echo 'UWSGI init process done. Ready for start up.'
        echo
    fi

    # There are some defaults we should set
    if [ -z "$UWSGI_PROJECT_HOME" ]; then
        UWSGI_PROJECT_HOME=/var/code
    fi

    if [ -z "$UWSGI_SERVICE_MODULE" ]; then
        UWSGI_SERVICE_MODULE=app.main:app
    fi

    if [ -z "$UWSGI_PROCESSES" ]; then
        UWSGI_PROCESSES=4
    fi

    if [ -z "$UWSGI_THREADS" ]; then
        UWSGI_THREADS=10
    fi

    if [ -z "$UWSGI_THREADS_STACKSIZE" ]; then
        UWSGI_THREADS_STACKSIZE=1024
    fi

    if [ -z "$UWSGI_SOCKET_PORT" ]; then
        UWSGI_SOCKET_PORT=3031
    fi

    if [ "$UWSGI_HTTP_PORT" ]; then
        set -- "$@" --http :$UWSGI_HTTP_PORT
    fi

    # Append other required arguments (first non-parameterized, then parameterized for uwsgi, then parameterized for app)
    set -- "$@" --master --need-app --max-request 100 --die-on-term --socket :$UWSGI_SOCKET_PORT --stats :1717 --buffer-size 16192 --reload-on-rss=768 --thunder-lock
    set -- "$@" --processes $UWSGI_PROCESSES --threads $UWSGI_THREADS --threads-stacksize $UWSGI_THREADS_STACKSIZE
    set -- "$@" --chdir $UWSGI_PROJECT_HOME --pp $UWSGI_PROJECT_HOME --module $UWSGI_SERVICE_MODULE

    # Now execute under the uwsgi user
    set -- gosu uwsgi "$@"

elif [ "$1" = 'celery-beat' -a "$(id -u)" = '0' ]; then
    if [ -z "$CELERY_APP" ]; then
        CELERY_APP=app.main:celery
    fi

    if [ -z "$CELERY_SCHEDULE" ]; then
        CELERY_SCHEDULE=/tmp/celerybeat-schedule
    fi

    if [ -z "$CELERY_PID" ]; then
        CELERY_PID=/tmp/celerybeat.pid
    fi

    if [ -z "$CELERY_LOGLEVEL" ]; then
        CELERY_LOGLEVEL=info
    fi

    set -- gosu uwsgi celery -A $CELERY_APP beat --loglevel=$CELERY_LOGLEVEL --schedule=$CELERY_SCHEDULE --pidfile=$CELERY_PID

elif [ "$1" = 'celery-worker' -a "$(id -u)" = '0' ]; then
    if [ -z "$CELERY_APP" ]; then
        CELERY_APP=app.main:celery
    fi

    if [ -z "$CELERY_LOGLEVEL" ]; then
        CELERY_LOGLEVEL=info
    fi

    set -- gosu uwsgi celery -A $CELERY_APP worker --loglevel=$CELERY_LOGLEVEL

fi


exec "$@"
