#!/usr/bin/env python
# encoding: utf-8
"""
Temp script to migrate catalog metadata from HSTORE to JSON.
"""

from starplex.database import connect_to_server, Session
from starplex.database import Catalog


def main():
    connect_to_server("marvin", echo=True)
    session = Session()

    catalogs = session.query(Catalog)
    for catalog in catalogs:
        catalog.metajson = catalog.meta
    session.commit()


if __name__ == '__main__':
    main()
