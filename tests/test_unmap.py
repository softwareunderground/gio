"""Test unmapping data from images."""
from io import StringIO

from PIL import Image
import numpy as np
import matplotlib.cm as cm

import gio
from gio.unmap import is_greyscale


def test_unmap():
    """Test the basics.
    """
    img = Image.open('data/synthetic/test.png')
    img_as_arr = np.asarray(img)[..., :3] / 255.

    # Using a cbar image.
    cbar = np.asarray(Image.open('data/synthetic/test_cbar.png'))[..., :3] / 255
    cbar = cbar[7:-7, 7:-7]
    cbar = cbar[13]  # Middle row of pixels
    data = gio.unmap(img_as_arr, cmap=cbar, threshold=0.05, vrange=(100, 200), background=(1, 1, 1), levels=256)
    assert data.shape == (231, 231)
    assert np.nanmax(data) == 200
    assert np.nanmean(data) - 150.60721435278933 < 1e-6
    assert np.any(np.isnan(data))

    # Using a matplotlib cmap.
    data = gio.unmap(img_as_arr, cmap='viridis', threshold=0.05, vrange=(200, 300))
    assert np.nanmean(data) - 250.6121076492208 < 1e-6

    # Using a NumPy array.
    viridis_colours = cm.get_cmap('viridis')(np.linspace(0, 1, 24))[..., :3]
    data = gio.unmap(img_as_arr, cmap=viridis_colours, threshold=0.05, vrange=(200, 300))
    assert np.nanmean(data) - 250.56328195784667 < 1e-6


def is_greyscale():
    """
    Test the is_greyscale function.
    """
    # 8-bit colour.
    assert not gio.is_greyscale(rgb = (np.random.random((10, 10, 3)) * 256).astype(int))

    # RGBA colour.
    assert not is_greyscale(np.random.random((10, 10, 4)))

    # Simple 2D array.
    assert is_greyscale(np.random.random((10, 10)))

    # One-channel image.
    gs = np.random.random((10, 10, 1))
    assert is_greyscale(gs)

    # RBG greyscale.
    assert is_greyscale(np.dstack([gs, gs, gs]))

    # RGBA greyscale with random A channel.
    assert is_greyscale(np.dstack([gs, gs, gs, np.random.random((10, 10, 1))]))
