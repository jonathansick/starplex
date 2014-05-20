#!/usr/bin/env python
# encoding: utf-8
"""
Tools for designating zeropoint reference fields for intercal.
"""

from ..database import Catalog


def set_zeropoint_reference(session, catalog_name, instrument):
    """Set this field as a zeropoint reference so that solved zeropoints
    will be normalized against this field (and other reference fields).
    """
    catalog = session.query(Catalog).\
        filter(Catalog.name == catalog_name).\
        filter(Catalog.instrument == instrument).\
        one()
    meta = catalog.meta
    meta['intercal_reference'] = True
    catalog.meta = meta
    session.query(Catalog).\
        filter(Catalog.name == catalog_name).\
        filter(Catalog.instrument == instrument).\
        update({'meta': meta})


def unset_zeropoint_reference(session, catalog_name, instrument):
    """Revoke this catalog's status as a zeropoint reference."""
    catalog = session.query(Catalog).\
        filter(Catalog.name == catalog_name).\
        filter(Catalog.instrument == instrument).\
        one()
    meta = catalog.meta
    meta['intercal_reference'] = False
    catalog.meta = meta
    session.query(Catalog).\
        filter(Catalog.name == catalog_name).\
        filter(Catalog.instrument == instrument).\
        update({'meta': meta})
