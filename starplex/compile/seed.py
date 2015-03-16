#!/usr/bin/env python
# encoding: utf-8
"""
Tools for seeding the star table with an initial observational catalog.
"""

from ..database import Star, CatalogStar


def seed_star_table(session, obs_catalog, reset=False):
    """Seed the star table with an observed catalog."""
    if reset:
        reset_star_table(session, obs_catalog)
    q = session.query(CatalogStar)\
        .filter(CatalogStar.catalog == obs_catalog)\
        .filter(CatalogStar.star == None)  # NOQA FIXME conditional?
    for catalog_star in q:
        star = Star(catalog_star.coord)
        catalog_star.star = star


def reset_star_table(session, obs_catalog):
    """Delete existing stars."""
    q = session.query(CatalogStar)\
        .filter(CatalogStar.catalog == obs_catalog)\
        .filter(CatalogStar.star != None)  # NOQA FIXME conditional?
    for catalogstar in q:
        session.delete(catalogstar.star)
    session.query(Star).delete()
