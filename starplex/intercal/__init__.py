#!/usr/bin/env python
# encoding: utf-8
"""
Pipeline for computing inter-catalog zeropoint calibrations by minimizing
field-to-field zeropoint differences.

First, set which fields should be treated as having 'true' (trusted)
zeropoints using the ``set_zeropoint_reference()`` function.

The pipeline is run with three successive functions

1. ``prepare_network()``
2. ``analyze_network()``
3. ``solve_network()``
"""

from .refmanager import set_zeropoint_reference, unset_zeropoint_reference
from .prep import prepare_network
from .analyze import analyze_network
from .solve import solve_network
