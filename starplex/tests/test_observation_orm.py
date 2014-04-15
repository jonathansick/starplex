#!/usr/bin/env python
# encoding: utf-8
"""
Test working with observation catalogs in the ORM.
"""

import numpy as np

from starplex.database import engine, connect, create_all, drop_all, Session
from starplex.database import Bandpass, Catalog, CatalogStar, Observation


class MockCatalog(object):
    """Create a Mock star catalog"""
    def __init__(self, catalog_name, instrument_name, band_names,
            ra_range, dec_range, n=10):
        super(MockCatalog, self).__init__()
        self.catalog_name = catalog_name
        self.instrument_name = instrument_name
        self.fits_path = "test.fits"
        self.ra = np.random.uniform(low=min(ra_range),
                high=max(ra_range), size=n)
        self.dec = np.random.uniform(low=min(dec_range),
                high=max(dec_range), size=n)
        self.mags = [np.random.uniform(12., 20, n) for band in band_names]
        self.band_sys = "Vega"
        self.bands = band_names
        self.n = n


class TestObservationsORM(object):

    mock_dataset = MockCatalog("test1", "myinstr", ['B', 'V'],
            [10.0, 10.5], [40.0, 41.])

    def setup_class(self):
        print "engine init", engine
        connect(user='jsick', name='starplex_test')
        print "engine after connect", engine
        self.session = Session()
        drop_all()
        create_all()

        catalog = Catalog(self.mock_dataset.catalog_name,
                self.mock_dataset.instrument_name,
                None,
                fits_path=self.mock_dataset.fits_path)
        for i in xrange(self.mock_dataset.n):
            cstar = CatalogStar(0., 0., self.mock_dataset.ra[i],
                    self.mock_dataset.dec[i], 0., 0., 1.)
            for j, bandname in enumerate(self.mock_dataset.bands):
                bp = Bandpass.as_unique(self.session, bandname,
                        self.mock_dataset.band_sys)
                obs = Observation(self.mock_dataset.mags[j][i], 0.)
                obs.bandpass = bp
                cstar.observations.append(obs)
            catalog.catalog_stars.append(cstar)
        self.session.add(catalog)

    def teardown_class(self):
        self.session.rollback()
        self.session.close()
    
    def test_band_insert(self):
        bp = self.session.query(Bandpass).\
                filter(Bandpass.name == self.mock_dataset.bands[0]).one()
        print bp
        print bp.name, bp.system
        assert bp.name == self.mock_dataset.bands[0]
        assert bp.system == self.mock_dataset.band_sys

    def test_hstore_metadata_read(self):
        c = self.session.query(Catalog).\
                filter(Catalog.name == self.mock_dataset.catalog_name).one()
        assert c.meta['fits_path'] == self.mock_dataset.fits_path
