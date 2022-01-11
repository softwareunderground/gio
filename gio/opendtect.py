# -*- coding: utf-8 -*-
"""
I/O for OpendTect horizon formats.

:copyright: 2022 Agile Geoscience
:license: Apache 2.0
"""
import re
import pandas as pd
import xarray as xr


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


def regularize_columns(df, mapping=None, snake_case=True):
    """
    Adjust the column names to use segyio / SEGY-SAK standard names.
    And optionally transform to snake case.
    """
    mapping = mapping or {'Inline': 'iline',
                          'Crossline': 'xline',
                          'X': 'cdp_x',
                          'Y': 'cdp_y',
                          'Z': 'twt'}
    df = df.rename(columns=mapping)
    if snake_case:
        df.columns = [n.casefold().replace(' ', '_') for n in df.columns]
    return df


def read_odt_as_df(fname, kind='auto', names=None, usecols=None):
    """
    Read an OdT file as a Pandas DataFrame.
    """
    header, types = get_meta(fname)
    
    if (names is None) and header:
        names = get_names_from_header(header)
    elif (names is None) and not header:
        t0, t1, *data_cols = types
        if (t0 == int) and (t1 == int):
            ix = ['Inline', 'Crossline']
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

def df_to_xarray(df, attrs=None):
    """
    Convert a DataFrame to a DataArray.
    """
    if ('iline' in df.index.names) and ('xline' in df.index.names):
        pass  # Do nothing to df.
    elif ('iline' in df.columns) and ('xline' in df.columns):
        df = df.set_index(["iline", "xline"])
    else:
        message = "Require columns or indexes 'iline' and 'xline'."
        raise TypeError(message)

    if len(df.columns) == 1:
        dx = xr.DataArray.from_series(df.iloc[:, 0])  # One column.
    else:
        dx = xr.Dataset.from_dataframe(df)

    dx.attrs.update(attrs or {})

    return dx


def read_odt(fname, kind='auto'):
    """
    Read an OdT horizon file. (Native format, not IESX.)
    """
    df = read_odt_as_df(fname, kind=kind)
    df = regularize_columns(df)
    return df_to_xarray(df)
