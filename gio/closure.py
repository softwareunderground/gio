"""
Closed-contour-related functions.

Author: Rob Gooder, Matt Hall
License: MIT License

Copyright (c) 2023 Rob Gooder, Matt Hall

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from typing import List

import numpy as np
from numpy.typing import ArrayLike
import scipy.ndimage as ndimage
from skimage import measure
from shapely.geometry import Polygon


def closure_height(arr: ArrayLike, c: ArrayLike) -> float:
    """
    Check that the max height is greater than the level.

    This is rather slow, so do it on the fewest possible candidates.
    """
    # Create an empty image to store the masked array
    mask = np.zeros_like(arr, dtype='bool')

    # Create a contour image by using the contour coordinates rounded to their nearest integer value
    mask[np.round(c[:, 1]).astype('int'),np.round(c[:, 0]).astype('int')] = 1

    # Fill in the hole created by the contour boundary
    mask = ndimage.binary_fill_holes(mask)

    return np.nanmax(arr[mask])


def is_high(arr: ArrayLike, p: Polygon, step:float = 1.0) -> bool:
    """
    Decide if polygon p encloses a high region on grid z (returns True), or a
    low region (False).

    This is much faster than closure_height and can help reduce the number of
    times we run that.

    Sometimes the erosion buffer can result in more than 1 polygon, which tries
    to get `exterior` on a MultiPolygon, which fails. Could maybe do
    Polygon.boundary.xy instead, I think that works for MultiPolygon?
    """
    x, y = p.exterior.xy
    sample = arr[np.floor(y).astype('int'), np.floor(x).astype('int')]

    # Step inside the polygon.
    x, y = p.buffer(step).exterior.xy
    sample_in = arr[np.floor(y).astype('int'), np.floor(x).astype('int')]

    return sample.mean() > sample_in.mean()


def is_closed(c: ArrayLike) -> bool:
    """
    Determine if the last point is the same as the first.
    """
    return all(c[0] == c[-1])


def find_closures(arr: ArrayLike,
                  interval: float = 1.0,
                  min_area: float = 0.0,
                  min_height: float = 0.0
                  ) -> List[Polygon]:
    """
    Find the largest closed contour in a grid.

    Args:
        arr (ndarray): The grid to search.
        interval (int): The interval between contours to consider, default 1 unit.
        min_area (int): The minimum area of a closure to consider, in grid squares.
        min_closure (int): The minimum closure of a closure to consider, in z units.

    Returns:
        list of shapely.geometry.Polygon: The list of polygons that meet the criteria.

    TODO:
        - Accept an xarray with real-world coordinates and use appropriate units.
        - Test what happens if pass an xarray [Seems ok]
        - Test what happens if grid is partly or completely negative [Seems ok]
        - Test what happens if there are NaNs. [Seems ok]
        - Test what happens if there are no closures. [Seems ok]
        - Test what happens if there are donut highs. Need to add holes to Polygon.
    """
    arr_ = np.asarray(arr)

    levels = np.arange(int(np.nanmin(arr)), np.nanmax(arr)-min_height+interval, interval)

    all_contours = []

    for level in levels:
        # Gives row (y), column (x) coordinates.
        contours = measure.find_contours(arr_, level)

        # Keep only closed contours with no NaNs.
        contours = [c for c in contours if is_closed(c) and ~np.isnan(c).any()]

        # Capture all contours that are high enough.
        for contour in contours:

            y_, x = contour.T  # y_ is row *from top* of array
            contour = np.stack([x, y_, np.ones_like(x)*level]).T
            p = Polygon(contour)

            # Do various tests.
            if p.area < min_area: continue
            if not is_high(arr_, p): continue
            if any([p.within(c) for c in all_contours]): continue
            if (closure_height(arr_, contour) - level) < min_height: continue

            # What's left is a good closure.
            all_contours.append(p)

    return all_contours
