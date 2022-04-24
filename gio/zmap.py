"""
I/O for ZMAP grid formats.

Author: Matt Hall
License: Apache 2.0
"""
import zmapio
import xarray as xr


def read_zmap(fname):
    """
    Read a ZMAP file and return an xarray.Dataset

    Args:
        fname (str): The name of the file to read.

    Returns:
        xarray.Dataset with coordinates of "Y" and "X" and data value of "Z"
    """
    
    df = zmapio.ZMAPGrid(fname).to_pandas()
    ds = xr.Dataset.from_dataframe(df.set_index(['Y', 'X']))
    return ds
