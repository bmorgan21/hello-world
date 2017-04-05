# coding: utf-8

import warnings

from flask.exthook import ExtDeprecationWarning
from sqlalchemy import exc

warnings.simplefilter('ignore', ExtDeprecationWarning)
warnings.simplefilter('ignore', category=exc.SAWarning)
