#!/usr/bin/env python
# encoding: utf-8
"""
Handles catalog ingest.
"""

from astropy.wcs import WCS

from .database import Catalog, CatalogStar, Observation, Bandpass


class IngestBase(object):
    """Baseclass for ingesting an observed star catalog into Starplex.
    
    This class is meant to be inherited by the user's application.
    """
    def __init__(self, Session):
        super(IngestBase, self).__init__()
        self.session = Session()

    def set_catalog_metadata(self, catalogname, telescope, catalogpath,
            fitspath, band_names, band_system):
        """Define the metadata for the observational catalog being inserted.
        """
        self.catalogname = catalogname
        self.telescope = telescope
        self.catalogpath = catalogpath
        self.fitspath = fitspath
        self.band_system = band_system
        self.band_names = list(band_names)
        self.footprints = self.extract_footprint_polygons()
        self.catalog = Catalog(catalogname, catalogpath, fitspath, telescope,
                self.footprints)

    def extract_footprint_polygons(self):
        """Must be overridden by the user to yield a list of footprint
        polygons for all extensions in the FITS image.
        
        Once a ``astropy.io.fits`` header is extracted, the user may pass it
        to the :meth:`make_footprint_polygon` method to get a footprint
        polygon.
        """
        pass

    def make_polygon(self, header):
        """Get footprint polygons, with (RA,Dec) vertices, from the given
        extensions in the in the reference FITS file.
        """
        wcs = WCS(header)
        fp = wcs.calcFootprint().tolist()
        return fp

    def ingest(self, data):
        """Insert a record array of observations, creating catalog and
        catalog star entries with each observation."""
        nstars, nbands = data['mag'].shape
        for i in xrange(nstars):
            cstar = CatalogStar(float(data['x'][i]),
                    float(data['y'][i]),
                    float(data['ra'][i]),
                    float(data['dec'][i]),
                    float(data['cfrac'][i]))
            for j, bandname in zip(xrange(nbands), self.band_names):
                bp = Bandpass.as_unique(self.session,
                        bandname, self.band_system)
                if nbands == 0:
                    mag = float(data['mag'][i])
                    mag_err = float(data['mag_err'][i])
                else:
                    mag = float(data['mag'][i, j])
                    mag_err = float(data['mag_err'][i, j])
                obs = Observation(mag, mag_err)
                obs.bandpass = bp
                cstar.observations.append(obs)
            self.catalog.catalog_stars.append(cstar)
        self.session.add(self.catalog)
        self.session.commit()
