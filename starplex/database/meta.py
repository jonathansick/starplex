#!/usr/bin/env python
# encoding: utf-8
"""
Handles Base metadata for table models.
"""

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

engine = None
# base.Base.metadata.create_all(engine, checkfirst=True)
Session = None  # sessionmaker(bind=engine)
