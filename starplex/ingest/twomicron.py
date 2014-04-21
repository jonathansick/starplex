#!/usr/bin/env python
# encoding: utf-8
"""
Tools for ingesting the 2MASS near-infrared point-source catalog.
"""

import glob
import os
import gzip

import numpy as np
from astropy import log

from starplex.utils import Timer
from .ingestbase import init_catalog, add_observations


PSC_FORMAT = [('ra', float), ('dec', float),
        ('err_maj', float), ('err_min', float), ('err_ang', int),
        ('designation', object),
        ('j_m', float), ('j_cmsig', float), ('j_msigcom', float),
        ('j_snr', float), ('h_m', float), ('h_cmsig', float), 
        ('h_msigcom', float), ('h_snr', float), ('k_m', float),
        ('k_cmsig', float), ('k_msigcom', float), ('k_snr', float),
        ('ph_qual', object), ('rd_flg', object), ('bl_flg', object),
        ('cc_flg', object), ('ndet', object), ('prox', float), ('pxpa', int),
        ('pxcntr', int), ('gal_contam', int), ('mp_flg', int),
        ('pts_key', int), ('hemis', object), ('date date', object),
        ('scan', int), ('glon', float), ('glat', float), ('x_scan', float),
        ('jdate', float), ('j_psfchi', float), ('h_psfchi', float),
        ('k_psfchi', float), ('j_m_stdap', float), ('j_msig_stdap', float),
        ('h_m_stdap', float), ('h_msig_stdap', float), ('k_m_stdap', float),
        ('k_msig_stdap', float), ('dist_edge_ns', int), ('dist_edge_ew', int),
        ('dist_edge_flg', object), ('dup_src', int), ('use_src', int),
        ('a', object), ('dist_opt', float), ('phi_opt', int),
        ('b_m_opt', float), ('vr_m_opt', float), ('nopt_mchs', int),
        ('ext_key', int), ('scan_key', int), ('coadd_key', int),
        ('coadd', int)]


class TwoMassPSCIngest(object):
    """Pipeline for ingesting the 2MASS survey (or a subset).

    Example
    -------

    >>> from astropy import log
    >>> log.setLevel('INFO')
    >>> from starplex.database import connect, Session, create_all
    >>> from starplex.ingest import TwoMassPSCIngest
    >>> connect(user='jsick', name='starplex')
    >>> session = Session()
    >>> create_all()
    >>> tm_ingester = TwoMassPSCIngest(session, data_dir)
    >>> tm_ingester.ingest_region('2MASS_PSC', [9, 11], [37, 43])

    Parameters
    ----------
    session : 
        The SQLAlchemy session
    data_dir : str
        Directory where 2MASS data files are stored.
    """
    def __init__(self, session, data_dir):
        super(TwoMassPSCIngest, self).__init__()
        self._s = session
        self.data_dir = data_dir
        self._band_names = ["J_2MASS", "H_2MASS", "K_2MASS"]
        self._band_system = "Vega"

    def ingest_region(self, catalog_name, ra_span, dec_span):
        """Ingest stars from the 2MASS PSC that are found within the area
        defined by ``ra_span`` and ``dec_span``.

        Rows added to the Catalog, CatalogStar and Observation tables will be
        commited during this method.

        Parameters
        ----------
        catalog_name : str
            Name of the Catalog for the batch of stars. It is safe to
            import multiple regions onto the same named catalog, the entries
            will no be overwritten.
        ra_span : tuple
            Type of (ra_min, ra_max) spanning the region.
        dec_span : tuple
            Type of (dec_min, dec_max) spanning the region.
        """
        min_ra = min(ra_span)
        max_ra = max(ra_span)
        min_dec = min(dec_span)
        max_dec = max(dec_span)

        poly = [[min_ra, min_dec], [min_ra, max_dec],
                [max_ra, max_dec], [max_ra, min_dec]]

        init_catalog(self._s, "2MASS_PSC", "2MASS",
                self._band_names, self._band_system,
                footprint_polys=[poly],
                meta=None)

        paths = self._get_psc_paths()
        for p in paths:
            self._ingest_psc_file(p, min_ra, max_ra, min_dec, max_dec)

    def _get_psc_paths(self):
        """Return a list of paths to PSC file."""
        return glob.glob(os.path.join(self.data_dir, "psc_*.gz"))

    def _ingest_psc_file(self, p, min_ra, max_ra, min_dec, max_dec):
        """Ingest data from the PSC file it it is within bounding box."""
        # Parse the PSC file, producing a structured numpy array
        log.info("Searching in {}".format(p))
        cols = [0, 1, 6, 8, 10, 12, 14, 16]
        dt = [PSC_FORMAT[i] for i in cols]
        with Timer() as read_timer:
            with gzip.open(p) as f:
                data = np.genfromtxt(f,
                        dtype=np.dtype(dt),
                        usecols=cols,
                        delimiter='|')
        log.info("Read in {:.1f} seconds".format(read_timer.interval))
        with Timer() as sel_timer:
            sel = np.where((data['ra'] >= min_ra) & (data['ra'] <= max_ra)
                    & (data['dec'] >= min_dec) & (data['dec'] <= max_dec))[0]
            nstars = sel.shape[0]
        log.info("\tUsing {0:d} stars from {1} (in {2:.1f} s)".
                format(nstars, p, sel_timer.interval))
        if nstars == 0:
            return None

        z = np.zeros(nstars)
        ones = np.ones(nstars)

        with Timer() as insert_timer:
            mag_keys = ["%s_m" % k for k in ('j', 'h', 'k')]
            magerr_keys = ["%s_msigcom" % k for k in ('j', 'h', 'k')]
            mags = np.column_stack([data[k][sel] for k in mag_keys])
            mag_errs = np.column_stack([data[k][sel] for k in magerr_keys])
            add_observations(self._s, "2MASS_PSC", "2MASS",
                    self._band_names, self._band_system,
                    z, z,
                    data['ra'][sel], z, data['dec'][sel], z,
                    mags, mag_errs, ones)
        log.info("Inserted {0:d} stars in {1:.1f} seconds".
                format(nstars, insert_timer.interval))
