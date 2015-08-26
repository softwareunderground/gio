#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Geoscience I/O functions.

Single file module for now.

:copyright: 2015 Agile Geoscience
:license: Apache 2.0
"""
from io import StringIO
import os
import gzip

import numpy as np
import h5py


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
    pass


def read_odt_seismic(filename, start_time=None, sample_interval=None):
    """
    Read an ascii seismic volume from OdT.  Assumes we have inline and
    xline numbers, not x, y.

    Returns a tuple of timebase, arrays representing inline and xline numbers,
    and an array of data.

    TODO:
        Is it better to return an array of inline, xline coordinates?
        Is that np.meshgrid...?
    """
    # Sniff file compression.
    file_extension = os.path.splitext(filename)[1]

    if file_extension[-2:] == 'gz':
        with gzip.open(filename, 'rb') as f:
            raw = f.readlines()
    else:
        with open(filename, 'r') as f:
            raw = f.readlines()

    # Sniff for a header.
    if len(raw[0].split()) == 3:
        temp = [float(x) for x in raw.pop(0).split()]
        start_time, sample_interval, number_samples = temp

    # Gather the data.
    inlines, xlines, traces = [], [], []

    for line in raw:
        l = line.split()
        inlines.append(int(l.pop(0)))
        xlines.append(int(l.pop(0)))
        trace = np.loadtxt(l)
        traces.append(trace)

    # Prepare everything for return.
    number_inlines = max(inlines) - min(inlines) + 1
    number_xlines = max(xlines) - min(xlines) + 1
    number_samples = len(traces[0])  # Nevermind what the header said

    if start_time and sample_interval:
        end_time = start_time + (number_samples-1)*sample_interval
        time_basis = np.linspace(start_time, end_time, number_samples)
    else:
        time_basis = None

    data = np.array(traces)
    data = np.reshape(data, (number_inlines, number_xlines, number_samples))

    return time_basis, np.array(inlines), np.array(xlines), data


def seismic_array_to_hdf5(a):
    """
    Write seismic as HDF5 file.

    This is clearly not needed, just parking it here.
    """
    h5f = h5py.File('data/seismic.h5', 'w')
    h5f.create_dataset('data', data=a, compression='lzf')
    h5f.close()
