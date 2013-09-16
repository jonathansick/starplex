#!/usr/bin/env python
# encoding: utf-8
"""
Handles catalog ingest.
"""

from sqlalchemy.orm.exc import NoResultFound

from .database.models import Catalog, CatalogStar, Observation, Bandpass


class IngestBase(object):
    """Baseclass for ingesting an observed star catalog into Starplex.
    
    This class is meant to be inherited by the user's application.
    """
    def __init__(self, Session):
        super(IngestBase, self).__init__()
        self.session = Session()

    def set_catalog_metadata(self, catalogname, telescope, catalogpath,
            fitspath, band_defs):
        """Define the metadata for the observational catalog being inserted.
        
        Automatically calls :meth:`_set_band_list` to insert bandpass
        definitions in the database.
        """
        self.catalogname = catalogname
        self.telescope = telescope
        self.catalogpath = catalogpath
        self.fitspath = fitspath
        self._set_band_list(band_defs)
        self.catalog = Catalog(catalogname, telescope, catalogpath,
                fitspath)

    def _set_band_list(self, band_defs):
        """Define the sequence of bandpasses, corresponding to the order of
        magnitude measurements in the observed catalog.

        This method will search the database for existing bandpass records,
        and if matching bandpasses do not exist, add these bandpasses to the
        ``bandpass`` table.

        Parameters
        ----------
        band_defs : list
            List of :class:`BandpassDefinition` instances.
        """
        self.bands = [bdef.get_record(self.session) for bdef in band_defs]
        print "Bands:", self.bands

    def ingest(self, data):
        """Insert a record array of observations, creating catalog and
        catalog star entries with each observation."""
        nstars, nbands = data['mag'].shape
        catalog = Catalog(self.catalogname, self.catalogpath,
                self.fitspath, self.telescope)
        for i in xrange(nstars):
            cstar = CatalogStar(float(data['x'][i]),
                    float(data['y'][i]),
                    float(data['ra'][i]),
                    float(data['dec'][i]),
                    float(data['cfrac'][i]))
            for j, bp in zip(xrange(nbands), self.bands):
                if nbands == 0:
                    mag = float(data['mag'][i])
                    mag_err = float(data['mag_err'][i])
                else:
                    mag = float(data['mag'][i, j])
                    mag_err = float(data['mag_err'][i, j])
                obs = Observation(mag, mag_err)
                obs.bandpass = bp
                cstar.observations.append(obs)
            catalog.catalog_stars.append(cstar)
        self.session.add(catalog)
        self.session.commit()


class BandpassDefinition(object):
    """Handles insertion of bandpass records into the database.
    
    Parameters
    ----------
    name : str
        Name of this bandpass.
    """
    def __init__(self, name):
        super(BandpassDefinition, self).__init__()
        self.name = name

    def get_record(self, session):
        """Returns an existing database record for this bandpass, or inserts
        a new one.

        Parameters
        ----------
        session : :class:`Session`
            Instance of the :class:`Session`.
        """
        try: 
            bp = session.query(Bandpass).\
                    filter(Bandpass.name == self.name).one()
        except NoResultFound:
            bp = self._insert_bandpass(session)
        return bp

    def _insert_bandpass(self, session):
        """Insert this bandpass into the database."""
        bp = Bandpass(self.name)
        session.add(bp)
        return bp
