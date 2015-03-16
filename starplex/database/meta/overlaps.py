#!/usr/bin/env python
# encoding: utf-8
"""
Module for finding footprint overlaps.

Use :class:`FootprintOverlaps` to finding Catalogs that overlap an arbitrary
PostGIS multipolygon instance, or :class:`CatalogOverlaps` to find Catalogs
that overlap a specific Catalog.
"""

from sqlalchemy import func, not_

from ..observation import Catalog
# from .gistools import sq_meter_to_sq_degree


class OverlapBase(object):
    """Baseclass for catalog overlaps."""
    def __init__(self, session, main_footprint):
        super(OverlapBase, self).__init__()
        self._s = session
        self._main_footprint = main_footprint
        self.query = None
        self._overlapping_catalogs = None
        self._clips = None  # overlapping polygons, will be list
        self._areas = None  # areas of overlaps

    def _query_overlaps(self):
        """Execute the query, reset caches"""
        self._overlapping_catalogs = self.query.all()
        self._clips = None
        self._areas = None

    @property
    def count(self):
        """Number of overlaps"""
        if self._overlapping_catalogs is None:
            self._query_overlaps()
        return len(self._overlapping_catalogs)

    @property
    def catalogs(self):
        """List of overlapping catalogs"""
        if self._overlapping_catalogs is None:
            self._query_overlaps()
        return self._overlapping_catalogs

    @property
    def clips(self):
        """Polygons representing the intersecting areas between the principal
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
        if self._overlapping_catalogs is None:
            self._query_overlaps()
        if self._clips is None:
            self._clips = []
            for catalog in self._overlapping_catalogs:
                clip = self._s.\
                    query(func.ST_Intersection(
                          catalog.footprint, self._main_footprint)).\
                    one()
                self._clips.append(clip)
        return self._clips

    @property
    def areas(self):
        """Returns area of each overlap, as a list. Areas are given in
        square degrees.
        """
        if self._overlapping_catalogs is None:
            self._query_overlaps()
        if self._areas is None:
            self._areas = []
            for clip in self.clips:
                A = 0.
                for part in clip:
                    A += self._s.scalar(part.ST_Area(use_spheroid=False))
                # Since clips area created by ST_Intersection, they are
                # polygons in WK84 (Lat long), thus the areas should
                # automatically be in square degrees.
                self._areas.append(A)
        return self._areas

    @property
    def largest_overlapping_catalog(self):
        """Convenience accessor for Catalog entry with the largest overlap."""
        if self._overlapping_catalogs is None:
            self._query_overlaps()
        max_area = max(self.areas)
        max_index = self.areas.index(max_area)
        return self.catalogs[max_index]


class FootprintOverlaps(OverlapBase):
    """Queries catalogs that overlap the given footprint.

    The query can be customized by chaining to the ``query`` attributed. e.g.

       footprint_overlaps.query.filter(Catalog.instrument == my_instrument)

    Parameters
    ----------
    session :
        The active SQLAlchemy session instance.
    footprint :
        The multipolygon instance to find overlaps against.
    """
    def __init__(self, session, footprint, exclude=None):
        super(FootprintOverlaps, self).__init__(session, footprint)
        self._s = session
        self._footprint = footprint
        self._excluded_catalogs = exclude
        self.query = self._query_from_footprint()

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
        return q


class CatalogOverlaps(OverlapBase):
    """Queries catalogs that overlap a principal catalog.

    The query can be customized by chaining to the ``query`` attributed. e.g.

       catalog_overlaps.query.filter(Catalog.instrument == my_instrument)

    Parameters
    ----------
    session :
        The active SQLAlchemy session instance.
    catalog : :class:`starplex.Catalog` instance
        The :class:`Catalog` instance to find footprint overlaps against.
    """
    def __init__(self, session, catalog):
        super(CatalogOverlaps, self).__init__(session, catalog.footprint)
        self.main_catalog = catalog
        self.query = self._query_from_catalog(self.main_catalog)

    def _query_from_catalog(self, main_catalog):
        """Query for overlapping catalogs given a principal catalog.
        Returns a list of overlapping catalogs.
        """
        q = self._s.query(Catalog)\
            .filter(func.ST_Intersects(
                Catalog.footprint, self._main_footprint))\
            .filter(Catalog.id != main_catalog.id)
        return q
