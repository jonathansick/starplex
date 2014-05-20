#!/usr/bin/env python
# encoding: utf-8
"""
Prepare a network of fields for inter-field calibration.
"""

from ..database import Catalog, CatalogStar, Observation, IntercalEdge
from ..database import CatalogOverlaps


def prepare_network(session, bandpass):
    """Find the network of overlapping fields for this bandpass and prepare
    rows in the `intercal_edge` table.
    """
    catalogs = session.query(Catalog).\
        join(CatalogStar).\
        join(Observation).\
        filter(Observation.bandpass == bandpass).\
        group_by(Catalog.id)
    network_catalogs = session.query(Catalog.id).\
        join(CatalogStar).\
        join(Observation).\
        filter(Observation.bandpass == bandpass).\
        group_by(Catalog.id).\
        all()

    for catalog in catalogs:
        print catalog.name
        # Get overlapping fields
        overlaps = CatalogOverlaps(session, catalog)
        overlaps.query = overlaps.query.\
            filter(Catalog.id.in_(network_catalogs))
        overlap_count = overlaps.count
        print "overlap count", overlaps.count
        if overlap_count == 0:
            continue

        # For each overlap, ensure the edge is unique (or its inverse) and
        # add it to IntercalEdge
        for to_catalog in overlaps.catalogs:
            if IntercalEdge.edge_exists(session,
                                        catalog, to_catalog,
                                        bandpass):
                # skip this
                continue

            edge = IntercalEdge(catalog, to_catalog, bandpass, None, None)
            session.add(edge)
