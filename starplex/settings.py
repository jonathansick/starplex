#!/usr/bin/env python
# encoding: utf-8
"""
Handle settings for Starplex databases.

Settings are stored on disk as a JSON file located at ``$HOME/.starplex.json``.
Alternative locations can be set with the ``$STARPLEXCONFIG`` environment
variable.

A basic ``.starplex.json`` file looks like this::

    {"servers":
        {"marvin": {"host": "localhost",
                    "port": 5432,
                    "user": "starplex",
                    "name": "starplex"
                    }
        }
    }


Server definitions are stored as a hash under the ``servers`` key. Here we
define one server named ``marvin`` that is connected to as ``localhost:5432``.


Functions
---------

- :func:`read_settings`
- :func:`locate_server`
"""

import os
import json
# import logging
from astropy import log


def read_settings(path=os.getenv('STARPLEXCONFIG',
                  os.path.expandvars('$HOME/.starplex.json'))):
    """Read the Starplex JSON configurations file.

    Parameters
    ----------
    path : str
        Path to the ``.moastro.json`` file.

    Returns
    -------
    settings : dict
        The settings, as a ``dict``. If the settings file is not found,
        an empty dictionary is returned.
    """
    try:
        with open(path, 'r') as f:
            return json.loads(f.read())
    except IOError:
        log.warning("{path} config file not found".format(path=path))
        return {}


def locate_server(servername):
    """Return connection parameters for a named server.

    Parameters
    ----------
    servername : str
        Name of the server, matching that in the ``.starplex.json`` file.

    Returns
    -------
    connect_configs : dict
        Keyword arguments for :func:`starplex.database.meta.base.connect`
    """
    conf = read_settings()
    try:
        connect_configs = conf['servers'][servername]
    except KeyError:
        log.warning("Bad config for server named '{n}'".format(n=servername))
        connect_configs = {}
    return connect_configs
