#!/usr/bin/env python
# encoding: utf-8
"""
Test inserting observation catalogs using the core api.
"""

import numpy as np

from starplex.database import connect, create_all, drop_all, Session
from starplex.database import Bandpass, Catalog, CatalogStar, Observation
from starplex.ingest import init_catalog, add_observations


class MockCatalog(object):
    """Create a Mock star catalog"""
    def __init__(self, catalog_name, instrument_name, band_names,
            ra_range, dec_range, n=10):
        super(MockCatalog, self).__init__()
        self.catalog_name = catalog_name
        self.instrument_name = instrument_name
        self.meta = {"fits_path": "test.fits"}
        self.x = np.random.uniform(low=0., high=1000., size=n)
        self.y = np.random.uniform(low=0., high=1000., size=n)
        self.cfrac = np.random.uniform(low=0.5, high=1., size=n)
        self.ra = np.random.uniform(low=min(ra_range),
                high=max(ra_range), size=n)
        self.dec = np.random.uniform(low=min(dec_range),
                high=max(dec_range), size=n)
        self.ra_err = np.random.randn(n) / 3600.
        self.dec_err = np.random.randn(n) / 3600.
        self.mag = np.array([np.random.uniform(12., 20, n)
            for band in band_names]).T
        self.mag_err = np.array([0.05 * np.random.randn(n)
            for band in band_names]).T
        self.band_sys = "Vega"
        self.bands = band_names
        self.footprints = [[[min(ra_range), min(dec_range)],
            [min(ra_range), max(dec_range)],
            [max(ra_range), max(dec_range)],
            [max(ra_range), min(dec_range)]]]
        self.n = n


class TestObservationsCoreIngest(object):

    mock = MockCatalog("test1", "myinstr", ['B', 'V'],
            [10.0, 10.5], [40.0, 41.])

    def setup_class(self):
        connect(user='jsick', name='starplex_test')
        self.session = Session()
        drop_all()
        create_all()

        init_catalog(self.session,
                self.mock.catalog_name, self.mock.instrument_name,
                self.mock.bands, self.mock.band_sys,
                self.mock.footprints,
                meta=self.mock.meta)
        add_observations(self.session,
                self.mock.catalog_name, self.mock.instrument_name,
                self.mock.bands, self.mock.band_sys, self.mock.x, self.mock.y,
                self.mock.ra, self.mock.ra_err,
                self.mock.dec, self.mock.dec_err,
                self.mock.mag, self.mock.mag_err, self.mock.cfrac)

    def teardown_class(self):
        # drop_all()
        # create_all()
        # self.session.commit()
        self.session.close()
    
    def test_band_insert(self):
        bp = self.session.query(Bandpass).\
                filter(Bandpass.name == self.mock.bands[0]).one()
        assert bp.name == self.mock.bands[0]
        assert bp.system == self.mock.band_sys

    def test_hstore_metadata_read(self):
        c = self.session.query(Catalog).\
                filter(Catalog.name == self.mock.catalog_name).one()
        assert c.meta['fits_path'] == self.mock.meta['fits_path']

    def test_count_catalog_stars(self):
        c = self.session.query(Catalog).\
                filter(Catalog.name == self.mock.catalog_name).one()
        assert self.mock.n == self.session.query(CatalogStar).\
                filter(CatalogStar.catalog == c).\
                count()
