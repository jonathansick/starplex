#!/usr/bin/env python
# encoding: utf-8
"""
Solve the network of inter-field zeropoint differences.
"""


import numpy as np
from scipy.optimize import basinhopping

from ..database import Catalog, IntercalEdge
from .cyobj import IntercalObjective


def solve_network(session, bandpass, prior_zp_delta_key='zp_offset',
                  use_cython=True):
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

    if use_cython:
        # Cython version
        obj = _prep_cy_objective(catalog_ids, network)
    else:
        # Python version
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
            update({'meta', meta})


def _prep_cy_objective(catalog_ids, network):
    """Constructs the cython objective function."""
    n_terms = network.shape[0]
    # Translates catalog id to index in the parameter space of objective func
    h = dict(zip(catalog_ids, range(len(catalog_ids))))
    from_index = np.empty(n_terms, dtype=int)
    to_index = np.empty(n_terms, dtype=int)
    delta = np.empty(n_terms, dtype=float)
    weight = np.empty(n_terms, dtype=float)
    for i in xrange(n_terms):
        from_index[i] = h[network[i]['from_id']]
        to_index[i] = h[network[i]['to_id']]
        delta[i] = network[i]['delta']
        weight[i] = 1. / network[i]['delta_err'] ** 2.

    objf = IntercalObjective(from_index, to_index, delta, weight, n_terms)
    return objf


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
