#!/usr/bin/env python
# encoding: utf-8
"""
Utilities for querying the compiled ``star`` table to ask what catalogs have
been compiled, what the aggregate footprint is, etc..
"""

from sqlalchemy import func
# from geoalchemy2 import Geography

from ..database import CatalogStar, Catalog


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
    if len(catalogs) == 1:
        agg_footprint = catalogs[0].footprint
    else:
        agg_footprint = session.query(
                func.ST_Union(
                    *[catalog.footprint for catalog in catalogs])).\
                one()[0]
    return agg_footprint


def main():
    pass


if __name__ == '__main__':
    main()
