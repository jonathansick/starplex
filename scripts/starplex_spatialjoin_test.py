#!/usr/bin/env python
# encoding: utf-8
"""
This script tries to run a simple spatial join of two WIRCam catalogs.
Requires the WIRCam data to be ingested (not included yet, sorry).
"""

from sqlalchemy import func

from starplex.database.connection import connect
from starplex.database.models import Catalog
from starplex.overlap import CatalogOverlaps


def main():
    engine, Session = connect(host="localhost", port=5432, user='jsick',
            name='jsick')
    session = Session()

    main_catalog = session.query(Catalog).filter(
            Catalog.catalogname == "M31-1"
            ).one()
    print main_catalog
    overlaps = CatalogOverlaps(session, main_catalog, "wircam")
    print overlaps.count
    print overlaps.catalogs
    print overlaps.clips
    for clip in overlaps.clips:
        print type(clip)
        print type(clip[0])
        print session.query(func.ST_AsText(clip[0])).one()
    print overlaps.areas
    print overlaps.largest_overlapping_catalog


if __name__ == '__main__':
    main()
