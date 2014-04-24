#!/usr/bin/env python
# encoding: utf-8
"""
Script to ingest 2MASS data into the Staplex database
"""

import argparse

from astropy import log
from starplex.database import connect, Session, create_all
from starplex.ingest import TwoMassPSCIngest


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

    log.setLevel('INFO')
    connect(user=args.user, name=args.name)
    session = Session()
    create_all()
    tm_ingester = TwoMassPSCIngest(session, args.data_dir)
    tm_ingester.ingest_region('2MASS_PSC', [7.5, 17], [36, 47])


if __name__ == '__main__':
    main()
