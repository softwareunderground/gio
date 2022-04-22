"""Test ZMAP reading"""


import gio
import xarray as xr

def test_read_zmap():
    """Test the basics.
    """
    ds = gio.read_zmap('data/ZMAP/NStopo.dat.txt')
    
    assert isinstance(ds, xr.core.dataset.Dataset)
    assert ds['Z'].shape == (208, 435)
    assert abs(ds['Z'].mean() + 531.92306) < 1e-5

