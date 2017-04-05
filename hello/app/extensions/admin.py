# coding: utf-8

from flask import g, redirect, request, url_for
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.form import AdminModelConverter
from flask_admin.model.form import converts
from wtforms import fields

from app.models import User
from app.utils.database import db


class AuthView(object):

    def is_accessible(self):
        return g.current_user and g.current_user.is_staff is True

    def inaccessible_callback(self, name, **kwargs):
        if g.current_user and g.current_user.is_staff is False:
            return redirect('/')

        # redirect to login page if user doesn't have access
        return redirect(url_for('auth.login', next=request.url))


class BaseModelConverter(AdminModelConverter):

    @converts('NestedJsonObject')
    def nested_json_object(self, field_args, **extra):
        return fields.TextField(**field_args)


class MyModelView(AuthView, ModelView):
    model_form_converter = BaseModelConverter


class MyAdminIndexView(AuthView, AdminIndexView):
    pass


class AdminUserView(MyModelView):
    column_list = [
        'id', 'first_name', 'last_name', 'email', 'is_staff', 'verified_at', 'created_at', 'modified_at', 'deleted_at'
    ]


admin = Admin(
    index_view=MyAdminIndexView(url='/u/<int:user_index>/admin'),
    template_mode='bootstrap3',
    url='/u/<int:user_index>/admin')
admin.add_view(AdminUserView(User, db.session))
