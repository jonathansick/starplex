#!/usr/bin/env python
# encoding: utf-8
"""
Handles connection to DB.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import meta


def connect():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    meta.engine = create_engine('sqlite:////tmp/test.db')
    meta.Base.metadata.create_all(meta.engine, checkfirst=True)
    meta.Session = sessionmaker(bind=meta.engine)
