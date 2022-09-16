from io import BytesIO

import requests
import numpy as np
from PIL import Image

import gio


def get_image_from_web(uri):
    data = requests.get(uri).content
    img = Image.open(BytesIO(data)).convert('RGB')
    rgb_im = np.asarray(img)[..., :3] / 255.
    return rgb_im


def test_unmap():
    # An image from Matteo Niccoli's blog:
    # https://mycartablog.com/2014/08/24/what-your-brain-does-with-colours-when-you-are-not-looking-part-1/

    img = get_image_from_web('https://i0.wp.com/mycartablog.com/wp-content/uploads/2014/03/spectrogram_jet.png')

    cmap = (2035, 102, 2079, 1198)   # (left, top, right, bottom)
    crop = (312, 102, 1954, 1198)
    vrange = (-156.2, -69.0)
    data = gio.unmap_to_dataarray(img, cmap=cmap, crop=crop, vrange=vrange)
    assert data.shape == (1096, 1642)
    assert np.mean(data) + 133.46107021444217 < 1e-6
