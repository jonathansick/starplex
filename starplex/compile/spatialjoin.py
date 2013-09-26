#!/usr/bin/env python
# encoding: utf-8
"""
Compile the star catalog using basic PostGIS spatial joins.
"""

from ..database.models import Catalog, CatalogStar, Observation, Star
from ..overlap import FootprintOverlaps
from ..database.tools import degree_to_meter
from .aggprops import compiled_footprint, compiled_catalogs
from . import seed


class SpatialJoiner(object):
    """Compiles the star catalog using basic PostGIS spatial joins."""
    def __init__(self, session):
        super(SpatialJoiner, self).__init__()
        self._s = session

    def seed_catalog(self, catalog, reset=True):
        """Initialize the star catalog using a seed observational catalog."""
        seed.seed_star_table(self._s, catalog, reset=reset)

    def accrete_catalogs(self, r_tol, bandpass, query=None, telescope=None):
        """Accrete observational catalogs onto the star catalog given
        the query constraints on the catalogs to add.

        Parameters
        ----------
        r_tol : float
            Join search radius tolerance, in arcseconds.
        bandpass : :class:``starplex.database.models.Bandpass``
            The bandpass to be used to order the observed stars from brightest
            to faintest; this ordering matches bright stars first, to faint
            stars.
        query : 
            An SQLAlchemy query statement against the catalog table. If not
            provided, a query will be built using other constraints.
        telescope : str
            Constraint on the ``telescope`` field of catalogs to add.
        """
        r_tol_m = degree_to_meter(r_tol / 3600.)
        while True:
            catalogs = compiled_catalogs(self._s)
            footprint = compiled_footprint(self._s, catalogs)
            print "Accreted catalogs", catalogs
            print "Total footprint", footprint
            overlaps = FootprintOverlaps(self._s, footprint,
                    exclude=catalogs,
                    telescope=telescope)
            # TODO use ``query`` to customize the query
            if overlaps.count == 0:
                break
            next_catalog = overlaps.largest_overlapping_catalog
            print "Ingesting:", next_catalog
            self._ingest_catalog(next_catalog, r_tol_m, bandpass)

    def _ingest_catalog(self, catalog, r_tol_m, bandpass):
        """Join an observational catalog to the Star table"""
        matched_count = 0
        new_count = 0
        # Query catalog stars for this catalog, ordering brightnest to
        # faintest; that are not in the Star table already
        cstar_query = self._s.query(CatalogStar).\
            join(Observation, Observation.catalogstar_id == CatalogStar.id).\
            filter(CatalogStar.catalog == catalog).\
            filter(CatalogStar.star == None).\
            order_by(Observation.mag.desc())
        print "cstar_query.count", cstar_query.count()
        for i, cstar in enumerate(cstar_query):
            # FIXME Subquery: for a given star, what catalogs observed it?
            # star_catalogs_subq = self._s.query(Catalog.id).\
            #         join(CatalogStar, CatalogStar.catalog_id == Catalog.id).\
            #         join(Star, Star.id == CatalogStar.star_id).\
            #         correlate(Star).subquery()
            # Problem is I can't get .in_ on many-to-one relationship
            # filter(~cstar.catalog.in_(star_catalogs_subq)).
            # thus I'll manually iterate through spatial match to ensure
            # star is not already included in the catalog
            # FIXME returns too many stars
            q = self._s.query(Star).\
                    filter(cstar.coord.ST_DWithin(
                        Star.coord, r_tol_m, False)).\
                    order_by(cstar.coord.ST_Distance(Star.coord))
            _ingested = False
            if i % 100 == 0:
                print i, q.count()
            if q.count() > 0:
                for matched_star in q:
                    # Check this star is not already included in this catalog
                    # FIXME this query seems wrong?
                    star_catalogs_q = self._s.query(Catalog.id).\
                            join(CatalogStar,
                                    CatalogStar.catalog_id == Catalog.id).\
                            join(Star,
                                    Star.id == CatalogStar.star_id).\
                            filter(matched_star.id == Star.id)
                    # unpack to a list of Catalog ids
                    catalog_ids = [x[0] for x in star_catalogs_q.all()]
                    if i % 100 == 0:
                        print "\t", matched_star
                        print "\tcount of member catalogs", star_catalogs_q.count()
                        print "\t", catalog_ids
                    if cstar.catalog_id not in catalog_ids:
                        # This star can be joined
                        self._add_to_star(cstar, matched_star)
                        matched_count += 1
                        _ingested = True
                        break
            if _ingested == False:
                # No match; add this star directly
                self._add_new_star(cstar)
                new_count += 1
            if i % 100 == 0:
                print "\tmatched %i new %i" % (matched_count, new_count)


    def _add_to_star(self, catalog_star, matched_star):
        """Add an observed catalog star to the matched star in the Star table.
        """
        catalog_star.star = matched_star

    def _add_new_star(self, catalog_star):
        """Insert a new catalog star into the Star table."""
        star = Star(catalog_star.coord)
        catalog_star.star = star


def main():
    pass


if __name__ == '__main__':
    main()
