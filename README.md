# gio

[![Tests](https://github.com/agilescientific/gio/actions/workflows/build-test.yml/badge.svg)](https://github.com/agilescientific/gio/actions/workflows/build-test.yml)
[![Build docs](https://github.com/agilescientific/gio/actions/workflows/build-docs.yml/badge.svg)](https://github.com/agilescientific/gio/actions/workflows/build-docs.yml)
[![PyPI version](https://img.shields.io/pypi/v/gio.svg)](https://pypi.org/project/gio/)
[![PyPI versions](https://img.shields.io/pypi/pyversions/gio.svg)](https://pypi.org/project/gio/)
[![PyPI license](https://img.shields.io/pypi/l/gio.svg)](https://pypi.org/project/gio/)

**Geoscience I/O for grids and horizons.**

The goal of this project is to load and save various geoscience surface data formats (2D and 3D seismic horizons, grids, etc). The interchange formats are the `xarray.DataArray` (and `xarray.Dataset` where we need a collection of arrays). This format is convenient because it allows us to store a NumPy array with Pandas-like indexing (as opposed to ordinary NumPy positional indexing).

We've started with:

- OpendTect horizons
- ZMAP grids
- Surfer grids
- Petrel horizons

**What formats would you like to see? [Make an issue](https://github.com/agilescientific/gio/issues).**


## Installation

This library is on PyPI, so you can install it with:

    pip install gio

 To get the latest unstable release, you can install it from GitHub:

    python -m pip install --upgrade https://github.com/agilescientific/gio/archive/develop.zip


## Basic usage

In general, there's a reader for each supported file format. The reader produces an `xarray.DataArray`, or `xarray.Dataset` if the format supports multiple surfaces in one file.

```python
import gio

da = gio.read_surfer(fname)
da.plot()
```


## Documentation

See [the documentation](https://code.agilescientific.com/gio) for more examples, and for help developing `gio` or making contributions back to this project.
