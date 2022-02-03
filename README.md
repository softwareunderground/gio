# gio

[![Tests](https://github.com/agile-geoscience/gio/actions/workflows/build-test.yml/badge.svg)](https://github.com/agile-geoscience/gio/actions/workflows/build-test.yml)
[![PyPI status](https://img.shields.io/pypi/status/gio.svg)](https://pypi.org/project/gio//)
[![PyPI versions](https://img.shields.io/pypi/pyversions/gio.svg)](https://pypi.org/project/gio//)
[![PyPI license](https://img.shields.io/pypi/l/gio.svg)](https://pypi.org/project/gio/)

**Geoscience I/O for grids and horizons.**

The goal of this project is to load and save various geoscience surface data formats (2D and 3D seismic horizons, grids, etc). The interchange formats are the `xarray.DataArray` (and `xarray.Dataset` where we need a collection of arrays). This format is convenient because it allows us to store a NumPy array with Pandas-like indexing (as opposed to ordinary NumPy positional indexing).

We've started with:

- OpendTect horizons
- ZMAP grids
- Surfer grids
- Petrel horizons

**What formats would you like to see? [Make an issue](https://github.com/agile-geoscience/gio/issues).**


## Installation

This library is on PyPI, so you can install it with:

    pip install gio

 To get the latest unstable release, you can install it from GitHub:

    python -m pip install --upgrade https://github.com/agile-geoscience/gio/archive/develop.zip


## Examples

```python
import gio

da = gio.read_surfer(fname)
da.plot()
```

See more examples in the **notebooks** folder.


## Contributing

Please get involved! See [CONTRIBUTING.md](CONTRIBUTING.md).


## Testing

You can run the tests (requires `pytest` and `pytest-cov`) with

    python run_tests.py


## Building

This repo uses PEP 517-style packaging. [Read more about this](https://setuptools.pypa.io/en/latest/build_meta.html) and [about Python packaging in general](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

Building the project requires `build`, so first:

    pip install build

Then to build `gio` locally:

    python -m build

The builds both `.tar.gz` and `.whl` files, either of which you can install with `pip`.

---

&copy; 2022 Agile Scientific, openly licenced under Apache 2.0
