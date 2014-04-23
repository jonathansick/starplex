#!/usr/bin/env python
# encoding: utf-8
"""
Compile the star catalog using basic PostGIS spatial joins.
"""

from astropy import log
from ..database import Catalog, CatalogStar, Observation, Star
from ..overlap import FootprintOverlaps
from ..database.meta.gistools import degree_to_meter
from .aggprops import compiled_footprint, compiled_catalogs
from .seed import seed_star_table


class SpatialJoiner(object):
    """Compiles the star catalog using basic PostGIS spatial joins."""
    def __init__(self, session):
        super(SpatialJoiner, self).__init__()
        self._s = session

    def seed_catalog(self, catalog, reset=True):
        """Initialize the star catalog using a seed observational catalog."""
        seed_star_table(self._s, catalog, reset=reset)

    def accrete_catalogs(self, r_tol, bandpass, instrument=None,
            no_new=False):
        """Accrete observational catalogs onto the star catalog given
        the query constraints on the catalogs to add.

        Parameters
        ----------
        r_tol : float
            Join search radius tolerance, in arcseconds.
        bandpass : :class:``starplex.database.Bandpass``
            The bandpass to be used to order the observed stars from brightest
            to faintest; this ordering matches bright stars first, to faint
            stars.
        instrument : str
            Constraint on the ``instrument`` field of catalogs to add.
        no_new : bool
            If ``True`` then stars from this catalog will be matched to stars
            in the ``Star`` table, but unmatched stars will not create new
            entries. This option can be useful for matching observed star
            catalogs to a reference catalog. Default is ``False``.
        """
        while True:
            catalogs = compiled_catalogs(self._s)
            footprint = compiled_footprint(self._s, catalogs)
            log.info("Accreted catalogs:\n{}".
                    format([str(c) for c in catalogs]))
            log.info("Total footprint {}".format(str(footprint)))
            overlaps = FootprintOverlaps(self._s, footprint,
                    exclude=catalogs)
            if instrument is not None:
                overlaps.query.filter(Catalog.instrument == instrument)
            if overlaps.count == 0:
                break
            next_catalog = overlaps.largest_overlapping_catalog
            log.info("Ingesting: {}".format(str(next_catalog)))
            self.join_catalog(next_catalog, r_tol, bandpass,
                    no_new=no_new)

    def join_catalog(self, catalog, r_tol, bandpass, no_new=False):
        """Join a specific observational catalog to the Star table.
        
        Parameters
        ----------
        catalog : 
            The :class:`starplex.database.models.Catalog` to join to the
            `Star` table.
        r_tol : float
            Join search radius in arcseconds.
        bandpass : float
            The :class:`starplex.database.models.Bandpass` to use to sort
            the stars being added by brightness.
        no_new : bool
            If ``True`` then stars from this catalog will be matched to stars
            in the ``Star`` table, but unmatched stars will not create new
            entries. This option can be useful for matching observed star
            catalogs to a reference catalog. Default is ``False``.
        """
        r_tol_m = degree_to_meter(r_tol / 3600.)
        matched_count = 0
        new_count = 0
        # Query catalog stars for this catalog, ordering brightnest to
        # faintest; that are not in the Star table already
        cstar_query = self._s.query(CatalogStar).\
            join(Observation, Observation.catalogstar_id == CatalogStar.id).\
            filter(CatalogStar.catalog == catalog).\
            filter(CatalogStar.star == None).\
            order_by(Observation.mag.desc())
        log.debug("cstar_query.count {0:d}".format(cstar_query.count()))
        for i, cstar in enumerate(cstar_query):
            # FIXME returns too many stars
            q = self._s.query(Star).\
                    filter(cstar.coord.ST_DWithin(
                        Star.coord, r_tol_m, False)).\
                    order_by(cstar.coord.ST_Distance(Star.coord))
            _ingested = False
            if i % 100 == 0:
                log.debug("{0:d}, {1:d}".format(i, q.count()))
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
                        log.debug("\t{}".format(str(matched_star)))
                        log.debug("\tcount of member catalogs: {0:d}".
                                format(star_catalogs_q.count()))
                        log.debug("\t{}".format(str(catalog_ids)))
                    if cstar.catalog_id not in catalog_ids:
                        # This star can be joined
                        self._add_to_star(cstar, matched_star)
                        matched_count += 1
                        _ingested = True
                        break
            if _ingested == False and not no_new:
                # No match; add this star directly
                self._add_new_star(cstar)
                new_count += 1
            if i % 100 == 0:
                log.debug("\tmatched %i new %i" % (matched_count, new_count))


    def _add_to_star(self, catalog_star, matched_star):
        """Add an observed catalog star to the matched star in the Star table.
        """
        catalog_star.star = matched_star

    def _add_new_star(self, catalog_star):
        """Insert a new catalog star into the Star table."""
        star = Star(catalog_star.coord)
        catalog_star.star = star
