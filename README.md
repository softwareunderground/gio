# gio

Loading and saving various geoscience surface data formats (2D and 3D seismic horizons, grids, etc).

Starting with:

- OpendTect horizons
- Petrel horizons
  - IESX format
  - IRAP format
- ZMAP grids

**What formats would you like to see? [Make an issue](https://github.com/agile-geoscience/gio/issues).**


## Installation

This library is not on PyPI yet, so you'll have to install it from GitHub:

    python -m pip install --upgrade https://github.com/agile-geoscience/gio/archive/master.zip


## Contributing

Please get involved! We need:

- Example data (open access data only)
- Tutorials
- Documentation
- Parsers for various formats


## Testing

You can run the tests (requires `pytest` and `pytest-cov`) with 

    python run_tests.py


---

&copy; 2022 Agile Scientific, openly licenced under Apache 2.0
