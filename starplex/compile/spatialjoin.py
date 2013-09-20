#!/usr/bin/env python
# encoding: utf-8
"""
Compile the star catalog using basic PostGIS spatial joins.
"""

from . import seed


class SpatialJoiner(object):
    """Compiles the star catalog using basic PostGIS spatial joins."""
    def __init__(self, session):
        super(SpatialJoiner, self).__init__()
        self._s = session

    def seed_catalog(self, catalog, reset=True):
        """Initialize the star catalog using a seed observational catalog."""
        seed.seed_star_table(self._s, catalog, reset=reset)

    def accrete_catalogs(self, r_tol, query=None, telescope=None):
        """Accrete observational catalogs onto the star catalog given
        the query constraints on the catalogs to add.

        Parameters
        ----------
        r_tol : float
            Join search radius tolerance, in arcseconds.
        query : 
            An SQLAlchemy query statement against the catalog table. If not
            provided, a query will be built using other constraints.
        telescope : str
            Constraint on the ``telescope`` field of catalogs to add.
        """
        pass


def main():
    pass


if __name__ == '__main__':
    main()
