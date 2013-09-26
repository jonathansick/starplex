#!/usr/bin/env python
# encoding: utf-8
"""
Tools for ingesting the 2MASS near-infrared point-source catalog.
"""

import glob
import os
import gzip

from sqlalchemy.orm.exc import NoResultFound
import numpy as np
from ..database.models import Catalog, CatalogStar, Observation, Bandpass


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
        self._catalog = self._init_catalog()
        self._bandpasses = self._init_bandpasses()

    def _init_catalog(self):
        """Create a Catalog entry for 2MASS PSC, or return the existing
        catalog."""
        try: 
            catalog = self._s.query(Catalog).\
                    filter(Catalog.catalogname == 'twomicron_psc').one()
        except NoResultFound:
            # FIXME No footprint for 2MASS catalogs! Create post priori
            # from ingest range? Does it matter?
            catalog = Catalog("2MASS_PSC", None, None, "2MASS", None)
            self._s.add(catalog)
        return catalog

    def _init_bandpasses(self):
        """Create a list of Bandpass instances, ordered as JHKs bandpasses.
        """
        bandnames = ['J', 'H', 'Ks']
        bandpasses = []
        for name in bandnames:
            try: 
                bp = self._s.query(Bandpass).\
                        filter(Bandpass.name == name).one()
            except NoResultFound:
                bp = Bandpass(name)
                self._s.add(bp)
            bandpasses.append(bp)
        return bandpasses

    def ingest_in_range(self, ra_span, dec_span):
        """docstring for ingest"""
        min_ra = min(ra_span)
        max_ra = max(ra_span)
        min_dec = min(dec_span)
        max_dec = max(dec_span)

        paths = self._get_psc_paths()
        for p in paths:
            print "Ingesting %s" % p
            with gzip.open(p) as f:
                self._ingest_psc_file(f, min_ra, max_ra, min_dec, max_dec)

    def _get_psc_paths(self):
        """Return a list of paths to PSC file."""
        return glob.glob(os.path.join(self.data_dir, "psc_*.gz"))

    def _ingest_psc_file(self, f, min_ra, max_ra, min_dec, max_dec):
        """Ingest data from the PSC file it it is within bounding box."""
        # Parse the PSC file, producing a structured numpy array
        cols = [0, 1, 6, 8, 10, 12, 14, 16]
        dt = [PSC_FORMAT[i] for i in cols]
        data = np.genfromtxt(f, dtype=np.dtype(dt), delimiter='|',
                usecols=cols)
        sel = np.where((data['ra'] >= min_ra) & (data['ra'] <= max_ra)
                & (data['dec'] >= min_dec) & (data['dec'] <= max_dec))[0]
        nstars = sel.shape[0]
        print "\tUsing %i stars" % nstars
        if nstars == 0:
            return None

        # Create a CatalogStars and observations
        magkeys = ["%s_m" % k for k in ('j', 'h', 'k')]
        magerrkeys = ["%s_msigcom" % k for k in ('j', 'h', 'k')]
        zp = zip(self._bandpasses, magkeys, magerrkeys)
        for i in sel:
            row = data[i]
            if i % 1000 == 0:
                print "\t%.2f complete" % (i / float(nstars) * 100.)
            cstar = CatalogStar(None, None,
                    float(row['ra']), float(row['dec']),
                    None)  # ignore completeness
            for bp, magkey, magerrkey in zp:
                obs = Observation(float(row[magkey]), float(row[magerrkey]))
                obs.bandpass = bp
                cstar.observations.append(obs)
            self._catalog.catalog_stars.append(cstar)
        self._s.add(self._catalog)


def main():
    test_path = "/Users/jsick/Desktop/test_psc"
    pscingest = TwoMassPSCIngest(None, None)
    with open(test_path) as f:
        pscingest._ingest_psc_file(f, 0., 360., -90., 90.)


if __name__ == '__main__':
    main()
