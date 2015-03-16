#!/usr/bin/env python
# encoding: utf-8
"""
ORM tables for the intercal method of calibrating multi-field photometric
catalogs.
"""

from sqlalchemy import Column, Integer, Float
from sqlalchemy import ForeignKey
from sqlalchemy.orm import aliased

from .meta import Base, UniqueMixin
from .observation import Catalog
from .bandpass import Bandpass


class IntercalEdge(UniqueMixin, Base):
    """SQLAlchemy table for representing connections between photometric
    catalogs and ZP offsets in a single bandpass. Each row is thus effectively
    an edge in a directed graph.
    """
    __tablename__ = 'intercal_edge'

    id = Column(Integer, primary_key=True)
    from_id = Column(Integer,
                     ForeignKey('catalog.id', ondelete='CASCADE'))
    to_id = Column(Integer,
                   ForeignKey('catalog.id', ondelete='CASCADE'))
    bandpass_id = Column(Integer,
                         ForeignKey('bandpass.id', ondelete='CASCADE'))
    delta = Column(Float)
    delta_err = Column(Float)

    def __init__(self, from_catalog, to_catalog, bandpass, delta, delta_err):
        self.from_id = from_catalog.id
        self.to_id = to_catalog.id
        self.bandpass_id = bandpass.id
        if delta is not None:
            self.delta = float(delta)
        else:
            self.delta = None
        if delta_err is not None:
            self.delta_err = float(delta_err)
        else:
            self.delta = None

    @classmethod
    def unique_hash(cls, from_catalog, to_catalog, bandpass, delta, delta_err):
        return "_".join((str(from_catalog), str(to_catalog), bandpass))

    @classmethod
    def unique_filter(cls, query,
                      from_catalog, to_catalog, bandpass, delta, delta_err):
        from_cat = aliased(Catalog)
        to_cat = aliased(Catalog)
        return query.filter(from_cat.id == from_catalog.id)\
            .filter(to_cat.id == to_catalog.id)\
            .filter(Bandpass.id == bandpass.id)

    def __repr__(self):
        return "<IntercalEdge(%i)>" % self.id

    @staticmethod
    def edge_exists(session, from_catalog, to_catalog, bandpass):
        """Return True if this edge, or its reverse, exists."""
        q1 = session.query(IntercalEdge)\
            .filter(IntercalEdge.from_id == from_catalog.id)\
            .filter(IntercalEdge.to_id == to_catalog.id)\
            .filter(IntercalEdge.bandpass_id == bandpass.id)
        if q1.count() > 0:
            return True

        # search for reverse edge
        q2 = session.query(IntercalEdge)\
            .filter(IntercalEdge.from_id == to_catalog.id)\
            .filter(IntercalEdge.to_id == from_catalog.id)\
            .filter(IntercalEdge.bandpass_id == bandpass.id)
        if q2.count() > 0:
            return True

        return False
