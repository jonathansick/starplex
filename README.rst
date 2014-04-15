========
Starplex
========

Starplex is a panchromatic star catalog engine developed for the ANDROIDS survey.
Starplex combines observations from multiple catalogs into a unified star catalog.
Starplex is also capable of applying calibrations to photometry.

Setting up the database
-----------------------

Starplex requires a working PostgreSQL database.
On a Mac, the best way to get this is with `Postgres.app<http://postgresapp.com>`_.
Running this will create a user corresponding to your login account name.
Login to the default database using psql and prepare a new one for Starplex::

   create database starplex;
   \connect starplex;
   create extension postgis;
   create extension hstore;

Running Tests
-------------

Create a test database named ``starplex_test`` using the same procedure as above.
As before create postgis and hstore extensions.

Then run tests via::

   python setup.py test

Note: This assumes the user is named ``jsick``.
Obviously we'll need to get this fixed.

About
-----

Copyright 2014 Jonathan Sick. BSD Licensed.
