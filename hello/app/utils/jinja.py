# coding: utf-8

import datetime

import bleach
import humanize
from jinja2 import Markup


def register_jinja_filters(environment):

    def ago(dt):
        return humanize.naturaltime(datetime.datetime.now() - dt)

    def clean(content):
        return Markup(bleach.clean(content))

    def nl2br(value):
        if isinstance(value, str):
            return value.replace('\n', '<br>\n')
        return value

    def plural(count, singluar, plural):
        if count == 1:
            return '{} {}'.format(count, singluar)
        else:
            return '{} {}'.format(count, plural)

    environment.filters.update({
        'ago': ago,
        'clean': clean,
        'nl2br': nl2br,
        'plural': plural
    })
