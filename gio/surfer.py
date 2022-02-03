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
    xll: float  # x-value of lower-left corner
    yll: float  # y-value of lower-left corner
    xsize: float  # x-axis spacing
    ysize: float  # y-axis spacing
    data: np.ndarray  # grid of data values, shape=(nrow, ncol)

    ncol: int = float('nan')   # number of columns, min=2 (implicit)
    nrow: int = float('nan')   # number of rows, min=2 (implicit)
    zmin: float = float('nan')   # minimum data value (implicit)
    zmax: float = float('nan')  # maximum data value (implicit)

    fname: str = '' # The filename

    def to_xarray(self):
        """
        Convert to xarray.DataArray. Only (x, y)-orthogonal grids are supported.
        """
        try:
            return xr.DataArray(self.data,
                            dims=('y', 'x'),
                            coords={'x': np.arange(self.ncol) * self.xsize + self.xll,
                                    'y': np.arange(self.nrow) * self.ysize + self.yll},
                            attrs={'source': self.fname,})
        except ValueError:
            # This should be more predictable.
            return xr.DataArray(self.data.T,
                            dims=('y', 'x'),
                            coords={'x': np.arange(self.ncol) * self.xsize + self.xll,
                                    'y': np.arange(self.nrow) * self.ysize + self.yll},
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
    xray = grd_info.to_xarray()
    return xray

def read_grd(fname):
    with open(fname, 'rb') as f:
        file_ident = unpack('4s', f.read(4))[0]

    if file_ident == b'DSRB':
        print("Surfer 7 binary .grd file detected. ")
        grd_info = _surfer7bin(fname)
    elif file_ident == b'DSBB':
        print("Surfer 6 binary .grd file detected. ")
        grd_info = _surfer6bin(fname)
    elif file_ident == b'DSAA':
        grd_info = _surfer6ascii(fname)
    else:
        raise RuntimeError(
            'Invalid file identifier for Surfer .grd file. First 4 '
            'characters must be DSRB, DSBB, or DSAA'
        )
    return grd_info

def _surfer7bin(fname):
    with open(fname, 'rb') as f:
        if unpack('4s', f.read(4))[0] != b'DSRB':
            raise RuntimeError(
                'Invalid file identifier for Surfer 7 binary .grd '
                'file. First 4 characters must be DSRB.'
            )
        f.read(8)  # Size & Version

        section = unpack('4s', f.read(4))[0]
        if section != b'GRID':
            raise RuntimeError(
                'Unsupported Surfer 7 file structure. GRID keyword '
                'must follow immediately after header but {} '
                'encountered.'.format(section)
            )
        size = unpack('<i', f.read(4))[0]
        if size != 72:
            raise RuntimeError(
                'Surfer 7 GRID section is unrecognized size. Expected '
                '72 but encountered {}'.format(size)
            )
        nrow = unpack('<i', f.read(4))[0]
        ncol = unpack('<i', f.read(4))[0]
        x0 = unpack('<d', f.read(8))[0]
        y0 = unpack('<d', f.read(8))[0]
        deltax = unpack('<d', f.read(8))[0]
        deltay = unpack('<d', f.read(8))[0]
        zmin = unpack('<d', f.read(8))[0]
        zmax = unpack('<d', f.read(8))[0]
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
        if datalen != ncol*nrow*8:
            raise RuntimeError('Surfer 7 DATA size does not match expected size from '
                               'columns and rows. Expected {} but encountered '
                               '{}'.format(ncol*nrow*8, datalen))
        data = np.zeros(ncol*nrow)
        for i in range(ncol*nrow):
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

    grd_info = GridInfo(
        ncol=ncol,
        nrow=nrow,
        xll=x0,
        yll=y0,
        xsize=deltax,
        ysize=deltay,
        zmin=zmin,
        zmax=zmax,
        data=data.reshape(ncol, nrow, order='F').T,
        fname=fname,
    )

    return grd_info

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
        zlo = unpack('<d', f.read(8))[0]
        zhi = unpack('<d', f.read(8))[0]
        data = np.ones(nx * ny)
        for i in range(nx * ny):
            zdata = unpack('<f', f.read(4))[0]
            if zdata >= 1.701410009187828e+38:
                data[i] = np.nan
            else:
                data[i] = zdata

    grd_info = GridInfo(
        ncol=nx,
        nrow=ny,
        xll=xlo,
        yll=ylo,
        xsize=(xhi-xlo)/(nx-1),
        ysize=(yhi-ylo)/(ny-1),
        zmin=zlo,
        zmax=zhi,
        data=data.reshape(nx, ny, order='F').T,
        fname=fname,
    )

    return grd_info

def _surfer6ascii(fname):
    with open(fname, 'r') as f:
        if f.readline().strip() != 'DSAA':
            raise RuntimeError('Invalid file identifier for Surfer 6 ASCII .grd '
                               'file. First line must be DSAA')
        [ncol, nrow] = [int(n) for n in f.readline().split()]
        [xmin, xmax] = [float(n) for n in f.readline().split()]
        [ymin, ymax] = [float(n) for n in f.readline().split()]
        [zmin, zmax] = [float(n) for n in f.readline().split()]
        data = np.fromiter(f.read().split(), dtype=float)

    grd_info = GridInfo(
        ncol=ncol,
        nrow=nrow,
        xll=xmin,
        yll=ymin,
        xsize=(xmax-xmin)/(ncol-1),
        ysize=(ymax-ymin)/(nrow-1),
        zmin=zmin,
        zmax=zmax,
        data=data.reshape(nrow, ncol),
        fname=fname,
    )

    return grd_info
