# coding: utf-8

import sys

import flask
import flask.cli


def locate_app(app_id):
    """Attempts to locate the application."""
    __traceback_hide__ = True  # noqa
    if ':' in app_id:
        module, app_obj = app_id.split(':', 1)
    else:
        module = app_id
        app_obj = None

    try:
        __import__(module)
    except ImportError:
        # BM: this chunk here is the fix backported
        # Reraise the ImportError if it occurred within the imported module.
        # Determine this by checking whether the trace has a depth > 1.
        if sys.exc_info()[-1].tb_next:
            raise
        else:
            raise flask.cli.NoAppException('The file/path provided (%s) does not appear to '
                                           'exist.  Please verify the path is correct.  If '
                                           'app is not on PYTHONPATH, ensure the extension '
                                           'is .py' % module)
    mod = sys.modules[module]
    if app_obj is None:
        app = flask.cli.find_best_app(mod)
    else:
        app = getattr(mod, app_obj, None)
        if app is None:
            raise RuntimeError('Failed to find application in module "%s"' % module)

    return app


if flask.__version__ != '0.12':
    raise Exception('Check to make sure new version needs to locate_app patch, 0.13-dev has the fix')

# this properly reports import errors within the code vs saying no app is found
flask.cli.locate_app = locate_app
