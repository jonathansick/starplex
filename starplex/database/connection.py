#!/usr/bin/env python
# encoding: utf-8
"""
Handles connection to DB.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import meta


def connect(host="localhost", port=5432, user=None, name=None, password=None):
    """Establish a connection to the Postgres database.

    After running :func:`connect`, sessions can be established.

    >> import starplex
    >> starplex.database.connection.connect(**args)
    >> session = starplex.database.meta.Session()

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
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    url = _build_url(host, port, name, user, password)
    meta.engine = create_engine(url)
    create_all()
    meta.Session = sessionmaker(bind=meta.engine)


def drop_all():
    """Delete all tables.
    
    Needs a connection to already be established with :func:`connect`.
    """
    meta.Base.metadata.drop_all()


def create_all():
    """Create all tables.
    
    Needs a connection to already be established with :func:`connect`.
    """
    meta.Base.metadata.create_all(meta.engine, checkfirst=True)


def _build_url(host, port, name, user, password):
    """Construct the Postgres connection URL"""
    if password is not None:
        return "postgresql+psycopg2://%s:%s@%s:%i/%s" \
                % (user, password, host, port, name)
    else:
        return "postgresql+psycopg2://%s@%s:%i/%s" \
                % (user, host, port, name)
