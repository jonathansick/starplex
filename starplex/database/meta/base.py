#!/usr/bin/env python
# encoding: utf-8
"""Base SQLAlchemy tools for connecting to a Postgres database with SQLAlchemy.

Here we provide the SQLAlchemy ``engine``, ``Session`` and ``Base``.

This module is partly based on an example project presented by Mike Bayer at
PyCon 2014, available at `<https://bitbucket.org/zzzeek/pycon2014_atmcraft>`_.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from decorator import decorator


engine = None
Session = sessionmaker()


def connect(host="localhost", port=5432, user=None, name=None, password=None,
        **kwargs):
    """Establish a connection to the Postgres database.

    After running :func:`connect`, sessions can be established.

    >> import starplex
    >> starplex.database.connect(**args)
    >> session = starplex.database.Session()

    Parameters
    ----------
    host : str
        Hostname
    port : int
        Server port
    user : str
        Username for server
    password : str
        Password to log into server
    name : str
        Name of database
    """
    global engine
    url = _build_url(host, port, name, user, password)
    engine = create_engine(url)
    Session.configure(bind=engine)
    Base.metadata.bind = engine


def _build_url(host, port, name, user, password):
    """Construct the Postgres connection URL"""
    if password is not None:
        return "postgresql+psycopg2://%s:%s@%s:%i/%s" \
                % (user, password, host, port, name)
    else:
        return "postgresql+psycopg2://%s@%s:%i/%s" \
                % (user, host, port, name)


def drop_all():
    """Delete all tables.

    Note that the change is *not* committed, and thus could be rolled back.
    Needs a connection to already be established with :func:`connect`.
    """
    Base.metadata.drop_all()


def create_all():
    """Create all tables.
    
    Needs a connection to already be established with :func:`connect`.
    """
    Base.metadata.create_all()


@decorator
def commit_on_success(fn, *arg, **kw):
    """Decorate any function to commit the session on success, rollback in
    the case of error."""

    try:
        result = fn(*arg, **kw)
        Session.commit()
    except:
        Session.rollback()
        raise
    else:
        return result

# NOTE, use this to enable the References mixin in schema.py
# class Base(References):
#     pass
class Base(object):
    pass


Base = declarative_base(cls=Base)

# establish a constraint naming convention.
# see http://jsick.net/RicYJE
Base.metadata.naming_convention={
        "pk": "pk_%(table_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s"
    }
