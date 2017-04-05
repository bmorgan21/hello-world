# coding: utf-8

from datetime import datetime
import logging
import re

from flask import g
from flask_sqlalchemy import BaseQuery as SQLABaseQuery, SQLAlchemy
from sqlalchemy import literal, MetaData
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import validates
from sqlalchemy.sql.expression import ClauseElement

from .sqlalchemy_json import NestedJsonObject

logger = logging.getLogger(__name__)

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def convert_to_underscore(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def _escaped(value, escape):
    return value.replace('%', escape + '%').replace('_', escape + '_')


convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)
db.NestedJsonObject = NestedJsonObject


def real_user_id():
    if g.real_user:
        return g.real_user.id
    return None


class Audit(object):

    @declared_attr
    def created_by_id(self):
        return db.Column(
            db.Integer, db.ForeignKey('user.id'), default=real_user_id, server_default=None, nullable=False)

    @declared_attr
    def created_by(self):
        return db.relationship('User', foreign_keys=[self.created_by_id])


class FullText(object):
    __fulltext_columns__ = tuple()

    @declared_attr
    def __table_args__(self):
        return (db.Index('search', *self.__fulltext_columns__, mysql_prefix="FULLTEXT"),)


class FullTextSearch(ClauseElement):
    def __init__(self, against, model, alias=None):
        self.alias = alias
        self.model = model
        self.against = literal(against)


def get_table_name(element):
    if element.alias:
        return "`" + element.alias + "`."
    elif hasattr(element.model, "__table__"):
        return "`" + element.model.__table__.fullname + "`."
    return ""


@compiles(FullTextSearch, 'mysql')
def mysql_fulltext_search(element, compiler):
    return u"MATCH ({0}) AGAINST ({1})".format(
        ", ".join([get_table_name(element) + column for column in element.model.__fulltext_columns__]),
        compiler.process(element.against))


class HasProperties(object):
    properties = db.Column(db.NestedJsonObject, default=dict, server_default=None)

    @validates('properties')
    def validate_properties(self, key, properties):
        assert isinstance(properties, dict)
        return properties


class Timestamp(object):
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


db.Audit = Audit
db.FullText = FullText
db.HasProperties = HasProperties
db.Timestamp = Timestamp


class BaseQuery(SQLABaseQuery):

    def search(self, text, model, alias=None):
        return self.filter(FullTextSearch(text, model, alias=alias))

    def contains(self, column, text):
        return self.filter(column.contains(_escaped(text, '\\')))


class BaseModel(object):
    query_class = BaseQuery

    @declared_attr
    def __tablename__(self):
        return convert_to_underscore(self.__name__)

    @declared_attr
    def id(self):
        return db.Column(db.Integer, primary_key=True)


db.Model = declarative_base(cls=(BaseModel, db.Model), metadata=metadata)
