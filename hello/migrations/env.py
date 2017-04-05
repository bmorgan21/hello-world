# coding: utf-8

from __future__ import with_statement

import logging
from logging.config import fileConfig

from alembic import context
from alembic import op
from flask import current_app
from sqlalchemy import engine_from_config, pool
from sqlalchemy.dialects import mysql
from sqlalchemy.sql.schema import Column

from app.utils.database import db

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option('sqlalchemy.url', current_app.config.get('SQLALCHEMY_DATABASE_URI'))

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# change up column ordering to make sure the id column is first
def create_table(table_name, *columns, **kw):
    id_column = [x for x in columns if isinstance(x, Column) and x.name == 'id']
    if len(id_column) == 1:
        id_column = id_column[0]

        columns = list(columns)
        columns.remove(id_column)
        columns = [id_column] + columns

    return _create_table(table_name, *columns, **kw)


_create_table = op.create_table
op.create_table = create_table


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url)

    context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.readthedocs.org/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix='sqlalchemy.', poolclass=pool.NullPool)

    connection = engine.connect()
    context.configure(
        compare_type=compare_type,
        compare_server_default=True,
        connection=connection,
        process_revision_directives=process_revision_directives,
        render_item=render_item,
        target_metadata=db.Model.metadata,
        **current_app.extensions['migrate'].configure_args)

    try:
        context.run_migrations()
    finally:
        connection.close()


ARE_SAME = False
FALLBACK_TO_DEFAULT_BEHAVIOR = None


def compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    return FALLBACK_TO_DEFAULT_BEHAVIOR


def render_item(type_, obj, autogen_context):
    """Apply custom rendering for selected items."""

    # default rendering for other objects
    return False


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
