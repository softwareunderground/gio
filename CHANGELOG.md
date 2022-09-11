# CHANGELOG

## 0.1.6, 11 September 2022

The overall plan of `gio` is starting to take shape. In general, the plan is to read specialist subsurace formats of various file types, with either `xarray.Dataset` or `xarray.DataArray` as the target. Then, `gio` will write these same formats via an accessor method on the `xarray` object (and possibly also via ordinary functions). This release implements this pattern for the first time, specifically for the ZMAP format.

- Added the `zmap` module, with functions for reading ZMAP files (`read_zmap()`) and for writing files starting from an `xarray.DataArray` or from a NumPy array.
- Added `xarray.DataArray` accessor (in `xarray.py`) to save in ZMAP and OpendTect formats. The plan is to add more target formats the the accessor, according to need.
- Added tests for the ZMAP components. Removed `run_tests.py` and put the `pytest` options in `setup.cfg`, which seems cleaner.
- Started trying to maintain this file properly!
- Note that there are two 'work in progress' modules: `esri.py` and `usgs.py`, which will eventually read some common DEM formats.

In general, everything is a work in progress but if there is a chapter on something in [the User Guide](https://code.agilescientific.com/gio/index.html#user-guide) then it mostly works, at least for the test cases I have. If you have a file that should work but doesn't, please consider [making an issue](https://github.com/agilescientific/gio/issues).

Feedback is welcome on whether the target format for readers should be `xarray.Dataset` every time, even for singleton files.


## 0.1.5, 12 February 2022

- Added the `random` module, which generates random surfaces using sums of Perlin noise. The high-level interface is `gio.generate_random_surface()`. Also added a notebook for help on this module.
- Added the `logo` module, which plots gio's logo. Using the logo in the docs.


## 0.1.4, 3 February 2022

- New module: `surfer`, adapted from Seequent's [`steno3d_surfer`](https://pypi.org/project/steno3d_surfer), for reading Surfer 6 binary and ASCII files, and Surfer 7 binary files. The module does not write files yet.
- Started development on `iesx` module for reading IESX formatted files, eg from Petrel or OpendTect


## 0.1.0 to 0.1.3, February 2022

- Early development included setting up the package, and adding the `opendtect` and `xy_to_grid` modules.
