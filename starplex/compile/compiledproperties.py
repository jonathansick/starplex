#!/usr/bin/env python
# encoding: utf-8
"""
Utilities for querying the compiled ``star`` table to ask what catalogs have
been compiled, what the aggregate footprint is, etc..
"""

from sqlalchemy import func

from ..database.models import CatalogStar, Catalog


def compiled_catalogs(session):
    """Returns a list of :class:``Catalog`` instances compiled into the
    ``Star`` table.
    """
    q = session.query(Catalog).distinct().\
            join(CatalogStar, CatalogStar.catalog_id == Catalog.id).\
            filter(CatalogStar.star != None)
    return q.all()


def compiled_footprint(session, catalogs):
    """Returns a Geoalchemy2 footprint polygon from the compiled footprint."""
    print catalogs
    agg_footprint = catalogs[0].footprint  # seed the aggregate footprint
    if len(catalogs) == 1:
        return agg_footprint
    for catalog in catalogs[1:]:
        # TODO I'm uneasy about whether I need to explicitly cast to
        # geometry in order to perform a union.
        # e.g. using func.ST_Transform(agg_footprint)
        agg_footprint = session.query(
                func.ST_Union(agg_footprint, catalog.footprint)
            ).one()
    return agg_footprint


def main():
    pass


if __name__ == '__main__':
    main()
