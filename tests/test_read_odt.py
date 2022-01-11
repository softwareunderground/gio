"""Test gio"""
import pandas as pd
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

    Really makes no difference if we have a header or not.
    """
    df = pd.read_csv('data/OdT/3d_horizon/Segment_XY_No-header.dat',
                 names=['x', 'y', 'twt', 'var_0', 'var_1', 'var_2', 'var_3'],
                 sep='\s+')

    arr, (dx, dy) = gio.xy_to_grid(df.x, df.y, df.twt)

    assert arr.shape == (57, 54)
    assert (dx, dy) == (50, 50)
