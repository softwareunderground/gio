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
import pandas as pd


def read_opendtect_points(filename):
    """
    Read an OpendTect points file. Returns array with columns UTMx, UTMy, TWT.

    TODO:
        Do something with metadata in file.
    """
    data = np.loadtxt(filename, skiprows=6, comments='!', usecols=[0,1,2])
    return data


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

def read_spwla(fname, null=-999.25):
    """
    Read SPWLA SPT core analysis / mudlog format.
    This has only been tested on one file! Use at your own risk.
    Reads fields 30, 36 and 40, using column names from field 15.

    Args
        fname (str): An SPWLA / SPT file.
        null (float): The number representing nulls; will be cast to NaNs.

    Returns
        pandas.DataFrame
    """
    import re

    # Not using this one.
    # rx_fields = re.compile(r'''
    #     ^
    #     15\s+?\d+?\s+?\d+?\n
    #     (?P<fields>[\s\S]+?)
    #     (?=^[^1]|\Z)
    # ''', re.MULTILINE | re.VERBOSE)

    rx_fields = re.compile(r'''
        ^
        \s+?\d+?\s+?\d+?\s+?\d+?\s+?0\S+?\s+?(?P<field>[\w\d][- ,.\w\d]+?)\n
    ''', re.MULTILINE | re.VERBOSE)

    rx_depth = re.compile(r'''
        ^
        30\s+?1\n
        \s+?(?P<depth>[.\d]+?)[ \t]+?[.\d]+?[ \t]+?(?P<seq>[.\d]+?)\n
        (?P<record>[\s\S]+?)
        (?=^30|\Z)
    ''', re.MULTILINE | re.VERBOSE)

    rx_data = re.compile(r'''
        ^
        (?:36\s+?1\s+?1\n
        \s+?(?P<descr>.+?)\n)?
        40\s+?1\s+?\d+?\n
        \s+?(?P<data>[- .\d]+?)\n
    ''', re.MULTILINE | re.VERBOSE)
    
    records = (field.group('field') for field in rx_fields.finditer(s))

    result = (
              (
                float(record.group('depth')),
                record.group('seq'),
                data.group('descr'),
                *[float(x) for x in data.group('data').split()]
              )
               for record in rx_depth.finditer(s)
               for data in rx_data.finditer(record.group('record'))
    )

    columns = ['depth', 'seq', 'descr'] + list(records)
    
    df = pd.DataFrame(result, columns=columns)
    df = df.replace(null, np.nan)

    return df