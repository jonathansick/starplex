#!/usr/bin/env python
# encoding: utf-8
"""
Script to ingest 2MASS data into the Staplex database
"""

import argparse

from starplex.database.connection import connect
from starplex.publicdata.twomicron import TwoMassPSCIngest


def main():
    parser = argparse.ArgumentParser(
            description="Ingest 2MASS PSC into Starplex")
    parser.add_argument('data_dir', action='store',
            help="Directory with psc_*.gz files")
    parser.add_argument('--name', action='store', default='starplex',
            help="Database name")
    parser.add_argument('--user', action='store', default='starplex',
            help="Database user")
    parser.add_argument('--pw', action='store', default=None,
            help="Database password")
    parser.add_argument('--url', action='store', default='localhost',
            help="Database URL")
    parser.add_argument('--port', action='store', default=5432, type=int,
            help="Database port")
    parser.add_argument('--ra', action='store', nargs=2,
            default=[0., 360.], type=float,
            help="Min and max RA range")
    parser.add_argument('--dec', action='store', nargs=2,
            default=[-90., 90.], type=float,
            help="Min and max Dec range")
    args = parser.parse_args()

    engine, Session = connect(host=args.url, port=args.port, user=args.user,
            name=args.name, password=args.pw)
    session = Session()

    ingester = TwoMassPSCIngest(session, args.data_dir)
    ingester.ingest_in_range(args.ra, args.dec)
    session.commit()


if __name__ == '__main__':
    main()
