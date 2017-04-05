# coding: utf-8

from datetime import datetime, timedelta

import passlib.context
import passlib.pwd
from sqlalchemy.orm import synonym

from app.utils.database import db

__all__ = ['User']

pwd_context = passlib.context.CryptContext(schemes=["pbkdf2_sha256", "des_crypt"])


class User(db.Model, db.Timestamp, db.HasProperties, db.FullText):

    __fulltext_columns__ = ('first_name', 'last_name')

    first_name = db.Column(db.Unicode(64))
    last_name = db.Column(db.Unicode(64))
    email = db.Column(db.Unicode(255), nullable=False, unique=True)
    _password = db.Column(db.UnicodeText, name="password")
    _temp_password = db.Column(db.UnicodeText, name="temp_password")
    password_expires = db.Column(db.DateTime)

    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    tick = db.Column(db.Integer, nullable=False, default=0)

    last_login_at = db.Column(db.DateTime)
    last_request_at = db.Column(db.DateTime)

    @staticmethod
    def mkpassword(length=16):
        return passlib.pwd.genword(length=length)

    @staticmethod
    def check_password(password, plain_text_password):
        return password and plain_text_password and pwd_context.verify(plain_text_password, password)

    def __unicode__(self):
        return '{} {} ({})'.format(self.first_name, self.last_name, self.email)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, plain_text_password):
        self._password = pwd_context.hash(plain_text_password)
        self.password_expires = datetime.utcnow() + timedelta(days=365)

    password = synonym('_password', descriptor=password)

    @property
    def temp_password(self):
        return self._temp_password

    @temp_password.setter
    def temp_password(self, plain_text_password):
        self._temp_password = pwd_context.hash(plain_text_password) if plain_text_password is not None else None

    temp_password = synonym('_temp_password', descriptor=temp_password)
