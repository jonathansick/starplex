#!/usr/bin/env python
# encoding: utf-8
"""
ORM tables to represent observed star catalogs.

Comment about PostGIS Geography data types.
-------------------------------------------

I'm encoding RA/Dec as PostGIS
geography data types. This allow distances to be computed using spherical
geometry, however, the Geography data type can only use the 4326 SRID.
This is the standard WK 84 definition for representing the Earth. However,
this is not ideal for astronomy since the celestial sphere is truly a sphere!

The alternative is switching to the 2D geometry projection, perhaps with
SRID 4047. However, I can't get PostGIS/GeoAlchemy to let me insert points
with this SRID.

Two resources for using PostGIS in astronomy are:

- http://jsick.net/14bF4ZQ
- http://skyview.gsfc.nasa.gov/xaminblog/index.php/tag/postgis/
"""

from sqlalchemy import Column, Integer, String, Float
from geoalchemy2 import Geography
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import HSTORE, JSON
from sqlalchemy.ext.mutable import MutableDict

from .meta import Base, UniqueMixin, multipolygon_str


class Catalog(UniqueMixin, Base):
    """SQLAlchemy table for representing a source `catalog`."""
    __tablename__ = 'catalog'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    # catalogpath = Column(String)
    # fitspath = Column(String)
    instrument = Column(String)
    footprint = Column(Geography(geometry_type='MULTIPOLYGON', srid=4326))
    meta = Column(MutableDict.as_mutable(HSTORE),
            nullable=False,
            default={},
            index=True)
    metajson = Column(MutableDict.as_mutable(JSON), default={})

    catalog_stars = relationship("CatalogStar", backref="catalog",
            passive_deletes=True)

    def __init__(self, name, instrument, footprints=None, **metadata):
        self.name = name
        self.instrument = instrument
        if footprints is not None:
            self.footprint = multipolygon_str(*footprints)
        else:
            self.footprint = None
        self.meta = dict(metadata)

    @classmethod
    def unique_hash(cls, name, instrument, footprints=None, **metadata):
        return "_".join((name, instrument))

    @classmethod
    def unique_filter(cls, query, name, instrument, footprints=None, **md):
        return query.filter(Catalog.name == name)\
            .filter(Catalog.instrument == instrument)

    def __repr__(self):
        return "<Catalog(%i)>" % self.id

    def delete(self, session):
        """Delete this catalog and cleanup orphan catalog stars and
        observations.
        """
        # ForeignKey constrains CASCADE on delete
        session.delete(self)
        session.commit()
        # Clean up any orphan CatalogStars
        session.query(CatalogStar).\
            filter(CatalogStar.catalog_id.is_(None)).\
            delete(synchronize_session=False)
        session.commit()
        # Clean up any orphan Observations
        session.query(Observation).\
            filter(Observation.catalog_star_id.is_(None)).\
            delete(synchronize_session=False)
        session.commit()


class CatalogStar(Base):
    """SQLAlchemy table for representing an object in a `catalog`.
    Observations are associated with the `observation` table.
    """
    __tablename__ = 'catalog_star'

    id = Column(Integer, primary_key=True)
    x = Column(Float)
    y = Column(Float)
    ra = Column(Float)
    dec = Column(Float)
    cfrac = Column(Float)
    
    # Reference catalog we belong to (Catalog defines relationship)
    catalog_id = Column(Integer,
            ForeignKey('catalog.id', ondelete='CASCADE'))

    # Reference the star we associate to
    star_id = Column(Integer, ForeignKey('star.id'))
    star = relationship("Star",
            foreign_keys="[CatalogStar.star_id]",
            backref=backref('catalog_stars', order_by=id))

    # Relationship to Observation
    observations = relationship("Observation", backref="catalog_star",
            passive_deletes=True)

    def __init__(self, x, y, ra, dec, cfrac):
        self.x = x
        self.y = y
        assert ra >= 0. and ra <= 360.
        assert dec >= -90. and dec <= 90.
        self.ra = ra
        self.dec = dec
        self.cfrac = cfrac

    def __repr__(self):
        return "<CatalogStar(%i)>" % self.id


class Observation(Base):
    """SQLAlchemy table for representing an `observation`."""
    __tablename__ = 'observation'

    id = Column(Integer, primary_key=True)
    mag = Column(Float)
    mag_err = Column(Float)

    bandpass_id = Column(Integer, ForeignKey('bandpass.id'))
    bandpass = relationship("Bandpass",
            foreign_keys="[Observation.bandpass_id]")

    catalog_star_id = Column(Integer,
            ForeignKey('catalog_star.id', ondelete="CASCADE"))

    def __init__(self, mag, mag_err):
        self.mag = mag
        self.mag_err = mag_err

    def __repr__(self):
        return "<Observation(%i)>" % self.id
