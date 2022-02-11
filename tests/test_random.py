"""Test Surfer .grd readers."""
import gio


def test_random():
    """Test the basics.
    """
    da = gio.generate_random_surface(10, random_seed=42)
    assert da.shape == (12, 12)
    assert da.mean() - -0.14526361 < 1e-6
