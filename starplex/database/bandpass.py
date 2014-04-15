#!/usr/bin/env python
# encoding: utf-8
"""
Representation of bandpasses with the SQLAlchemy ORM.
"""
from sqlalchemy import Column, Integer, String

from .meta import Base


class Bandpass(Base):
    """SQLAlchemy table for representing a bandpass."""
    __tablename__ = 'bandpass'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    system = Column(String)

    def __init__(self, name, system):
        self.name = name
        self.system = system

    def __repr__(self):
        return "<Bandpass({id})> {name} {sys}".format(id=self.id,
                name=self.name, sys=self.system)
