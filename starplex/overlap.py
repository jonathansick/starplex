#!/usr/bin/env python
# encoding: utf-8
"""
Module for finding footprint overlaps.
"""

from sqlalchemy import func
from sqlalchemy import not_

from .database import Catalog
from .database.meta.gistools import sq_meter_to_sq_degree


class OverlapBase(object):
    """Baseclass for catalog overlaps."""
    def __init__(self, session, main_footprint):
        super(OverlapBase, self).__init__()
        self._s = session
        self._main_footprint = main_footprint
        self._overlapping_catalogs = []
        self._clips = None  # overlapping polygons, will be list
        self._areas = None  # areas of overlaps
        
    @property
    def count(self):
        """Number of overlaps"""
        return len(self._overlapping_catalogs)

    @property
    def catalogs(self):
        """List of overlapping catalogs"""
        return self._overlapping_catalogs

    @property
    def clips(self):
        """Polygons representing the intersecting areas between the princpiple
        catalog and all overlapping catalogs.
        
        Returns a list of tuples of :class:``WKBElement`` for each
        intersection, corresponding to the list of overlapping catalogs.
        That is, each overlap has a tuple of :class:``WKBElement`` since
        an overlap can have multiple polygon parts.

        The clipping polygons are cached.

        To get the WKT representation of these::

        >> for clip in overlaps.clips:
        >>     for part in clip:
        >>         print session.query(func.ST_AsText(part)).one()
        """
        if self._clips is None:
            self._clips = []
            for catalog in self._overlapping_catalogs:
                clip = self._s.\
                        query(func.ST_Intersection(
                            catalog.footprint, self._main_footprint))\
                        .one()
                self._clips.append(clip)
        return self._clips

    @property
    def areas(self):
        """Returns area of each overlap, as a list. Areas are given in
        square degrees.
        """
        if self._areas is None:
            self._areas = []
            for clip in self.clips:
                A = 0.
                for part in clip:
                    A += self._s.scalar(part.ST_Area(use_spheroid=False))
                # A is in square meters, given a Geography type
                # covert to square degrees
                self._areas.append(sq_meter_to_sq_degree(A))
        return self._areas

    @property
    def largest_overlapping_catalog(self):
        """Convenience accessor for Catalog entry with the largest overlap."""
        max_area = max(self.areas)
        max_index = self.areas.index(max_area)
        return self.catalogs[max_index]


class FootprintOverlaps(OverlapBase):
    """Queries catalogs that overlap the given footprint.
    
    Parameters
    ----------
    session :
        The active SQLAlchemy session instance.
    footprint : 
        The multipolygon instance to find overlaps against.
    telescope : str
        Value of ``telescope`` field in ``catalog`` table rows to query.
    """
    def __init__(self, session, footprint, exclude=None, telescope=None):
        super(FootprintOverlaps, self).__init__(session, footprint)
        self._s = session
        self._footprint = footprint
        self.telescope = telescope
        self._excluded_catalogs = exclude
        self._overlapping_catalogs = self._query_from_footprint()

    def _query_from_footprint(self):
        """Query for overlapping catalogs given a footprint, and possibly
        an exclusion of catalogs.
        """
        q = self._s.query(Catalog)\
            .filter(func.ST_Intersects(
                Catalog.footprint, self._main_footprint))
        if self._excluded_catalogs is not None:
            catalog_ids = [c.id for c in self._excluded_catalogs]
            q = q.filter(not_(Catalog.id.in_(catalog_ids)))
        if self.telescope is not None:
            q = q.filter(Catalog.telescope == self.telescope)
        overlaps = q.all()
        return overlaps


class CatalogOverlaps(OverlapBase):
    """Queries catalogs that overlap a principle catalog.
    
    Parameters
    ----------
    session :
        The active SQLAlchemy session instance.
    catalog : :class:`starplex.database.models.Catalog` instance
        The :class:`Catalog` instance to find footprint overlaps against.
    telescope : str
        Value of ``telescope`` field in ``catalog`` table rows to query.
    """
    def __init__(self, session, catalog, telescope=None):
        super(CatalogOverlaps, self).__init__(session, catalog.footprint)
        self.main_catalog = catalog
        self.telescope = telescope
        self._overlapping_catalogs = self._query_from_catalog(self.main_catalog)

    def _query_from_catalog(self, main_catalog):
        """Query for overlapping catalogs given a principle catalog.
        Returns a list of overlapping catalogs.
        """
        q = self._s.query(Catalog)\
            .filter(func.ST_Intersects(
                Catalog.footprint, self._main_footprint))\
            .filter(Catalog.id != main_catalog.id)
        if self.telescope is not None:
            q = q.filter(Catalog.telescope == self.telescope)
        overlaps = q.all()
        return overlaps


def main():
    pass


if __name__ == '__main__':
    main()
