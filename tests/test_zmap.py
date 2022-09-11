"""Test ZMAP reading and writing."""
from io import StringIO

import pytest

import gio


def test_read_zmap():
    """Test the basics.
    """
    da = gio.read_zmap('data/ZMAP/NStopo.dat')
    assert da.shape == (208, 435)
    assert da.mean() + 531.92306539 < 1e-6
    assert 'NStopo.dat' in da.attrs['fname']


def test_write_zmap():
    """Test the basics.
    """
    sio = StringIO()
    z = gio.generate_random_surface(size=(10, 20), random_seed=42)
    z.gio.to_zmap(sio)
    assert sio.getvalue()[46:60] == '@None, GRID, 6'
    assert len(sio.getvalue()) == 3038
    assert sio.getvalue()[-30:] == '0.198       0.332       0.207\n'
