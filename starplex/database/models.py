#!/usr/bin/env python
# encoding: utf-8
"""
Table models for SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

from .meta import Base


class Star(Base):
    """SQLAlchemy table for representing a `star`."""
    __tablename__ = 'star'

    id = Column(Integer, primary_key=True)
    ra = Column(Float)
    dec = Column(Float)

    def __init__(self, ra, dec):
        self.ra = ra
        self.dec = dec

    def __repr__(self):
        return "<Star(%i, %.8f, %.8f)>" % (self.id, self.ra, self.dec)


class SEDDatum(Base):
    """SQLAlchemy table for representing an reduced magnitude, making up
    a datum of a star's SED.
    """
    __tablename__ = 'sed'

    id = Column(Integer, primary_key=True)

    # Many to one on bandpass
    bandpass_id = Column(Integer, ForeignKey('bandpass.id'))
    bandpass = relationship("Bandpass",  # no need to backref
            foreign_keys="[SEDDatum.bandpass_id]")

    # Many to one on star
    star_id = Column(Integer, ForeignKey('star.id'))
    star = relationship("Star",
            foreign_keys="[SEDDatum.star_id]",
            backref=backref("sed", order_by=id))

    # TODO need a many-to-many between reduced observation and observation?
    # Because an observation can be reduced multiple ways?

    def __init__(self):
        pass

    def __repr__(self):
        return "<SEDDatum(%i)>" % self.id


class Observation(Base):
    """SQLAlchemy table for representing an `observation`."""
    __tablename__ = 'observation'

    id = Column(Integer, primary_key=True)
    mag = Column(Float)
    magerr = Column(Float)

    bandpass_id = Column(Integer, ForeignKey('bandpass.id'))
    bandpass = relationship("Bandpass",
            foreign_keys="[Observation.bandpass_id]",
            backref=backref('observations', order_by=id))

    catalogstar_id = Column(Integer, ForeignKey('catalogstar.id'))
    catalogstar = relationship("CatalogStar",
            foreign_keys="[Observation.catalogstar_id]",
            backref=backref('observations', order_by=id))

    def __init__(self, mag, magerr):
        self.mag = mag
        self.magerr = magerr

    def __repr__(self):
        return "<Observation(%i)>" % self.id


class Catalog(Base):
    """SQLAlchemy table for representing a source `catalog`."""
    __tablename__ = 'catalog'

    id = Column(Integer, primary_key=True)
    catalogname = Column(String)
    catalogpath = Column(String)
    fitspath = Column(String)
    telescope = Column(String)

    def __init__(self, catalogname, catalogpath, fitspath, telescope):
        self.catalogname = catalogname
        self.catalogpath = catalogpath
        self.fitspath = fitspath
        self.telescope

    def __repr__(self):
        return "<Observation(%i)>" % self.id


class CatalogStar(Base):
    """SQLAlchemy table for representing an object in a `catalog`.
    Observations are associated with the `observation` table.
    """
    __tablename__ = 'catalogstar'

    id = Column(Integer, primary_key=True)
    x = Column(Float)
    y = Column(Float)
    ra = Column(Float)
    dec = Column(Float)
    cfrac = Column(Float)

    # Many to one
    catalog_id = Column(Integer, ForeignKey('catalog.id'))
    catalog = relationship("Catalog",
            foreign_keys="[CatalogStar.catalog_id]",
            backref=backref('catalog_stars', order_by=id))

    # Reference the star we associate to
    star_id = Column(Integer, ForeignKey('star.id'))
    star = relationship("Star",
            foreign_keys="[CatalogStar.star_id]",
            backref=backref('catalog_stars', order_by=id))

    def __init__(self, x, y, ra, dec, cfrac):
        self.x = x
        self.y = y
        self.ra = ra
        self.dec = dec
        self.cfrac = cfrac

    def __repr__(self):
        return "<CatalogStar(%i)>" % self.id


class Bandpass(Base):
    """SQLAlchemy table for representing a bandpass."""
    __tablename__ = 'bandpass'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Bandpass(%i)>" % self.id


class ColorTransform(Base):
    """SQLAlchemy table for representing a color transformation."""
    __tablename__ = 'colortransform'

    id = Column(Integer, primary_key=True)

    def __init__(self):
        pass

    def __repr__(self):
        return "<colortransform(%i)>" % self.id


class ZPDelta(Base):
    """SQLAlchemy table for representing a zeropoint shift."""
    __tablename__ = 'zpdelta'

    id = Column(Integer, primary_key=True)
    kind = Column(String)
    delta = Column(Float)

    # Many to one against catalogs
    catalog_id = Column(Integer, ForeignKey('catalog.id'))
    catalog = relationship("Catalog", backref="zpdeltas",
            foreign_keys="[ZPDelta.catalog_id]")

    # Many to one against bandpasses
    bandpass_id = Column(Integer, ForeignKey('bandpass.id'))
    bandpass = relationship("Bandpass",  # no need to backref
            foreign_keys="[ZPDelta.bandpass_id]")

    def __init__(self, kind, delta):
        self.kind = kind
        self.delta = delta

    def __repr__(self):
        return "<ZPDelta(%i, %s, %.3f>" % (self.id, self.kind, self.delta)
