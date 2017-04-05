# coding: utf-8

import ast
import os

ENV = os.getenv('ENV', 'local')

SQLALCHEMY_TRACK_MODIFICATIONS = ast.literal_eval(os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False'))
SQLALCHEMY_ECHO = ast.literal_eval(os.getenv('SQLALCHEMY_ECHO', 'False'))
SQLALCHEMY_POOL_RECYCLE = ast.literal_eval(os.getenv('SQLALCHEMY_POOL_RECYCLE', '10'))
SQLALCHEMY_DATABASE_URI = 'mysql://{}:{}@{}:3306/{}'.format(
    os.getenv('MYSQL_USERNAME', 'web_user'),
    os.getenv('MYSQL_PASSWORD', 'password'), os.getenv('MYSQL_HOST', 'db'), os.getenv('MYSQL_DATABASE', 'hw_app'))

SECRET_KEY = 'something random for hello world'

DEBUG_TB_INTERCEPT_REDIRECTS = ast.literal_eval(os.getenv('DEBUG_TB_INTERCEPT_REDIRECTS', 'False'))

EXPLAIN_TEMPLATE_LOADING = ast.literal_eval(os.getenv('EXPLAIN_TEMPLATE_LOADING', 'False'))

TEMPLATES_AUTO_RELOAD = ast.literal_eval(os.getenv('TEMPLATES_AUTO_RELOAD', 'False'))
MAIL_SERVER = os.getenv('MAIL_SERVER', 'postfix')

ENABLE_MAIL_RECIPIENT_OVERRIDE = ast.literal_eval(os.getenv('ENABLE_MAIL_RECIPIENT_OVERRIDE ', 'True'))
MAIL_RECIPIENT_OVERRIDE = os.getenv('MAIL_RECIPIENT_OVERRIDE', 'emails@hello-world.com')
MAIL_SUPPRESS_SEND = ast.literal_eval(os.getenv('MAIL_SUPPRESS_SEND', 'True'))
MAIL_SUBACCOUNT = os.getenv('MAIL_SUBACCOUNT', 'None')

SESSION_LIMIT_TO_ONE = ast.literal_eval(os.getenv('SESSION_LIMIT_TO_ONE', 'True'))
SESSION_MAX_AGE = ast.literal_eval(os.getenv('SESSION_MAX_AGE', str(30 * 60)))
SESSION_MAX_IDLE = ast.literal_eval(os.getenv('SESSION_MAX_IDLE', str(30 * 24 * 60 * 60)))

MAX_CONTENT_LENGTH = ast.literal_eval(os.getenv('MAX_CONTENT_LENGTH', str(100 * 1024 * 1024)))

CLAMAV_SERVER = os.getenv('CLAMAV_SERVER', None)

CELERY_TASK_ALWAYS_EAGER = ast.literal_eval(os.getenv('CELERY_TASK_ALWAYS_EAGER', 'False'))
CELERY_BROKER_URL = 'amqp://{}:{}@{}:5672//'.format(
    os.getenv('CELERY_BROKER_USERNAME', 'guest'),
    os.getenv('CELERY_BROKER_PASSWORD', 'guest'), os.getenv('CELERY_BROKER_HOST', 'rabbitmq'))
