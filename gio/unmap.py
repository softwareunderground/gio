import unmap

from .xarray import GridInfo

def unmap_to_dataarray(arr,
                       cmap,
                       extent=None,
                       dims=None,
                       **kwargs
                       ):
    """
    Unmap data, via a colourmap, from an image. Reverse false-colouring.

    Args:
        arr: NumPy array of image data.
        cmap: Either another array, or pixel extent of colourbar in image,
                or name of mpl colourbar or if None, just use lightness (say)
                If get pixels and they're a few wide, then average them along
                short axis? Again, depends on scatter.
        extent: The extent of the image, as a tuple (left, right, bottom, top),
            giving the real-world coordinates.
        dims (tuple): The dimensions of the image, as a tuple e.g. ('x', 'y')
            or ('Lon', 'Lat')).
        **kwargs: Passed to unmap.unmap.
    
    Returns:
        An xarray.DataArray of the same shape as the input image, with the
        colourmap removed.
    """
    da = unmap.unmap(arr, cmap, **kwargs)

    if extent is not None:
        xmin, xmax, ymin, ymax = extent
        dims = dims or ('x', 'y')
    else:
        xmin, xmax, ymin, ymax = 0, arr.shape[1], 0, arr.shape[0]
        dims = dims or ('i', 'j')

    return GridInfo(xmin=xmin, ymin=ymin,
                    xmax=xmax, ymax=ymax,
                    data=da, dims=dims,
                    ).to_xarray()
