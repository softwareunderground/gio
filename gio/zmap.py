"""
I/O for ZMAP grid formats.

Author: Matt Hall
License: Apache 2.0
"""
import zmapio
import xarray as xr


def read_zmap(fname):
    """
    Read a ZMAP file and return an xarray.DataArray
    """
    df = zmapio.ZMAPGrid(fname).to_pandas()
    ds = xr.Dataset.from_dataframe(df.set_index(['Y', 'X']))
    return ds
