"""
Read 2D ASCII/binary Surfer grid files.

:copyright: 2022 Agile Geoscience (this adaptation)
:license: Apache 2.0

Adapted from Seequent's `steno3d_surfer`: https://pypi.org/project/steno3d_surfer

:copyright: 2018 Seequent
:license: MIT

MIT License
Copyright (c) 2018 Seequent
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from struct import unpack
from dataclasses import dataclass
import warnings

import numpy as np
import xarray as xr


@dataclass
class GridInfo:
    xmin: float  # x-value of lower-left corner
    ymin: float  # y-value of lower-left corner
    xmax: float  # x-value of lower-left corner
    ymax: float  # y-value of lower-left corner
    data: np.ndarray  # grid of data values, shape=(nrow, ncol)
    fname: str = '' # The filename

    def to_xarray(self):
        """
        Convert to xarray.DataArray. Only (x, y)-orthogonal grids are supported.
        """
        nrow, ncol = self.data.shape
        return xr.DataArray(self.data,
                            dims=('y', 'x'),
                            coords={'x': np.linspace(self.xmin, self.xmax, ncol),
                                    'y': np.linspace(self.ymin, self.ymax, nrow)},
                            attrs={'source': self.fname,})


def read_surfer(fname):
    """
    Reader for Surfer .grd files, supporting both
    Surfer 6 binary & ASCII files, and Surfer 7 binary files.
    Only (x, y)-orthogonal grids are supported.

    Args:
        fname (str): The filename of the Surfer .grd file.

    Returns:
        xarray.DataArray: The grid data.
    """
    grd_info = read_grd(fname)
    da = grd_info.to_xarray()
    return da

def read_grd(fname):
    with open(fname, 'rb') as f:
        file_ident = unpack('4s', f.read(4))[0]

    if file_ident == b'DSRB':
        grd_info = _surfer7bin(fname)
    elif file_ident == b'DSBB':
        grd_info = _surfer6bin(fname)
    elif file_ident == b'DSAA':
        grd_info = _surfer6ascii(fname)
    else:
        raise RuntimeError('Invalid file identifier for Surfer .grd file. '
                           'First 4 characters must be DSRB, DSBB, or DSAA')
    return grd_info

def _surfer7bin(fname):
    with open(fname, 'rb') as f:
        if unpack('4s', f.read(4))[0] != b'DSRB':
            raise RuntimeError('Invalid file identifier for Surfer 7 binary'
                               ' .grd grid. First 4 characters must be DSRB.')
        f.read(8)  # Size & Version

        section = unpack('4s', f.read(4))[0]
        if section != b'GRID':
            raise RuntimeError('Unsupported Surfer 7 file structure. GRID keyword '
                               'must follow immediately after header but {} '
                               'encountered.'.format(section))
        size = unpack('<i', f.read(4))[0]
        if size != 72:
            raise RuntimeError('Surfer 7 GRID section is unrecognized size. Expected '
                               '72 but encountered {}'.format(size))

        # Using symbols in docs:
        # https://grapherhelp.goldensoftware.com/subsys/surfer_7_grid_file_format.htm
        nRow = unpack('<i', f.read(4))[0]
        nCol = unpack('<i', f.read(4))[0]
        xLL = unpack('<d', f.read(8))[0]
        yLL = unpack('<d', f.read(8))[0]
        xSize = unpack('<d', f.read(8))[0]
        ySize = unpack('<d', f.read(8))[0]
        _ = unpack('<d', f.read(8))[0]  # zmin
        _ = unpack('<d', f.read(8))[0]  # zmax
        rot = unpack('<d', f.read(8))[0]
        if rot != 0:
            warnings.warn('Unsupported feature: Rotation != 0', stacklevel=2)
        blankval = unpack('<d', f.read(8))[0]

        section = unpack('4s', f.read(4))[0]
        if section != b'DATA':
            raise RuntimeError('Unsupported Surfer 7 file structure. DATA keyword '
                               'must follow immediately after GRID section but {} '
                               'encountered.'.format(section))
        datalen = unpack('<i', f.read(4))[0]
        if datalen != nCol*nRow*8:
            raise RuntimeError('Surfer 7 DATA size does not match expected size from '
                               'columns and rows. Expected {} but encountered '
                               '{}'.format(nCol*nRow*8, datalen))
        data = np.nan * np.zeros(nCol*nRow)
        for i in range(nCol*nRow):
            data[i] = unpack('<d', f.read(8))[0]

        data = np.where(data >= blankval, np.nan, data)
        try:
            section = unpack('4s', f.read(4))[0]
            if section == b'FLTI':
                warnings.warn('Unsupported feature: Fault Info', stacklevel=2)
            else:
                warnings.warn('Unrecognized keyword: {}'.format(section), stacklevel=2)
            warnings.warn('Remainder of file ignored', stacklevel=2)
        except:
            pass

    return GridInfo(xmin=xLL,
                    ymin=yLL,
                    xmax=xLL + xSize*nCol,
                    ymax=yLL + ySize*nRow,
                    data=np.flipud(data.reshape(nRow, nCol)),
                    fname=fname,
                    )


def _surfer6bin(fname):
    with open(fname, 'rb') as f:
        if unpack('4s', f.read(4))[0] != b'DSBB':
            raise RuntimeError('Invalid file identifier for Surfer 6 binary .grd '
                               'file. First 4 characters must be DSBB.')
        nx = unpack('<h', f.read(2))[0]
        ny = unpack('<h', f.read(2))[0]
        xlo = unpack('<d', f.read(8))[0]
        xhi = unpack('<d', f.read(8))[0]
        ylo = unpack('<d', f.read(8))[0]
        yhi = unpack('<d', f.read(8))[0]
        _ = unpack('<d', f.read(8))[0]  # zmin
        _ = unpack('<d', f.read(8))[0]  # zmax
        data = np.nan * np.zeros(nx * ny)
        for i in range(nx * ny):
            zdata = unpack('<f', f.read(4))[0]
            if zdata >= 1.701410009187828e+38:
                data[i] = np.nan
            else:
                data[i] = zdata

    return GridInfo(xmin=xlo,
                    ymin=ylo,
                    xmax=xhi,
                    ymax=yhi,
                    data=np.flipud(data.reshape(ny, nx)),
                    fname=fname,
                    )


def _surfer6ascii(fname):
    with open(fname, 'rt') as f:
        if f.readline().strip() != 'DSAA':
            raise RuntimeError('Invalid file identifier for Surfer 6 ASCII .grd '
                               'file. First line must be DSAA')
        [nx, ny] = [int(n) for n in f.readline().split()]
        [xlo, xhi] = [float(n) for n in f.readline().split()]
        [ylo, yhi] = [float(n) for n in f.readline().split()]
        [_, _]       = [float(n) for n in f.readline().split()]  # zmin zmax
        data = np.fromiter(f.read().split(), dtype=float)

    return GridInfo(xmin=xlo,
                    ymin=ylo,
                    xmax=xhi,
                    ymax=yhi,
                    data=np.flipud(data.reshape(ny, nx)),
                    fname=fname,
                    )
