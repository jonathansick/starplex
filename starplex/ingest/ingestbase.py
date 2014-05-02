#!/usr/bin/env python
# encoding: utf-8
"""
Handles catalog ingest.
"""

from astropy.wcs import WCS
from astropy import log

from sqlalchemy.sql import func, select
from sqlalchemy import Integer

from ..database import Catalog, CatalogStar, Observation, Bandpass
from ..database.meta import point_str


def init_catalog(session, name, instrument, band_names, band_system,
        footprint_polys=None, meta=None):
    """Insert a new observational catalog. Follow this up with
    insert_observations.

    Parameters
    ----------
    session : ``Session``
        The session instance.
    name : str
        Name of the Catalog.
    instrument : str
        Name of the instrument.
    band_names : list
        List of bandpass names
    band_system : str
        Name of the photometric system.
    footprint_polys : list
        List of footprint polyons of the catalogs footprint on the sky.
    meta : dict
        Metadata passed to the Catalog's `meta` HSTORE field.
    """
    if not meta:
        meta = {}
    # Pre-insert the catalog and bandpass
    catalog = Catalog.as_unique(session, name, instrument,
        footprints=footprint_polys, **meta)
    session.add(catalog)
    # Ensure the bandpass exists
    for n in band_names:
        bp = Bandpass.as_unique(session, n, band_system)
        session.add(bp)
    session.commit()


def add_observations(session, name, instrument, band_names, band_system,
        x, y, ra, ra_err, dec, dec_err, mag, mag_err, cfrac):
    """Insert and observational catalog (Catalog, CatalogStar and Observation
    tables) efficiently with SQLAlchemy Core.

    :func:`init_catalog` should be called first to ensure the Catalog and
    Bandpass rows are added. This function can be called several times to
    append stars in several batches to the catalog.

    Parameters
    ----------
    session : ``Session``
        The session instance.
    name : str
        Name of the Catalog.
    instrument : str
        Name of the instrument.
    band_names : list
        List of bandpass names
    band_system : str
        Name of the photometric system.
    x : ``ndarray``, (n_stars,)
        X-coordinates of stars on reference image.
    y : ``ndarray``, (n_stars,)
        Y-coordinates of stars on reference image.
    ra : ``ndarray``, (n_stars,)
        RA-coordinates of stars.
    ra_err : ``ndarray``, (n_stars,)
        Uncertainty of RA-coordinates of stars.
    dec : ``ndarray``, (n_stars,)
        Dec-coordinates of stars.
    dec_err : ``ndarray``, (n_stars,)
        Uncertainty of Dec-coordinates of stars.
    mag : ``ndarray``, (n_stars, n_bands)
        Magnitudes of stars.
    mag_err : ``ndarray``, (n_stars, n_bands
        Uncertainties of magnitudes of stars.
    cfrac : ``ndarray``, (n_stars,)
        Completeness fraction of a star in this catalog.
    """
    n_bands = len(band_names)
    n_stars = ra.shape[0]
    assert n_bands == mag.shape[1]
    assert n_bands == mag_err.shape[1]
    assert n_stars == ra.shape[0]
    assert n_stars == ra_err.shape[0]
    assert n_stars == dec.shape[0]
    assert n_stars == dec_err.shape[0]
    assert n_stars == mag.shape[0]
    assert n_stars == mag_err.shape[0]
    assert n_stars == x.shape[0]
    assert n_stars == y.shape[0]
    assert n_stars == cfrac.shape[0]

    # Pre-fetch catalog ids and band ids
    catalog_id = session.query(Catalog).\
            filter(Catalog.name == name).\
            filter(Catalog.instrument == instrument).one().id
    band_ids = [session.query(Bandpass).
            filter(Bandpass.name == n).
            filter(Bandpass.system == band_system).one().id
            for n in band_names]

    # Counter, seeded with next CatalogStar id value
    id_star_0 = _max_id(session, CatalogStar.__table__)
    id_obs = _max_id(session, Observation.__table__)

    cstars = []
    obs_list = []
    for i, id_star in enumerate(
            xrange(id_star_0 + 1, id_star_0 + n_stars + 1)):
        cstars.append({"id": id_star,
            "x": float(x[i]), "y": float(y[i]),
            "ra": float(ra[i]), "dec": float(dec[i]),
            "ra_err": float(ra_err[i]), "dec_err": float(dec_err[i]),
            "coord": point_str(ra[i], dec[i]),
            "cfrac": float(cfrac[i]),
            "catalog_id": catalog_id,
            "star_id": None})
        for j, band_id in enumerate(band_ids):
            id_obs += 1
            obs_list.append({"id": id_obs,
                "catalog_star_id": id_star, "bandpass_id": band_id,
                "mag": float(mag[i, j]), "mag_err": float(mag_err[i, j])})
        if i % 10 == 0:
            log.debug("Executing chunk")
            session.execute(CatalogStar.__table__.insert(), cstars)
            session.execute(Observation.__table__.insert(), obs_list)
            session.commit()
            log.debug("Committed chunk")
            cstars = []
            obs_list = []
    if len(cstars) > 0:  # insert remainders
        session.execute(CatalogStar.__table__.insert(), cstars)
        session.execute(Observation.__table__.insert(), obs_list)
        session.commit()


def _max_id(session, tbl):
    """Returns the maximum id value already present for a table,
    or 0 if no rows are yet in the DB.
    """
    try:
        maxid = session.execute(select([
            func.max(tbl.c.id, type_=Integer).label('maxid')]))\
            .scalar()
    except:
        maxid = 0
    if not maxid:
        maxid = 0
    log.debug("{0} MAXID {1}".format(tbl, maxid))
    return maxid


def make_polygon(header):
    """Get footprint polygons, with (RA,Dec) vertices, from the given
    extensions in the in the reference FITS file.
    """
    wcs = WCS(header)
    return wcs.calcFootprint().tolist()
