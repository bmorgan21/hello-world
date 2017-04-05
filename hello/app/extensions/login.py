# coding: utf-8

from datetime import datetime
from functools import wraps
import logging
import re
import time

from urllib.parse import urlparse

from flask import current_app, g, redirect, request, url_for
from itsdangerous import BadSignature, TimedJSONWebSignatureSerializer

from app.models import User
from app.utils.database import db
from app.utils.routing import context_url

logger = logging.getLogger(__name__)

COOKIE_NAME_PATTERN = 'u{}'
cookie_name_re = re.compile('u([0-9]+)')


def login_required(func):

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if g.current_user is None:
            return redirect(url_for('auth.login', next=request.url))
        elif not g.current_user_fresh:
            return redirect(url_for('auth.login', next=request.url, user_index=g.user_index))
        return func(*args, **kwargs)

    decorated_view.original_func = func

    return decorated_view


def next_index():
    for i in range(100):
        cookie_name = COOKIE_NAME_PATTERN.format(i)
        if cookie_name not in request.cookies:
            return i
    return 0


def login_user(user, session_only=False):
    fresh = True
    found_user = [x for x in g.known_users if x[1] == user]

    if found_user:
        g.user_index = found_user[0][0]
    else:
        if current_app.config['SESSION_LIMIT_TO_ONE']:
            user.tick += 1

        g.user_index = next_index()

        if session_only:
            fresh = False

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    g.current_user_fresh = fresh
    g.current_user = user

    g.real_user = g.current_user


def logout_user():
    g.current_user = None
    g.real_user = None


def refresh_user():
    g.current_user_fresh = True

    if current_app.config['SESSION_LIMIT_TO_ONE']:
        g.current_user.tick += 1


def switch_user(user):
    g.current_user_fresh = True
    g.current_user = user


def is_impersonating():
    return (g.real_user and g.real_user.is_staff and g.real_user != g.current_user)


def _dumps(value, expires_in, namespace=None):
    s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expires_in=expires_in, salt=namespace)

    header_fields = {'t': time.time()}

    return s.dumps(value, header_fields=header_fields)


def _loads(value, namespace=None, default=None):
    s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], salt=namespace)
    try:
        payload, headers = s.loads(value, return_header=True)
        now = time.time()
        return now - headers['t'] < current_app.config['SESSION_MAX_AGE'], payload
    except BadSignature as e:
        logger.info(e)
    return False, default


def init_app(app):

    @app.after_request
    def after_request(response):
        if g.user_index is not None:
            d = {}
            max_age = 0

            if g.current_user:
                if g.current_user == g.real_user:
                    max_age = current_app.config['SESSION_MAX_IDLE']
                else:
                    max_age = current_app.config['SESSION_MAX_AGE']
                d['user_id'] = g.current_user.id if g.current_user else None
                d['real_user_id'] = g.real_user.id if g.real_user and g.real_user else None
                d['real_user_tick'] = (g.real_user.tick if g.real_user else None) if g.current_user_fresh else None

            parsed_url = urlparse(request.url)

            response.set_cookie(
                COOKIE_NAME_PATTERN.format(g.user_index),
                value=_dumps(d, expires_in=max_age),
                max_age=max_age,
                httponly=True,
                secure=parsed_url.scheme == 'https')

        return response

    @app.before_request
    def before_request():
        values = []
        for name in request.cookies.keys():
            m = cookie_name_re.match(name)
            if m:
                idx = m.groups()[0]
                fresh, d = _loads(request.cookies[name])
                if d:
                    d['fresh'] = fresh
                    values.append((int(idx), d))

        values.sort(key=lambda x: x[0])

        user_ids = {x[1].get('user_id') for x in values} | {x[1].get('real_user_id') for x in values}
        users = {x.id: x for x in User.query.filter(User.id.in_([x for x in user_ids if x]))}

        g.known_users = known_users = []
        found_data = None
        found_index = 0
        for (i, d) in values:
            real_user = users.get(d.get('real_user_id'))
            fresh = d['fresh'] = d.get('fresh', False) and real_user and real_user.tick == d.get('real_user_tick')
            known_users.append((i, users.get(d.get('user_id')),
                                d.get('user_id') != d.get('real_user_id'), fresh))

            if i == g.user_index:
                found_data = d
                found_index = len(known_users) - 1

        d = {}
        if found_data:
            d = found_data
            known_users.insert(0, known_users.pop(found_index))
        elif g.user_index and len(values) > 0:
            g.user_index = None
            return redirect(context_url(request.url, user_index=values[0][0]))

        g.current_user_fresh = d.get('fresh')
        g.current_user = users.get(d.get('user_id'))
        g.real_user = users.get(d.get('real_user_id'))

    @app.context_processor
    def context_processor():
        return dict(
            user_index=g.user_index,
            current_user_fresh=g.current_user_fresh,
            current_user=g.current_user,
            impersonating=is_impersonating(),
            real_user=g.real_user,
            known_users=g.known_users)
