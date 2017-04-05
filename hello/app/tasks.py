# coding: utf-8

from app.extensions.flask_celery import celery


@celery.task()
def add(x, y):
    return x + y
