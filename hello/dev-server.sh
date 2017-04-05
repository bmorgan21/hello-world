#!/bin/bash
set -eo pipefail

if [ -z "$FLASK_CODE_DIR" ]; then
    FLASK_CODE_DIR=/var/code
fi

if [ -z "$FLASK_HTTP_PORT" ]; then
    FLASK_HTTP_PORT=5000
fi

cd $FLASK_CODE_DIR
set -- gosu uwsgi flask run --host=0.0.0.0 --port $FLASK_HTTP_PORT

while /bin/true ; do
	$@ 2>&1 || sleep 1;
done

exit 0
