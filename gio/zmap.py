"""
I/O for ZMAP grid formats.

:copyright: 2022 Agile Geoscience
:license: Apache 2.0
"""
import zmapio
import xarray as xr


def read_zmap(fname):
    """
    Read a ZMAP file and return an xarray.DataArray
    """
    z = ZMAPGrid(fname)
    da = xr.DataArray.from_dataframe(z.to_pandas())
    return da
