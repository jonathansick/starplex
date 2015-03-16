#!/usr/bin/env python
# encoding: utf-8
"""
Representation of bandpasses with the SQLAlchemy ORM.
"""
from sqlalchemy import Column, Integer, String

from .meta import Base, UniqueMixin


class Bandpass(UniqueMixin, Base):
    """SQLAlchemy table for representing a bandpass."""
    __tablename__ = 'bandpass'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    system = Column(String)

    @classmethod
    def unique_hash(cls, name, system):
        return "_".join((name, system))

    @classmethod
    def unique_filter(cls, query, name, system):
        return query.filter(Bandpass.name == name)\
            .filter(Bandpass.system == system)

    def __init__(self, name, system):
        self.name = name
        self.system = system

    def __repr__(self):
        return "<Bandpass({id})> {name} {sys}".format(
            id=self.id, name=self.name, sys=self.system)
