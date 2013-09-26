#!/usr/bin/env python
# encoding: utf-8
"""
This script tries to run a simple spatial join of two WIRCam catalogs.
Requires the WIRCam data to be ingested (not included yet, sorry).
"""

from sqlalchemy import func

from starplex.database.connection import connect
from starplex.database.models import Catalog, Bandpass
from starplex.overlap import CatalogOverlaps
from starplex.compile import spatialjoin
from starplex.compile.aggprops import compiled_catalogs
from starplex.compile.aggprops import compiled_footprint


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

    print compiled_catalogs(session)
    print compiled_footprint(session, session.query(Catalog).all())

    bandpass = session.query(Bandpass).\
            filter(Bandpass.name == "Ks").\
            one()

    joiner = spatialjoin.SpatialJoiner(session)
    # joiner.seed_catalog(main_catalog)
    joiner.accrete_catalogs(1., bandpass)
    session.commit()

    # TODO test compilation then do a rollback.



if __name__ == '__main__':
    main()
