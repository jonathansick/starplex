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


def multipolygon_str(*polygons):
    """Convert polygons with (RA,Dec) vertices into a PostGIS MULITPOLYGON
    defininition.

    Note that this function automatically closes each polygon (the first vertex
    is the same as the last).

    e.g.::
    
        MULTIPOLYGON(((2.25 0,1.25 1,1.25 -1,2.25 0)),
        ((1 -1,1 1,0 0,1 -1)))
    """
    poly_strs = []
    for polygon in polygons:
        v_strs = ["%.10f %.10f" % tuple(v) for v in polygon]
        v_strs.append(v_strs[0])  # auto close the polygon
        poly_str = "(( %s ))" % ",".join(v_strs)
        poly_strs.append(poly_str)
    return 'MULTIPOLYGON(%s)' % ",".join(poly_strs)


def main():
    pass


if __name__ == '__main__':
    main()
