# coding: utf-8

import celery as _celery
from celery.schedules import crontab
from flask import g

from app.utils.database import db


class Celery(_celery.Celery):

    def init_app(self, app):
        self.conf.update({k.lstrip('CELERY_').lower(): v for k, v in app.config.items() if k.startswith('CELERY_')})
        task_always_eager = self.conf.get('task_always_eager', False)

        # times are in UTC unless self.conf.timezone is changed
        self.conf.beat_schedule = {
            'add-every-30-seconds': {
                'task': 'app.tasks.add',
                'schedule': 30.0,
                'args': (16, 16)
            },
            'add-every-monday-morning': {
                'task': 'app.tasks.add',
                'schedule': crontab(hour=7, minute=30, day_of_week=1),
                'args': (16, 16),
            },
        }

        if task_always_eager:

            @app.after_request
            def handler(response):
                for name, func, args, kwargs in getattr(g, 'after_request_tasks', []):
                    func(*args, **kwargs)
                    if db.session.new or db.session.deleted or db.session.dirty:
                        raise Exception('State not committed before exiting task: {}'.format(name))

                return response

            class AfterRequestTask(_celery.Task):
                abstract = True

                def __call__(self, *args, **kwargs):
                    if not hasattr(g, 'after_request_tasks'):
                        g.after_request_tasks = []
                    g.after_request_tasks.append((self.name, super().__call__, args, kwargs))

                    # we currently don't do anything with the task result.  If this changes, this approach won't work
                    return

            self.Task = AfterRequestTask
        else:

            class ContextTask(_celery.Task):
                abstract = True

                def __call__(self, *args, **kwargs):
                    with app.app_context():
                        return super().__call__(*args, **kwargs)

            self.Task = ContextTask


celery = Celery()
