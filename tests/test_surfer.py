"""Test Surfer .grd readers."""
import gio


def test_surfer_6():
    """Test the basics.
    """
    da = gio.read_surfer('data/Surfer/surfer-6-ascii-tiny.grd')
    assert da.shape == (10, 10)
    assert da.max() == 97.19

def test_surfer_7():
    """Test the basics.
    """
    da = gio.read_surfer('data/Surfer/WDS1_Si_TAP_Quant.grd')
    assert da.shape == (352, 629)
    assert da.mean() - 23.4545715 < 1e-5
