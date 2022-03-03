"""Test OdT reading and writing."""
from io import StringIO

import pytest

import gio


def test_read_odt():
    """Test the basics.
    """
    ds = gio.read_odt('data/OdT/3d_horizon/Segment_ILXL_Single-line-header.dat')
    assert ds['twt'].shape == (54, 57)
    assert ds['twt'].mean() - 661.88136 < 1e-5

    ds = gio.read_odt('data/OdT/3d_horizon/Segment_ILXL_Multi-line-header.dat')
    assert ds['twt'].shape == (54, 57)
    assert ds['twt'].mean() - 661.88136 < 1e-5

    ds = gio.read_odt('data/OdT/3d_horizon/Segment_ILXL_No-header.dat')
    assert ds['var_0'].shape == (54, 57)
    assert ds['var_0'].mean() - 661.88136 < 1e-5


def test_read_odt_xy():
    """
    Test the automagical XY reader.
    """
    fname = 'data/OdT/3d_horizon/Segment_XY_No-header.dat'

    with pytest.warns(UserWarning):
        # Warns the users it's computing a grid.
        ds = gio.read_odt(fname, names=['X', 'Y', 'TWT'])

    assert ds['twt'].shape == (54, 57)
    assert ds['twt'].mean() - 661.88136 < 1e-5


def test_write_odt():
    """Test the basics.
    """
    sio = StringIO()
    ds = gio.read_odt('data/OdT/3d_horizon/Segment_ILXL_Single-line-header.dat')
    _ = gio.to_odt(sio, ds, header='none')
    assert sio.getvalue()[:7].split() == ['376', '914']

    sio = StringIO()
    _ = gio.to_odt(sio, ds)
    assert sio.getvalue()[:11] == '# 1: Inline'
