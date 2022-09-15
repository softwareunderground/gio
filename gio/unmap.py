import warnings
from collections import Counter

import numpy as np
from scipy.spatial import cKDTree
from scipy.cluster.vq import kmeans
from matplotlib import cm
from matplotlib.colors import hsv_to_rgb, rgb_to_hsv
from matplotlib.colors import to_rgb, LinearSegmentedColormap


def check_arr(arr):
    """
    Check the input array, and return it as a NumPy array, and the alpha channel
    
    Args:
        arr: NumPy array of image data.
        
    Returns:
        The RGB image array, and the alpha channel.
    """
    if arr.ndim == 2:
        arr = arr.reshape(arr.shape + (1,))
    elif arr.ndim != 3:
        raise ValueError('Array must be a grayscale or RGB(A) image.')
    
    h, w, c = arr.shape
    alpha = None
    if c == 1:
        warnings.warn('Grayscale image will be scaled and returned.')
        # But we can still scale it.
    elif (c == 0) or (c == 2) or (c >= 5):
        raise ValueError('Array must be a grayscale or RGB(A) image.')
    elif c == 4:
        arr = arr[..., :3]
        alpha = arr[..., 3]

    return arr, alpha


def get_background_rgb(arr, background='w'):
    """
    Get the RGB value of the background colour.

    Currently does not deal with alpha channel, if bg is transparent.

    Could also accept a pixel location to get the colour from.

    Args:
        arr: NumPy array of image data.
        background: The background colour: any matplotlib or CSS colour name,
            or 'common' to use the most common colour in the image.

    Returns:
        The RGB value of the background colour.
    """
    h, w, c = arr.shape
    if background == 'common':
        n_pixels = min(1000, h * w)
        ix = np.random.choice(h * w, size=n_pixels, replace=False)
        c = Counter(tuple(rgb) for rgb in arr.reshape(-1, c)[ix])
        bg = c.most_common(1)[0][0]
    elif isinstance(background, str):
        bg = to_rgb(background)
    else:
        try:
            bg = np.array(background).reshape(-1, 3)
        except:
            raise ValueError('background must be a str or Nx3 array-like of N RGB-triples in range (0-1).')
    return bg


def remove_hillshade(img):
    """
    Pass in an RGB 3-channel image, scaled 0-1.

    Returns the original image without the hillshading, and an RGBA array
    with only the hillshade.

    This will only work if the colourmap only uses full-valued colours. 
    In other words, the only thing affecting the lightness in the image is
    the hillshade. If the colourmap has any dark colours, this may be a 
    problem.

    Args:
        img: NumPy array of image data.

    Returns:
        The image without the hillshade, and the hillshade as a separate
            RGBA array.
    """
    hsv_im = rgb_to_hsv(img)
    val = 1 - hsv_im[..., 2]
    hillshade = val[..., None] * [0, 0, 0, 1]
    hsv_im[..., 2] = 1.0
    return hsv_to_rgb(hsv_im), hillshade


def crop_out(arr, rect, reduce=None, reverse='auto'):
    """
    Crop pixels out of a larger image.

    If reduce is a function, it is applied across the short axis.
    """
    l, t, r, b = rect
    assert (r >= l) and (b >= t), "Right and bottom must be greater than left and top respectively; the origin is at the top left of the image."

    r += 1 if r == l else 0
    b += 1 if t == b else 0
    pixels = arr[t:b, l:r]

    if r - l < b - t:
        # Then it is a vertical rectangle.
        pixels = np.swapaxes(pixels, 0, 1)
        if reverse == 'auto':
            reverse = True

    if reduce is not None:
        pixels = reduce(pixels, axis=0)
        
    if reverse:
        pixels = pixels[::-1]

    return pixels


