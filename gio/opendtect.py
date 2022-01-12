# -*- coding: utf-8 -*-
"""
I/O for OpendTect horizon formats.

:copyright: 2022 Agile Geoscience
:license: Apache 2.0
"""
import re
import pandas as pd
import xarray as xr
import numpy as np

from .xy_to_grid import xy_to_grid


def sense_types(data):
    """
    Guess the type of some numbers.
    """
    types = []
    for d in data:
        if re.fullmatch(r'[-.0-9]+', d):
            if '.' in d:
                t = float
            else:
                t = int
        else:
            t = str
        types.append(t)
    return types


def get_meta(fname, comment='#'):
    """
    Returns a string containing only the lines starting with
    the specified comment character. Does not read entire file.
    """
    header = ''
    with open(fname, 'rt') as f:
        for line in f:
            if line.startswith(comment):
                header += line
            else:
                types = sense_types(line.split())
                break
    return header, types


def get_names_from_header(header):
    """
    Get names from header text.
    """
    pattern = re.compile(r'(?:\"|\d: )(.+?)(?:\"|\n)')
    return pattern.findall(header)


def read_odt_as_df(fname, names=None, usecols=None):
    """
    Read an OdT file as a Pandas DataFrame.
    """
    header, types = get_meta(fname)
    
    if (names is None) and header:
        names = get_names_from_header(header)
    elif (names is None) and not header:
        t0, t1, *data_cols = types
        if (t0 == int) and (t1 == int):
            ix = ['Inline', 'Crossline']  # Standard OdT names.
        elif (t0 == float) and (t1 == float) and (len(data_cols) == 1):
            ix = ['X', 'Y']  # Standard OdT names.
        else:
            message = 'First two columns must be integers to be interpreted as inline and crossline.'
            raise TypeError(message)
        cols = range(len(data_cols))
        names = ix + [f'var_{n}' for n in cols if n in (usecols or cols)]
    else:
        usecols = range(len(names))
    
    df = pd.read_csv(fname,
                     names=names,
                     sep="\t",
                     comment='#',
                     usecols=usecols,
                    )
    
    return df


def regularize_columns(df, mapping=None, snake_case=True):
    """
    Adjust the column names to use segyio / SEGY-SAK standard names.
    And optionally transform to snake case.
    """
    mapping = mapping or {'Inline': 'iline', 'inline': 'iline',
                          'Crossline': 'xline', 'crossline': 'xline',
                          'X': 'cdp_x', 'x': 'cdp_x',
                          'Y': 'cdp_y', 'y': 'cdp_y',
                          'Z': 'twt'}
    df = df.rename(columns=mapping)
    if snake_case:
        df.columns = [n.casefold().replace(' ', '_') for n in df.columns]
    return df


def df_to_xarray(df, attrs=None, origin=(0, 0)):
    """
    Convert a DataFrame to a DataArray.
    """
    df = regularize_columns(df)
    if ('iline' in df.index.names) and ('xline' in df.index.names):
        pass  # Do nothing to df.
    elif ('iline' in df.columns) and ('xline' in df.columns):
        df = df.set_index(["iline", "xline"])
    elif ('cdp_x' in df.columns) and ('cdp_y' in df.columns):
        message = "Attempting to construct grid from (x, y) locations."
        ones = np.ones_like(df['cdp_x'])
        arr, (dx, dy), (addx, addy) = xy_to_grid(df['cdp_x'], df['cdp_y'], ones)
        df['iline'] = addx + origin[0]
        df['xline'] = addy + origin[1]
        df = df.set_index(["iline", "xline"])
    else:
        message = "Require columns or indexes 'iline' & 'xline', or 'cdp_x' & 'cdp_y'."
        raise TypeError(message)

    # Question: should return a DataArray if only 1 attribute?
    # But then have to deal with possibly having cdp_x and cdp_y.
    dx = xr.Dataset.from_dataframe(df)

    if ('cdp_x' in df.columns) and ('cdp_y' in df.columns):
        dx = dx.assign_coords(cdp_x=(('iline', 'xline'), dx['cdp_x'].data))
        dx = dx.assign_coords(cdp_y=(('iline', 'xline'), dx['cdp_y'].data))

    dx.attrs.update(attrs or {})

    return dx


def read_odt(fname, names=None, usecols=None, origin=(0, 0)):
    """
    Read an OdT horizon file. (Native format, not IESX.)

    Args
        names (list): The names of the columns in the file. If there's
            a header, this is not required. If there is no header, the
            function will attempt to interpret the columns:
            - If the first two columns are integers, they are interpreted
                as inline and crossline numbers.
            - If the first two columns are floats, and there is only one
                other column, then they are interpreted as (x, y) locations.
                Inline and crossline numbers will be generated, using
                `origin` as starting points.
            - In any other case, the function will throw an error;
                provide names to tell it what the columns are. Use 'inline'
                or 'iline' for inlines, 'xline' or 'crossline' for crosslines,
                'x' or 'cdp_x' for x locations, and 'y' or 'cdp_y' for y
                locations. The names of your attributes are up to you.
            If there are 5 columns but you only give 4 names, then only
            the first 4 columns will be loaded.
        usecols (list of ints): The indices of the columns that correspond
            to the names you're providing. If you're loading all the columns,
            or the N names correspond to the first N columns, then you don't
            need to provide this argument.
        origin (tuple of ints): If you only have (x, y) locations, then
            gio will try to construct a grid from them. It probably doesn't
            always work. It will assign inline and crossline numbers, which
            will just be NumPy-like indices by default. If you provide
            an origin, it will start numbering there.

    Returns
        xarray.Dataset: Each data column will be a data variable. Inline and
            crossline — and cdp_x and cdp_y, if present — will be coordinates.
    """
    df = read_odt_as_df(fname, names=names, usecols=usecols)
    return df_to_xarray(df, origin=origin)
