#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Geoscience I/O functions.

Single file module for now.

:copyright: 2015 Agile Geoscience
:license: Apache 2.0
"""
from io import StringIO

import numpy as np


def read_petrel_points(filename):
    """
    Read a Petrel points file. Return an array.

    TODO:
        Do something with Comments and Fields.
    """
    with open(filename) as f:

        comments = []
        fields = []
        in_header = False

        while True:
            line = f.readline().strip()

            if line.startswith('#'):
                comments.append(line.strip('# '))
            elif line.startswith('VERSION'):
                # version = line.split()[-1]
                pass
            elif line.startswith('BEGIN'):
                in_header = True
            elif line.startswith('END'):
                in_header = False
                break
            elif in_header:
                fields.append(line.strip())
            else:
                break

        d = f.read()
        s = StringIO(d)

        return np.loadtxt(s)


def read_petrel_horizon(filename):
    """
    Read a Petrel 2D IESX horizon file. Return an array.

    """
