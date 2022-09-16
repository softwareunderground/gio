"""
xarray convenience class and accessor.

Author: Matt Hall
Email: matt@agilescientific.com
Licence: Apache 2.0
"""
from dataclasses import dataclass

import numpy as np
import xarray as xr

from .zmap import dataarray_to_zmap


@dataclass
class GridInfo:
    xmin: float  # x-value of lower-left corner
    ymin: float  # y-value of lower-left corner
    xmax: float  # x-value of upper-right corner
    ymax: float  # y-value of upper-right corner
    data: np.ndarray  # grid of data values, shape=(nrow, ncol)
    dims: tuple = ('i', 'j')  # names of dimensions
    source: str = ''
    fname: str = ''

    def to_xarray(self):
        """
        Convert to xarray.DataArray. Only (x, y)-orthogonal grids are supported.
        """
        nrow, ncol = self.data.shape
        return xr.DataArray(self.data,
                            dims=self.dims,
                            coords={self.dims[1]: np.linspace(self.xmin, self.xmax, ncol),
                                    self.dims[0]: np.linspace(self.ymin, self.ymax, nrow)},
                            attrs={'source': self.source, 'fname': self.fname,})


@xr.register_dataarray_accessor("gio")
class SurfaceAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def to_zmap(self, fname,
                coords=None,
                comment_attr='comment',
                add_comment='File created by gio.to_zmap xarray accessory',
                nodes_per_line=6,
                field_width=12,
                precision=3,
                null_value=-999.25,
                ):
        """
        Write a DataArray to a ZMAP file.

        Args:
            fname (str): path to ZMAP file.
            coords (list or None): list of coordinate names to use for the X and
                Y axes. If None, use the first two dimensions of the DataArray.
            comment_attr (str or None): name of the DataArray attribute to use
                as a comment in the file. If None, no comment is added.
            add_comment (str or list or None): comment to add to the end of any
                comments found in the DataArray. If None, no comment is added.
            nodes_per_line (int): number of values to write per line.
            field_width (int): character width of each value field.
            precision (int): number of decimal places to write.
            null_value (float): value to use for NaN values.

        Returns:
            None
        """
        return dataarray_to_zmap(fname,
                                 self._obj,
                                 coords=coords,
                                 comment_attr=comment_attr,
                                 add_comment=add_comment,
                                 nodes_per_line=nodes_per_line,
                                 field_width=field_width,
                                 precision=precision,
                                 null_value=null_value,
                                 )
