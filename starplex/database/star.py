#!/usr/bin/env python
# encoding: utf-8
"""
ORM representation of star catalog tables that are reductions of observations.

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

from sqlalchemy import Column, Integer, Float
from geoalchemy2 import Geography
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

# from .meta import point_str, multipolygon_str
from .meta import Base


class Star(Base):
    """SQLAlchemy table for representing a `star`."""
    __tablename__ = 'star'

    id = Column(Integer, primary_key=True)
    coord = Column(Geography(geometry_type='POINT', srid=4326))

    def __init__(self, coord):
        self.coord = coord

    def __repr__(self):
        return "<Star(%i)>" % (self.id)


class Magnitude(Base):
    """SQLAlchemy table for representing an reduced magnitude, making up
    a datum of a star's SED.
    """
    __tablename__ = 'magnitude'

    id = Column(Integer, primary_key=True)
    mag = Column(Float)
    magerr = Column(Float)

    # Many to one on bandpass
    bandpass_id = Column(Integer, ForeignKey('bandpass.id'))
    bandpass = relationship("Bandpass",  # no need to backref
            foreign_keys="[Magnitude.bandpass_id]")

    # Many to one on star
    star_id = Column(Integer, ForeignKey('star.id'))
    star = relationship("Star",
            foreign_keys="[Magnitude.star_id]",
            backref=backref("magnitudes", order_by=id))

    def __init__(self):
        pass

    def __repr__(self):
        return "<Magnitude(%i)>" % self.id
