# coding: utf-8

from flask import render_template, request
from flask_debugtoolbar import module
from flask_debugtoolbar.panels import DebugPanel
from flask_mail import email_dispatched, Mail

mail = Mail()


def log_email(email, app):
    if app.debug:
        EmailDebugPanel.emails.append(email)


email_dispatched.connect(log_email)


class EmailDebugPanel(DebugPanel):
    emails = []
    name = "Emails"

    def __init__(self, jinja_env, context={}):
        DebugPanel.__init__(self, jinja_env, context=context)
        self.is_active = True

    @property
    def has_content(self):
        return bool(self.emails)

    def title(self):
        return 'Emails'

    def nav_title(self):
        return 'Emails'

    def nav_subtitle(self):
        count = len(self.emails)
        return '{} {}'.format(count, 'email' if count == 1 else 'emails')

    def url(self):
        return ''

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        pass

    def content(self):
        return render_template('panels/email.html', emails=self.emails)


@module.route('/email/view/', methods=['GET', 'POST'])
def view_message():
    index = int(request.args['idx'])
    email = EmailDebugPanel.emails[index]
    return render_template('panels/email_view.html', email=email, index=index)
