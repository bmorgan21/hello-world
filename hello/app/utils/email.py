# coding: utf-8

from flask import current_app, render_template
from flask_mail import Message

from app.extensions.mail import mail

DEFAULT_SENDER = 'info@hello-world.com'


class EmailMessage(object):

    def __init__(self, subject, recipients, sender=DEFAULT_SENDER):
        extra_headers = {}
        if not current_app.config['MAIL_SUPPRESS_SEND'] and current_app.config['ENABLE_MAIL_RECIPIENT_OVERRIDE']:
            recipient_override = current_app.config['MAIL_RECIPIENT_OVERRIDE']
            if recipient_override:
                extra_headers['X-CT-Recipients'] = ','.join(recipients)
                recipients = [recipient_override]

        sub_account = current_app.config['MAIL_SUBACCOUNT']
        if sub_account:
            extra_headers['X-MC-Subaccount'] = sub_account

        self._message = Message(subject, sender=sender, recipients=recipients, extra_headers=extra_headers)

    def html(self, value):
        self._message.html = value

    html = property(None, html)

    def send(self):
        mail.send(self._message)


def send_reset_password(user, password):
    msg = EmailMessage('Reset Your Password', recipients=[user.email])

    msg.html = render_template('email/reset_password.html', user=user, password=password)

    msg.send()
