# coding: utf-8

import re

from werkzeug.routing import BaseConverter

from app.utils.security import decode_id, encode_id

user_index_re = re.compile('^(/u/[0-9]+)/')


class IdConverter(BaseConverter):

    def to_python(self, value):
        return decode_id(value)

    def to_url(self, value):
        return BaseConverter.to_url(self, encode_id(value))


def context_url(path):
    pass
