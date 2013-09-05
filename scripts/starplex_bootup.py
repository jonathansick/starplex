#!/usr/bin/env python
# encoding: utf-8

import starplex.database.connection
from starplex.database.connection import connect


def main():
    connect(host="localhost", port=5432, name="jsick", user="jsick")
    print starplex.database.meta.engine
    print starplex.database.meta.Session


if __name__ == '__main__':
    main()
