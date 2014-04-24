========
Starplex
========

Starplex is a panchromatic star catalog engine developed for the ANDROIDS survey.
We're building Starplex to combine observations from multiple catalogs into a unified star catalog.
Starplex will also be capable of applying calibrations to photometry.

Setting up the database
-----------------------

Starplex requires a working PostgreSQL database.
On a Mac, the best way to get this is with `Postgres.app <http://postgresapp.com>`_.
Running this will create a user corresponding to your login account name.
Login to the default database using ``psql`` and prepare a new one for Starplex::

   create database starplex;
   \connect starplex;
   create extension postgis;
   create extension hstore;


To install Starplex dependencies, run::

   pip install -r requirements.txt

To install the python Starplex package itself, run::

   python setup.py install

Running Tests
-------------

Create a test database named ``starplex_test`` using the same procedure as above.
As before create postgis and hstore extensions.

Then run tests via::

   python setup.py test

Note: This assumes the user is named ``jsick``.
Obviously we'll need to get this fixed.

Schema Overview
---------------

Starplex sets up tables in three categories: supporting tables, observational tables, and reduced catalog tables.

The only supporting table right now is ``bandpass``, which provides a definition of a bandpass name and photometric system.

Observationally oriented tables provide storage of raw photometric catalogs, such as those made by DOLPHOT.

- ``catalog`` defines an observation catalog, such as a run of dolphot.
- ``catalog_star`` defines stars observed in a ``catalog``.
- ``observation`` defines a photometric observation, in a single bandpass for a ``catalog_star``.

Reduced catalogs are stored across two tables:

- ``star`` defines a unique star
- ``magnitude`` defines a photometric quality of a single star in a single bandpass.

Browse the ``starplex/database`` directory to see how the models are constructed. 


Ingesting the 2MASS Point Source Catalog
----------------------------------------

One thing you can do is ingest a portion of the 2MASS PSC.
First, download the PSC files (compressed as ``.gz``) from ``ftp.ipac.caltech.edu``.
Starplex includes a ``starplex_twomicron.py`` script to ingest an arbitrary portion of this.
For example, to ingest 2MASS stars around M31, run::

   starplex_twomicron.py /data/2mass_psc --ra 7.5 17 --dec 36 47

(where the directory points to your PSC files). This tool generates a catalog named ``2MASS_PSC`` in the ``catalog`` table, along with related catalog stars and observations.


About
-----

Copyright 2014 Jonathan Sick. BSD Licensed.
