:hide-toc:

.. container:: noclass
   :name: forkongithub

   `Fork on GitHub <https://github.com/agilescientific/gio>`_


gio: Geo I/O for Subsurface Surfaces
====================================

    | ``gio`` reads and write subsurface data files

    | describing surfaces, grids and horizons.


Quick start
-----------

.. toctree::
    :caption: Quick start

Install ``gio`` with pip:

.. code-block:: shell

    pip install gio

Read a Surfer grid:

.. code-block:: python

    import gio
    da = gio.read_surfer('surface.grd')

``da`` is a two-dimensional ``xarray.DataArray`` object, which is a kind of
array (NumPy, Dask, Pint, whatever) indexed like a Pandas dataframe. In
general, you can treat it like an array (or use ``da.data`` to get the
underlying array, or ``da.values`` to get the underlying array as a
``numpy.ndarray``).


User guide
----------

.. toctree::
    :maxdepth: 2
    :caption: User guide

    installation
    userguide/Read_OpendTect_horizons.ipynb
    userguide/Read_Surfer_grids.ipynb
    userguide/Read_and_write_ZMAP_files.ipynb
    userguide/Random_grids.ipynb


API reference
-------------

.. toctree::
    :maxdepth: 2
    :caption: API reference

    gio


Other resources
---------------

.. toctree::
    :maxdepth: 1
    :caption: Other resources

    development
    contributing
    authors
    license
    changelog


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. toctree::
    :caption: Project links
    :hidden:

    PyPI releases <https://pypi.org/project/gio/>
    Code in GitHub <https://github.com/agilescientific/gio>
    Issue tracker <https://github.com/agilescientific/gio/issues>
    Community guidelines <https://code.agilescientific.com/community>
    Agile's software <https://code.agilescientific.com>
    Agile's website <https://www.agilescientific.com>
