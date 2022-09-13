import warnings

import numpy as np
from scipy.spatial import cKDTree
from skimage.color import rgb2hsv, hsv2rgb
from collections import Counter
from matplotlib.colors import to_rgb, LinearSegmentedColormap
from matplotlib import cm


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
        warnings.warn('Grayscale image cannot be transformed; it is already the data.')
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
        c = Counter(arr.reshape(-1, c)[ix])
        bg = c.most_common(1)
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
    hsv_im = rgb2hsv(img)
    val = 1 - hsv_im[..., 2]
    hillshade = val[..., None] * [0, 0, 0, 1]
    hsv_im[..., 2] = 1.0
    return hsv2rgb(hsv_im), hillshade


def check_cmap(cmap, levels=256):
    """
    Turn whatever we get as a colourmap into a matplotlib cmap.
    
    Could try adding some options later, possibly as other arguments:
        - Pass an image URI
        - Pass a tuple of coordinates to extract the cbar from the main image

    Args:
        cmap: Either a matplotlib cmap, or a NumPy array of colours.
        levels: Number of colours / value levels desired, default 256.

    Returns:
        A matplotlib cmap.
    """
    if isinstance(cmap, str):
        try:
            cmap = cm.get_cmap(cmap)
        except ValueError:
            raise ValueError("cmap name not recognized by matplotlib")
    else:
        try:
            cmap = LinearSegmentedColormap.from_list('', cmap, N=levels)
        except TypeError as e:
            raise TypeError("cmap must be a str (name of a matplotlib cmap) or an array-like of RBG triples.")
    return cmap


def unmap(arr,
          cmap,
          vrange=(0, 1),
          levels=256,
          nan_colours=None,
          background='w',
          threshold = 0.1,
          hillshade=False):
    """
    Unmap data, via a colourmap, from an image. Reverse false-colouring.

    Args:
        arr: NumPy array of image data.
        cmap: Either another array, or pixel extent of colourbar in image,
                or name of mpl colourbar or if None, just use lightness (say)
                If get pixels and they're a few wide, then average them along
                short axis? Again, depends on scatter.
        vrange: (vmin, vmax) for the colourbar.
        levels: Number of colours / value levels desired, default 256.
        nan_colours: Colours to turn to NaN? Treat essentially like background.
                        Combine these args? 
        background: Give background pixel location so can get this, or can be
                    'white'/w or 'black'/k, or RGB, or try to sense if 'auto'
        threshold: 0 is exact match only, 1.732 is maximum distance and admits
                        all points.
        hillshade: Then use HSV
    
    Returns:
        A NumPy array of the same shape as the input image, with the colourmap
        removed. Essentially a greyscale image representing the data used to
        make the false colour image.
    """
    # Check or transform the inputs.
    arr, alpha = check_arr(arr)
    cmap = check_cmap(cmap)
    background = get_background_rgb(arr, background)
    if nan_colours is None:
        nan_colours = np.array([]).reshape(0, 3)

    # Get the colours from the cmap provided.
    colours = cmap(np.linspace(0, 1, levels))[..., :3]
    
    # Add the 'nan' and background colours to make the codebook.
    codebook = np.vstack([colours, nan_colours, background])

    # Make the KD tree.
    kdtree = cKDTree(codebook)
    
    # Remove the hillshade if required.
    if hillshade:
        arr, hill = remove_hillshade(arr)

    # Get the index (ix) of the closest colour to each pixel in px.
    dist, ix = kdtree.query(arr)
    
    ix = ix.astype(float)
    
    # Clean up anything that was looked up from too far away.
    ix[dist >= threshold] = np.nan
    
    # Remove the background etc colours.
    ix[ix >= len(colours)] = np.nan
    
    # Scale the image, assuming it goes from 0 to 'whatever'.
    mi, ma = vrange
    ix = ix / np.nanmax(ix)
    ix = (ma - mi) * ix + mi
    
    return ix
