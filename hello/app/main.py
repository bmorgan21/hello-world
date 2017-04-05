# coding: utf-8

import logging

# call this right away to handle monkey patching before anything happens
from app.utils import monkey_patch  # noqa

from app.extensions.flask_celery import celery  # noqa
from app.factory import create_app

logger = logging.getLogger(__name__)

try:
    app = create_app(__name__)
except ImportError as e:
    logger.error(e)
    raise

from app.tasks import *  # noqa
