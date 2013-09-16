#!/usr/bin/env python
# encoding: utf-8
"""
Utilities for working with Postgres/PostGIS.
"""


def point_str(ra, dec):
    """Convert an (RA,Dec) point into a PostGIS POINT definition (a ``str``).
    
    Parameters
    ----------
    ra : float
        Right ascension of point (degrees).
    dec : float
        Declination of point (degrees).
    """
    return 'POINT(%.10f %.10f)' % (ra, dec)


def main():
    pass


if __name__ == '__main__':
    main()
