#!/usr/bin/env python
# encoding: utf-8
"""
Module for finding footprint overlaps.
"""

from sqlalchemy import func

from .database.models import Catalog


class CatalogOverlaps(object):
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
    def __init__(self, session, catalog, telescope):
        super(CatalogOverlaps, self).__init__()
        self._s = session
        self.main_catalog = catalog
        self.telescope = telescope
        self._overlapping_catalogs = self._query_from_catalog(self.main_catalog)
    
    def _query_from_catalog(self, main_catalog):
        """Query for overlapping catalogs given a principle catalog.
        Returns a list of overlapping catalogs.
        """
        overlaps = self._s.query(Catalog)\
            .filter(func.ST_Intersects(
                Catalog.footprint, main_catalog.footprint))\
            .filter(Catalog.id != main_catalog.id)\
            .filter(Catalog.telescope == self.telescope)\
            .all()
        return overlaps

    @property
    def count(self):
        """Number of overlaps"""
        return len(self._overlapping_catalogs)

    @property
    def catalogs(self):
        """List of overlapping catalogs"""
        return self._overlapping_catalogs


def main():
    pass


if __name__ == '__main__':
    main()
