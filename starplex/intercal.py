#!/usr/bin/env python
# encoding: utf-8
"""
Pipeline for computing inter-catalog zeropoint calibrations by minimizing
field-to-field zeropoint differences.

First, set which fields should be treated as having 'true' (trusted)
zeropoints using the ``set_zeropoint_reference()`` function.

The pipeline is run with three successive functions

1. ``prepare_network()``
2. ``analyze_network()``
3. ``solve_network()``
"""

import numpy as np
import astropy.stats
from scipy.optimize import basinhopping

from sqlalchemy import func
from sqlalchemy.orm import aliased
from geoalchemy2.shape import to_shape

from .database import Catalog, CatalogStar, Bandpass, Observation, IntercalEdge
from .database import CatalogOverlaps


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


def analyze_network(session, bandpass, prior_zp_delta_key='zp_offset'):
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


def solve_network(session, bandpass, prior_zp_delta_key='zp_offset'):
    """Solve for ZP offsets to unify the photometry, respecting the
    zeropoint calibration of designated reference frames.

    The computed zeropoints are embedded in the each catalog's `intercal.zp`
    and `intercal.zp_err` metadata fields. The zeropoints are intended to
    be total, taking into account the prior_zp_delta_key field.
    """
    # Prepare the objective function
    q = session.query(IntercalEdge.from_id, IntercalEdge.to_id,
                      IntercalEdge.delta, IntercalEdge.delta_err).\
        filter(IntercalEdge.bandpass_id == bandpass.id)
    dt = [('from_id', int), ('to_id', int), ('delta', float),
          ('delta_err', float)]
    network = np.array(q.all(), dtype=np.dtype(dt))
    catalog_ids = np.unique(
        np.concatenate((network['from_id'], network['to_id']))).tolist()
    obj = Objective(catalog_ids, network)

    # Run the optimization
    z0 = 0.2 * np.random.randn(len(catalog_ids))
    result = basinhopping(obj, z0,
                          niter=100,
                          T=1.0e8,
                          stepsize=0.1,
                          minimizer_kwargs={'method': 'Nelder-Mead',
                                            'options': {'disp': True,
                                                        'maxiter': 1e9,
                                                        'maxfev': 1e6}},
                          take_step=None,
                          accept_test=None,
                          callback=None,
                          interval=10,  # rate at auto-updating stepsize
                          disp=True,
                          niter_success=None)
    # TODO change these to log statements
    print "RESULT MESSAGE", result.message
    print "RESULT NITER", result.nit
    print "RESULT FUNC", result.fun
    print "RESULT X", result.x
    zeropoints = result.x

    # Add the prior ZP to this result
    # and also get the list of zeropoint reference catalogs
    reference_catalog_ids = []
    reference_priors = []
    reference_solved_zps = []
    for i, catalog_id in enumerate(catalog_ids):
        result = session.query(Catalog.meta).\
            filter(Catalog.id == catalog_id).\
            one()
        meta = result.meta
        print catalog_id, meta

        try:
            prior_zp = meta[prior_zp_delta_key][str(bandpass.id)]['zp_delta']
        except:
            prior_zp = 0.
        print "prior_zp", prior_zp
        zeropoints[i] += prior_zp

        try:
            if meta['intercal_reference'] == True:
                print "Found intercal_reference"
                reference_catalog_ids.append(catalog_id)
                reference_priors.append(prior_zp)  # from prev try
                reference_solved_zps.append(zeropoints[i])
        except:
            pass

    print "reference_catalog_ids", reference_catalog_ids
    print "reference_priors", reference_priors
    print "reference_solved_zps", reference_solved_zps

    # Fit a zp normalization so that the ZP of the reference fields matches
    # that of the prior zp
    reference_priors = np.array(reference_priors)
    reference_solved_zps = np.array(reference_solved_zps)
    diff = reference_priors - reference_solved_zps
    corr = np.mean(diff)
    # FIXME Is this the right way to assess normalization uncertainty?
    # if len(diff) >= 5:
    #     corr_err = np.std(diff)
    # else:
    #     corr_err = 0.
    # Finally, normalize zeropoints
    zeropoints += corr

    print 'ZEROPOINTS', zeropoints
    print 'Correction', corr
    print 'Correction scatter', diff.std()
    print 'diffs', diff
    # Persist the intercal zeropoint to the Catalog's metadata
    for catalog_id, z in zip(catalog_ids, zeropoints):
        catalog = session.query(Catalog).\
            filter(Catalog.id == catalog_id).\
            one()
        meta = catalog.meta
        if 'intercal' not in meta:
            meta['intercal'] = {}
        meta['intercal'][str(bandpass.id)] = {"zp": float(z),
                                              "err": float(0.)}  # FIXME
        print meta
        catalog.meta = meta
        session.query(Catalog).\
            filter(Catalog.id == catalog_id).\
            update('meta', meta)


def _compute_zp_delta(session, edge, from_prior_zp, to_prior_zp):
    """Compute photometric zeropoint difference between two catalogs."""
    phot = _xmatch(session, edge)

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
    mean = _weighted_mean(filtered_delta, filtered_delta_err)

    # Do a bootstrap uncertainty analysis
    means = []
    for i in xrange(1000):
        idx = np.random.randint(low=0,
                                high=filtered_delta.shape[0] - 1,
                                size=delta.shape)
        m = _weighted_mean(filtered_delta[idx], filtered_delta_err[idx])
        means.append(m)
    return mean, np.std(np.array(means))


def _weighted_mean(delta, delta_err):
    mean = np.average(delta, weights=1. / delta_err ** 2.)
    return mean


def _xmatch(session, edge):
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

    overlap_polygon = _make_q3c_polygon(_get_overlap_polygon(session, edge))
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


def _get_overlap_polygon(session, edge):
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


def _make_q3c_polygon(poly):
    """Make a polygon in q3c (flattened) list format."""
    q3cpoly = poly.flatten().tolist()
    return q3cpoly


class Objective(object):
    """Inter-field zeropoint objective function."""
    def __init__(self, catalog_ids, network):
        super(Objective, self).__init__()
        self._net = network
        self._n_edges = len(self._net)
        self._hash = dict(zip(catalog_ids, range(len(catalog_ids))))

    def __call__(self, z):
        """Objective function call."""
        F = 0.
        for k in xrange(self._n_edges):
            i = self._hash[self._net[k]['from_id']]
            j = self._hash[self._net[k]['to_id']]
            F += ((self._net[k]['delta'] + z[i] - z[j])
                  / self._net[k]['delta_err'] ** 2) ** 2.
        return F