def get_cmap(cmap, arr=None, levels=256, quantize=False):
    """
    Turn whatever we get as a colourmap into a matplotlib cmap.
    
    Args:
        cmap (str or array-like): The colourmap to use. If a string, it must
            be a matplotlib colourmap name. If an array-like, it must be either
            a 4-tuple of pixel coordinates, or an Nx3 array of RGB values in
            the range (0-1). If you pass pixel coordinates, they must be
            ordered like (left, top, right, bottom), giving the coordinates of
            the colourmap in the image array `arr` (which you must also pass!).
        arr (2d array): The image array, if `cmap` is a 4-tuple of pixel
            coordinates.
        levels (int): The number of colours you want in the colourmap, or
            which you count in the colourmap if `quantize` is True. 
        quantize (bool): Whether to quantize the colourmap to `levels` colours.
            Set this to true if the colourmap array or pixel lcoations you pass
            are 'stepped' or contain image noise.

    Returns:
        A matplotlib colourmap.
    """
    if isinstance(cmap, str):
        try:
            return cm.get_cmap(cmap)
        except ValueError:
            raise ValueError("cmap name not recognized by matplotlib")

    else:
        try:
            cmap = np.array(cmap)
        except TypeError as e:
            raise TypeError("cmap must be a str (name of a matplotlib cmap) or an array-like.")

        if (cmap.ndim == 1) and (cmap.size == 4):
            cmap = crop_out(arr, cmap, reduce=np.mean)

        if quantize:
            cmap, _ = kmeans(cmap, levels)        

        if (cmap.ndim == 2) and (cmap.shape[1] in [3, 4]):
            cmap = LinearSegmentedColormap.from_list('', cmap[:, :3], N=levels)
        else:
            raise TypeError("If an array-like, cmap must be either a 4-tuple of pixel coordinates "
                            "in a 1d array-like or a sequence of RGB(A) tuples in a 2d array-like.")

    return cmap


def normalize(arr, vrange):
    """
    Normalize the array to the given range.
    
    Args:
        arr: NumPy array of image data.
        vrange: The range to normalize to, as a tuple (min, max).
        
    Returns:
        The normalized array.
    """
    mi, ma = vrange
    arr = arr / np.nanmax(arr)
    return (ma - mi) * arr + mi


def is_greyscale(arr, epsilon=1e-6):
    """
    Check if the image is greyscale.
    
    Args:
        arr: NumPy array of image data.
        epsilon: The maximum difference between the R, G and B channels
            for the image to be considered greyscale.
            
    Returns:
        True if the image is greyscale, False otherwise.
    """
    arr = np.squeeze(arr).astype(float)

    if arr.ndim == 2:
        return True
    
    if np.max(arr) > 1:
        arr /= 255
    
    r, g, b, *_ = arr.T
    reg = np.all(np.abs(r - g) < epsilon)
    geb = np.all(np.abs(g - b) < epsilon)
    return reg and geb


def unmap(arr,
          cmap,
          crop=None,
          vrange=(0, 1),
          levels=256,
          nan_colours=None,
          background='w',
          threshold = 0.1,
          hillshade=False,
          quantize=False,
          ):
    """
    Unmap data, via a colourmap, from an image. Reverse false-colouring.

    Args:
        arr: NumPy array of image data.
        cmap: Either another array, or pixel extent of colourbar in image,
                or name of mpl colourbar or if None, just use lightness (say)
                If get pixels and they're a few wide, then average them along
                short axis? Again, depends on scatter.
        crop: If not None, crop the image to the given rectangle.
            Given as a tuple (left, top, right, bottom).
        vrange: (vmin, vmax) for the colourbar.
        levels: Number of colours / value levels desired, default 256.
        nan_colours: Colours to turn to NaN? Treat essentially like background.
                        Combine these args? 
        background: Give background pixel location so can get this, or can be
                    'white'/w or 'black'/k, or RGB, or use the most common 
                    pixel colour with 'common'.
        threshold: 0 is exact match only, 1.732 is maximum distance and admits
                        all points.
        hillshade: Then use HSV
    
    Returns:
        A NumPy array of the same shape as the input image, with the colourmap
        removed. Essentially a greyscale image representing the data used to
        make the false colour image.
    """
    if is_greyscale(arr):
        return normalize(arr, vrange)

    # In future, maybe we also check for perceptually linear colours, and
    # just pass back the lightness channel if so.

    # In future, we may be able to sense the colourmap, either from an ML
    # model, or analytically from the image.

    # Check and transform inputs to get codebook.
    arr, alpha = check_arr(arr)
    if nan_colours is None:
        nan_colours = np.array([]).reshape(0, 3)
    background = get_background_rgb(arr, background)
    cmap = get_cmap(cmap, arr=arr, levels=levels, quantize=quantize)
    colours = cmap(np.linspace(0, 1, levels))[..., :3]
    codebook = np.vstack([colours, nan_colours, background])

    if hillshade:
        arr, hill = remove_hillshade(arr)

    kdtree = cKDTree(codebook)
    dist, ix = kdtree.query(arr)

    # Remove anything that was inferred from too far, and background.
    ix = ix.astype(float)    
    ix[dist >= threshold] = np.nan
    ix[ix >= len(colours)] = np.nan

    if crop:
        ix = crop_out(ix, crop)
    
    return normalize(ix, vrange)
