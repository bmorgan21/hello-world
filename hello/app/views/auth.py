# coding: utf-8

import logging

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms.fields import PasswordField, StringField
from wtforms.validators import DataRequired, Email, EqualTo

from app.extensions.login import login_required, login_user, logout_user, refresh_user
from app.models import User
from app.utils.database import db
from app.utils.email import send_reset_password
from app.utils.routing import context_url

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        rv = super().validate()
        if not rv:
            return False

        user = User.query.filter_by(email=self.email.data).one_or_none()
        if user:
            password_match = User.check_password(user.password, self.password.data)
            temp_password_match = User.check_password(user.temp_password, self.password.data)
            if password_match or temp_password_match:
                if not password_match and temp_password_match:
                    # these are only good once
                    user.temp_password = None
                self.user = user
                return True

        self.password.errors.append('Invalid email and/or password specified.')
        return False


class SignupForm(FlaskForm):
    email = StringField('', validators=[DataRequired(), Email()], render_kw={'placeholder': 'you@yourbusiness.com'})
    first_name = StringField('', validators=[DataRequired()], render_kw={'placeholder': 'First Name'})
    last_name = StringField('', validators=[DataRequired()], render_kw={'placeholder': 'Last Name'})
    password = PasswordField(
        '', validators=[DataRequired()], render_kw={'placeholder': 'Password'})

    def validate(self):
        rv = super().validate()

        if not rv:
            return False

        user = User.query.filter_by(email=self.email.data).one_or_none()

        if user:
            self.email.errors.append('Account already exists, please try logging in.')
            return False

        return True


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        rv = super().validate()
        if not rv:
            return False

        user = User.query.filter_by(email=self.email.data).one_or_none()
        if user:
            self.user = user
            return True

        self.email.errors.append('The email is incorrect. Please try again.')

        return False


class ChangePasswordForm(FlaskForm):
    new_password = PasswordField(
        'New Password',
        validators=[DataRequired(), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])


@bp.route('/login/', methods=['GET', 'POST'])
def login():
    next = request.args.get('next', '/')

    data = {}
    if g.current_user:
        if g.current_user_fresh:
            return redirect(next)
        else:
            data = {'email': g.current_user.email}

    login_form = LoginForm(data=data)

    if login_form.validate_on_submit():
        if g.current_user and g.current_user.email == login_form.email.data:
            refresh_user()
        else:
            login_user(login_form.user)

        # temp passwords can only be used once
        db.session.commit()
        return redirect(next)

    return render_template('auth/login.html', form=login_form)


@bp.route("/logout/")
def logout():
    logout_user()

    return redirect('/')


@bp.route('/forgot_password/', methods=['GET', 'POST'])
def forgot_password():
    next = request.args.get('next', '/')

    if g.current_user:
        return redirect(next)

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = form.user
        password = User.mkpassword()
        user.temp_password = password
        send_reset_password(user, password)

        # temp password was generated

        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@bp.route('/change_password/', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        g.current_user.password = form.new_password.data
        db.session.commit()
        return redirect('/')

    return render_template('auth/change_password.html', form=form)


@bp.route('/signup/', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if g.current_user:
        return redirect(context_url('/'))

    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)
        db.session.add(user)

        db.session.commit()

        login_user(user)

        flash('Thanks for signing up!')
        return redirect('/')

    return render_template('auth/signup.html', form=form)
