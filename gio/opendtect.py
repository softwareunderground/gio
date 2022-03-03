"""
I/O for OpendTect horizon formats.

Author: Matt Hall
License: Apache 2.0
"""
import warnings
import re
import csv
from io import StringIO

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


def read_odt_as_df(fname, names=None, usecols=None, na_values=None, **kwargs):
    """
    Read an OdT file as a Pandas DataFrame.

    Args:
        fname (str): Path to file.
        names (list): List of column names.
        usecols (list): List of column indices to use.
        na_values (list): List of values to treat as NA.
        kwargs are passed to pandas.read_csv.

    Returns:
        df (pandas.DataFrame): DataFrame containing the data.
    """
    header, types = get_meta(fname)

    if header and (len(types) > len(get_names_from_header(header))):
        # Then this is a multi-horizon file.
        header = '# "Horizon"\n' + header

    if (names is None) and header:
        names = get_names_from_header(header)
    elif (names is not None) and header:
        columns = get_names_from_header(header)
        usecols = [columns.index(n) for n in names]
    elif (names is not None) and not header:
        usecols = range(len(names))
    else:
        # Names is None, and no header.
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

    if na_values is None:
        na_values = ['1e30']
    else:
        na_values = [str(n) for n in na_values]

    df = pd.read_csv(fname,
                     names=names,
                     sep="\t",
                     comment='#',
                     usecols=usecols,
                     na_values=na_values,
                     keep_default_na=False,
                     **kwargs
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


def df_to_xarray(df, attrs=None, origin=(0, 0), step=(1, 1)):
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
        warnings.warn(message, stacklevel=2)
        ones = np.ones_like(df['cdp_x'])
        _, _, (addy, addx) = xy_to_grid(df['cdp_x'], df['cdp_y'], ones)
        addy = np.max(addy) - addy  # Adjust for origin.
        addx = np.max(addx) - addx  # I don't know why this is required..
        df['iline'] = step[0] * addx + origin[0]
        df['xline'] = step[1] * addy + origin[1]
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


def read_odt(fname,
             names=None,
             usecols=None,
             na_values=None,
             origin=(0, 0),
             step=(1, 1),
             attrs=None
             ):
    """
    Read an OdT horizon file. (Native format, not IESX.)

    Args:
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
        na_values (list of str): The strings that correspond to missing data.
            By default, this is ['1e30'], the deault NULL value in OpendTect.
            Any values you provide will *replace* this default and will be
            used to replace missing data with NaNs.
        origin (tuple of ints): If you only have (x, y) locations, then
            gio will try to construct a grid from them. It probably doesn't
            always work. It will assign inline and crossline numbers, which
            will just be NumPy-like indices by default. If you provide
            an origin, it will start numbering there; if you provide a step,
            it will use that to increment the indices.
        step (tuple of ints): The step size of the grid (see `origin`, above).
        attrs (dict): The attributes to add to the Dataset; the filename
            will be added as 'odt_filename'.

    Returns:
        xarray.Dataset: Each data column will be a data variable. Inline and
            crossline — and cdp_x and cdp_y, if present — will be coordinates.
    """
    df = read_odt_as_df(fname,
                        names=names,
                        usecols=usecols,
                        na_values=na_values
                        )

    attrs = attrs or {}
    attrs.update({'odt_filename': fname})

    if 'Horizon' in df.columns:
        dx = xr.Dataset()
        for name, group in df.groupby('Horizon'):
            group = group.drop(columns=['Horizon'])
            ds = df_to_xarray(group, attrs=attrs, origin=origin, step=step)

            # Get the one DataArray out (surely there's a better way to do this?).
            da = ds[list(ds.data_vars.keys())[0]]

            # Add it to the Dataset.
            dx[name] = da

    else:
        dx = df_to_xarray(df, attrs=attrs, origin=origin, step=step)

    return dx

def to_odt(fname, dx, multi=False, twt=None, force_twt=True, name=None, dropna=True, header='multiline', **kwargs):
    """
    Write an OdT horizon file. (Native format, not IESX.)
    
    There is an unhealthy amount of magic in this function.

    Args:
        fname (str): The name of the file to write.
        dx (xarray.Dataset): The data to write.
        multi (bool): Whether you want a multi-horizon export.
        twt (str): The name of the variable containing the two-way time, if
            not 'twt'.
        force_twt (bool): Whether to force the first variable to be two-way
            time. If there's more than one variable, this throws a warning.
        dropna (bool): If True, drop any rows with NaNs from the data. This
            is usual in OpendTect, but it may make the file harder to read
            by other software.
        header (str): The type of header to use. Either 'multiline' or
            'singleline' is recommended, but 'none' will omit it entirely.
        **kwargs: Additional arguments to pass to `pandas.DataFrame.to_csv`.

    Returns:
        None
    """
    # Deal with multi-horizon case, which can only have Z / twt, but can
    # have IL/XL and X/Y, and can have single, multi, or no header.
    # Split into DataArrays and call this function on each.
    if multi:
        strs = []
        for name, da in dx.data_vars.items():
            db = da.rename('twt')
            sio = StringIO()
            _ = to_odt(sio, db, twt=twt, name=name, dropna=dropna, header=header, **kwargs)
            strs.append(sio.getvalue())
        with open(fname, 'wt') as f:
            f.write('\n'.join(strs))
        return
    
    # Continue with single-horizon case.

    # Make the dataframe...
    df = dx.to_dataframe()
    if (twt is None) and force_twt and ('twt' not in df.columns):
        # Use the first column for twt.
        if (len(df.columns)>1):
            # Warn if there are several columns.
            message = 'Assuming first column is TWT; pass force_twt=False to prevent this.'
            warnings.warn(message, stacklevel=2)
        # Assume twt is first non-special column.
        twt = [c for c in df.columns if c not in ['cdp_x', 'cdp_y']][0]
    else:
        twt = twt or 'twt'
    df = df.reset_index()
    if dropna:
        df = df.dropna()
    # ... and regularize the columns.
    mapping = {'iline': 'Inline', 'xline': 'Crossline',
               'cdp_x': 'X', 'cdp_y': 'Y',
               twt: 'Z'
               }
    df = df.rename(columns=mapping)
    df.columns = [col.replace('_', ' ').title() for col in df.columns]

    # Construct the header text.
    if header not in ['multiline', 'singleline', 'none', None]:
        raise ValueError("header must be one of 'multiline', 'singleline', 'none'.")
    if header == 'multiline':
        h = [f"# {i+1}: {col}\n" for i, col in enumerate(df.columns)]
        h_text = ''.join(h) + "# - - - - - - - - - -\n"
    elif header == 'singleline':
        h_text = '# "' + '"\t"'.join(df.columns) + '"\n' + "# - - - - - - - - - -\n"
    else:
        h_text = ''
    
    # Write the header text.
    try:
        fname.write(h_text)  # fname is open file handle.
    except AttributeError:
        with open(fname, 'wt') as f:
            f.write(h_text)
            
    # Add the 'name' column, if required (only for multi-horizon export).
    if name is not None:
        cols = df.columns
        df['_'] = name
        df = df[['_'] + list(cols)]

    # Write the data.
    na_rep = kwargs.pop('na_rep', '1e30')
    df.to_csv(fname,
              mode='a',
              header=False,
              index=False,
              sep='\t',
              na_rep=na_rep,
              quotechar='"',
              quoting=csv.QUOTE_NONNUMERIC,
              **kwargs
              )

    return None
