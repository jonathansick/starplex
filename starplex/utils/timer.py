#!/usr/bin/env python
# encoding: utf-8
"""
Timing utiltities
"""
import time


class Timer:
    def __enter__(self):
        # I use time.time() rather than time.clock() since I want to measure
        # time spent waiting on SQL queries, not just in python execution.
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start
