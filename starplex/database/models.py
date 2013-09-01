#!/usr/bin/env python
# encoding: utf-8
"""
Table models for SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String
from .meta import Base

__all__ = ['Star']


class Star(Base):
    """SQLAlchemy table for representing a `star`."""
    __tablename__ = 'star'

    id = Column(Integer, primary_key=True)

    def __init__(self):
        pass

    def __repr__(self):
       return "<Star()>"
