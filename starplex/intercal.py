#!/usr/bin/env python
# encoding: utf-8
"""
Pipeline for computing inter-catalog zeropoint calibrations by minimizing
field-to-field zeropoint differences.
"""

import numpy as np
import astropy.stats

from sqlalchemy import func
from sqlalchemy.orm import aliased
from geoalchemy2.shape import to_shape

from .database import Catalog, CatalogStar, Bandpass, Observation, IntercalEdge
from .database import CatalogOverlaps


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


def compute_network(session, bandpass, prior_zp_delta_key='zp_offset'):
    """Compute zeropoint offsets for all pairs of fields (edges in the graph).

    .. todo:: Add a way to paginating so multiple processors can work on
       this task in separate sessions.
    """
    from_cat = aliased(Catalog)
    to_cat = aliased(Catalog)
    q = session.query(IntercalEdge, from_cat, to_cat).\
        join(from_cat, IntercalEdge.from_id == from_cat.id).\
        join(to_cat, IntercalEdge.to_id == to_cat.id)
    for edge, from_cat, to_cat in q:
        from_meta = from_cat.meta
        to_meta = to_cat.meta
        # Get prior zp correction estimates
        try:
            from_prior_zp \
                = from_meta[
                    prior_zp_delta_key][str(edge.bandpass_id)]['zp_delta']
        except:
            from_prior_zp = 0.
        try:
            to_prior_zp \
                = to_meta[
                    prior_zp_delta_key][str(edge.bandpass_id)]['zp_delta']
        except:
            to_prior_zp = 0.
        print "Prior ZPs: %.2e %.2e" % (from_prior_zp, to_prior_zp)
        delta, delta_err = _compute_zp_delta(session, edge,
                                             from_prior_zp, to_prior_zp)
        print "Deltas", delta, delta_err
        # Update the edge
        edge.delta = float(delta)
        edge.delta_err = float(delta_err)


def compute_zp_delta(session, edge, from_prior_zp, to_prior_zp):
    """Compute photometric zeropoint difference between two catalogs."""
    phot = xmatch(session, edge)

    # Apply prior ZP offsets
    phot['from_mag'] += from_prior_zp
    phot['to_mag'] += to_prior_zp

    # Compute zeropoint shift
    delta = phot['from_mag'] - phot['to_mag']
    delta_err = np.hypot(phot['from_mag_err'], phot['to_mag_err'])
    filtered_phot = astropy.stats.funcs.sigma_clip(delta, sig=3)
    filtered_delta = filtered_phot.data[~filtered_phot.mask]
    filtered_delta_err = delta_err[~filtered_phot.mask]
    good = np.where((np.isfinite(filtered_delta) == True)
                    & (np.isfinite(filtered_delta_err) == True))[0]
    filtered_delta = filtered_delta[good]
    filtered_delta_err = filtered_delta_err[good]
    mean = weighted_mean(filtered_delta, filtered_delta_err)

    # Do a bootstrap uncertainty analysis
    means = []
    for i in xrange(1000):
        idx = np.random.randint(low=0,
                                high=filtered_delta.shape[0] - 1,
                                size=delta.shape)
        m = weighted_mean(filtered_delta[idx], filtered_delta_err[idx])
        means.append(m)
    return mean, np.std(np.array(means))


def weighted_mean(delta, delta_err):
    mean = np.average(delta, weights=1. / delta_err ** 2.)
    return mean


def xmatch(session, edge):
    """Join photometric measurements of two overlapping catalogs in the
    given bandpass.
    """
    from_cstar = aliased(CatalogStar)
    to_cstar = aliased(CatalogStar)
    from_cat = aliased(Catalog)
    to_cat = aliased(Catalog)
    from_obs = aliased(Observation)
    to_obs = aliased(Observation)
    from_bp = aliased(Bandpass)
    to_bp = aliased(Bandpass)

    overlap_polygon = make_q3c_polygon(get_overlap_polygon(session, edge))
    q = session.query(from_obs.mag,
                      from_obs.mag_err,
                      to_obs.mag,
                      to_obs.mag_err).\
        join(to_cstar, to_cat.catalog_stars).\
        join(from_cstar, from_cat.catalog_stars).\
        filter(to_cat.id == edge.to_id).\
        filter(from_cat.id == edge.from_id).\
        filter(func.q3c_poly_query(to_cstar.ra,
                                   to_cstar.dec,
                                   overlap_polygon)).\
        filter(func.q3c_join(to_cstar.ra,
                             to_cstar.dec,
                             from_cstar.ra,
                             from_cstar.dec,
                             1. / 3600.)).\
        join(from_obs, from_cstar.observations).\
        join(to_obs, to_cstar.observations).\
        join(from_bp, from_obs.bandpass).\
        filter(from_bp.id == edge.bandpass_id).\
        join(to_bp, to_obs.bandpass).\
        filter(to_bp.id == edge.bandpass_id)
    dt = np.dtype([('from_mag', float),
                   ('from_mag_err', float),
                   ('to_mag', float),
                   ('to_mag_err', float)])
    data = np.array(q.all(), np.dtype(dt))
    return data


def get_overlap_polygon(session, edge):
    """Get polygon of the overlap area of this graph edge."""
    principal_catalog = session.query(Catalog).\
        filter(Catalog.id == edge.from_id).\
        one()
    cat_overlaps = CatalogOverlaps(session, principal_catalog)
    cat_overlaps.query = cat_overlaps.query.filter(Catalog.id == edge.to_id)
    part = cat_overlaps.clips[0][0]  # to get just one polygon
    s = to_shape(part)
    x, y = s.exterior.xy
    poly = np.array(zip(x, y))
    return poly


def make_q3c_polygon(poly):
    """Make a polygon in q3c (flattened) list format."""
    # TODO refactor this into starplex
    q3cpoly = poly.flatten().tolist()
    return q3cpoly
