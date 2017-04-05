# coding: utf-8

import logging
import os

from flask import Flask, g, redirect, render_template, request, url_for
from werkzeug.debug import DebuggedApplication

from app.extensions.admin import admin
from app.extensions.assets import assets
from app.extensions.flask_celery import celery
from app.extensions.login import init_app as login_init_app, login_user
from app.extensions.mail import mail
from app.extensions.migrate import migrate
from app.models import User
from app.utils.database import db
from app.utils.jinja import register_jinja_filters
from app.utils.routing import context_url, IdConverter

logger = logging.getLogger(__name__)


def create_app(import_name):
    app = Flask(import_name, instance_relative_config=True)
    app.url_map.converters['id'] = IdConverter

    app.config.from_object('app.settings')

    log_level = logging.INFO

    if app.debug:
        app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
        log_level = logging.DEBUG
        app.config['ASSETS_VERSIONS'] = 'timestamp'

    logging.basicConfig(level=log_level)

    ###
    # Register Extensions
    ##
    admin.init_app(app)
    assets.init_app(app)
    celery.init_app(app)
    db.init_app(app)
    login_init_app(app)
    mail.init_app(app)
    migrate.init_app(app=app, db=db)

    if app.config['DEBUG']:
        app.config['ASSETS_DEBUG'] = True
        from flask_debugtoolbar import DebugToolbarExtension
        app.config['DEBUG_TB_PANELS'] = (
            'flask_debugtoolbar.panels.versions.VersionDebugPanel', 'flask_debugtoolbar.panels.timer.TimerDebugPanel',
            'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
            'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
            'flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel',
            'flask_debugtoolbar.panels.template.TemplateDebugPanel',
            'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
            'flask_debugtoolbar.panels.logger.LoggingPanel', 'flask_debugtoolbar.panels.route_list.RouteListDebugPanel',
            'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel', 'app.extensions.mail.EmailDebugPanel')

        DebugToolbarExtension(app)

    ###
    # Register View endpoints
    ##

    from app.views import auth, home
    app.register_blueprint(auth.bp, url_prefix="/auth")
    app.register_blueprint(home.bp)

    @app.route('/u/')
    def handle_user_base_url():
        return redirect(context_url('/', user_index='-'))

    @app.route('/u/-/', defaults={'wildcard': None})
    @app.route('/u/-/<path:wildcard>')
    def handle_unknown_index(wildcard):
        user_id = request.args.get('uid')
        if user_id is not None:
            user = User.query.get_or_404(user_id)

            login_user(user, session_only=not app.config['DEBUG'])

            return redirect(context_url(request.url, uid=None, guid=None))

        return redirect(url_for('auth.login', next=request.url))

    @app.route('/u/<int:user_index>/check/<int:group_id>/<int:user_id>/')
    def check(group_id, user_id):
        current_group_id = g.current_group.id if g.current_group else None
        current_user_id = g.current_user.id if g.current_user else None

        if current_group_id == group_id and current_user_id == user_id:
            return 'OK', 200
        else:
            return 'MISMATCH', 200

    @app.route('/health/ping/')
    def ping():
        return 'pong', 200

    ###
    # Custom Error Handlers
    ##
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('error/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('error/500.html'), 500

    ###
    # Inject Template Variables
    ##
    @app.context_processor
    def context_processor():

        def dated_url_for(endpoint, **values):
            if endpoint == 'static':
                filename = values.get('filename', None)
                if filename:
                    file_path = os.path.join(app.root_path, endpoint, filename)
                    values['q'] = int(os.stat(file_path).st_mtime)
            return url_for(endpoint, **values)

        return {'url_for': dated_url_for}

    ###
    # Custom Jinja Filters
    ###
    register_jinja_filters(app.jinja_env)

    ###
    # Inject Shell Context Variables
    ##
    @app.shell_context_processor
    def shell_cmd_context():
        from app import models
        from app.utils.database import db
        return {'m': models, 'db': db}

    @app.url_value_preprocessor
    def url_value_preprocessor(endpoint, values):
        g.user_index = None
        if values:
            g.user_index = values.pop('user_index', None)

        if g.user_index is None:
            if 'user_index' in request.args:
                g.user_index = int(request.args['user_index'])

    @app.url_defaults
    def url_defaults(endpoint, values):
        if endpoint not in ('static', '_debug_toolbar.static'):
            values.setdefault('user_index', g.user_index)

    return app
