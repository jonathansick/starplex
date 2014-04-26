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

Connecting to a Session
-----------------------

The most way to get an SQLAlchemy session, and hence begin with the database, is with the ``connect`` function:

.. code:: python

    from starplex.database import connect, Session, create_all
    connect(user="starplex", name="starplex", host="localhost", port=5432, echo=True)
    session = Session()
    create_all()

Note that ``echo`` is an extra keyword passed to the SQLAlchemy engine.

Sometimes it's easier to maintain database connection info in a configuration file.
This can be done by creating a ``~/.starplex.json`` file with a format similar to:

.. code:: javascript

   {"servers":
       {"marvin": {"host": "localhost",
                   "port": 25432,
                   "user": "starplex",
                   "name": "starplex"
                   }
       }
   }

Here we've named a server call ``marvin``.
Now we can connect to a named server with:

.. code:: python

   from starplex.database import connect_to_server, Session, create_all
   connect_to_server("marvin", echo=True)
   session = Session()
   create_all()
    
Ingesting the 2MASS Point Source Catalog
----------------------------------------

One thing you can do is ingest a portion of the 2MASS PSC.
First, download the PSC files (compressed as ``.gz``) from ``ftp.ipac.caltech.edu``.
Starplex includes a ``starplex_twomicron.py`` script to ingest an arbitrary portion of this.
For example, to ingest 2MASS stars around M31, run::

   starplex_twomicron.py /data/2mass_psc --ra 7.5 17 --dec 36 47

(where the directory points to your PSC files).
This tool generates a catalog named ``2MASS_PSC`` in the ``catalog`` table, along with related catalog stars and observations.

Examples
--------

Querying an Observational Catalog to get a NumPy Structured Array
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suppose you've loaded an HST/ACS star catalog named ``'disk'`` with photometry in filters named ``'f606w'`` and ``'f814w'``.
We'd like to retrieve this observational catalog into a structured numpy array of stellar RA, Dec, completeness fraction, and magnitudes in F606W and F814W.
This can be accomplished with the following script:

.. code:: python

    import numpy as np
    from sqlalchemy.orm import aliased
    from starplex.database import connect_to_server, Session
    from starplex.database import Catalog, Bandpass, CatalogStar, Observation

    connect_to_server('marvin', echo=True)
    session = Session()
    mag606obs = aliased(Observation)
    mag814obs = aliased(Observation)
    bp606 = aliased(Bandpass)
    bp814 = aliased(Bandpass)
    fieldname = "disk"
    q = session.query(CatalogStar.ra, CatalogStar.dec,
                CatalogStar.cfrac, mag606obs.mag, mag814obs.mag)\
            .join(mag606obs, CatalogStar.observations)\
            .join(mag814obs, CatalogStar.observations)\
            .join(Catalog)\
            .filter(Catalog.name == fieldname)\
            .join(bp606, mag606obs.bandpass)\
            .filter(bp606.name == "f606w")\
            .join(bp814, mag814obs.bandpass)\
            .filter(bp814.name == "f814w")
    dt = [('ra', np.float), ('dec', np.float), ('cfrac', np.float),
        ('m606', np.float), ('m814', np.float)]
    data = np.array(q.all(), dtype=np.dtype(dt))
    session.close()
    print data

A lot of the query magic here revolves around grabbing two rows from the ``Observation`` table corresponding to the F606W and F814W magnitudes of stars.
Since we need to join to the ``Observation`` and ``Bandpass`` tables twice, we create aliases to declare when we're talking to those tables in the context of either the F606W or F814W bandpasses.

About
-----

This project is part of the Andromeda Optical and Infrared Disk Survey (ANDROIDS).
While it is made available, we express no guarantee of fitness for your application (see the BSD license).
We also cannot guarantee that API or schema-breaking changes will not be made.
If you make use of this code in your research, send a note to `@jonathansick <https://twitter.com/jonathansick>`_ on Twitter.

Copyright 2014 Jonathan Sick. BSD Licensed.
