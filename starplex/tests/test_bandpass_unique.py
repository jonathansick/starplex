#!/usr/bin/env python
# encoding: utf-8
"""
Test for the uniqueness quality of Bandpasses.
"""

from starplex.database import connect, create_all, Session
from starplex.database import Bandpass


class TestObservationsORM(object):

    def setup_class(self):
        connect(user='jsick', name='starplex_test')
        self.session = Session()
        create_all()

    def teardown_class(self):
        self.session.rollback()
        self.session.close()

    def test_bandpass_uniqueness(self):
        bp0 = Bandpass.as_unique(self.session, "V", "Vega")
        bp1 = Bandpass.as_unique(self.session, "B", "Vega")
        bp0b = Bandpass.as_unique(self.session, "V", "Vega")
        assert bp0 is bp0b
        assert bp1 is not bp0
