# -*- coding: utf-8 -*-
"""
Special case: binning data with only (x, y) coords.

:copyright: 2022 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np
import scipy.spatial.distance as sd
from scipy.stats import gaussian_kde
from scipy.signal import find_peaks
from scipy.interpolate import interp1d


def nearest_neighbours(x, y, precision=5):
    """
    Vector between 2 closest points. If there's a tie (there
    likely will be), then we get the first point with a minimally
    nearest neighbour (and its first such neighbour).
    
    The precision cut-off is needed to deal with floating-point
    imprecision.
    """
    X = np.array([x, y]).T
    
    # Make the pairwise distance matrix, D.
    D = sd.squareform(sd.pdist(X))
    D[D==0] = np.inf
    D = np.round(D, decimals=precision)

    # Find the minimum distance, considering all pairs.
    dmin = np.argmin(D)
    
    # Get the first point p and its near neighbour.
    p = X[dmin // len(x)]
    q = X[dmin % len(x)]
    
    return p - q


def rectify(X, vector):
    """
    Rotate the geometry X, which should have columns
    (x, y, data). Data can be anything, just ones if
    you only have points to transform.
    """
    # Figure out the angle of the given vector.
    θ = np.angle(complex(*vector))
    
    # Affine transformation matrix.
    A = np.array([[np.cos(θ), -np.sin(θ), 0],
                  [np.sin(θ),  np.cos(θ), 0],
                  [        0,          0, 1]])
    
    # Apply the transformation and return.
    return X @ A


def parabolic(f, x):
    """
    Quadratic interpolation for estimating the true position of an
    inter-sample maximum when nearby samples are known.
   
    f is a vector and x is an index for that vector.
   
    Returns (vx, vy), the coordinates of the vertex of a parabola that goes
    through point x and its two neighbors.
   
    Example:
    Defining a vector f with a local maximum at index 3 (= 6), find local
    maximum if points 2, 3, and 4 actually defined a parabola.
   
    >>> import numpy as np
    >>> f = [2, 3, 1, 6, 4, 2, 3, 1]
    >>> parabolic(f, np.argmax(f))
    (3.2142857142857144, 6.1607142857142856)
    """
    xv = 1/2 * (f[x-1] - f[x+1]) / (f[x-1] - 2 * f[x] + f[x+1]) + x
    yv = f[x] - 1/4 * (f[x-1] - f[x+1]) * (xv - x)
    return (xv, yv)


def get_intervals(x):
    """
    From an unsorted and possibly sparse collection
    of 1D coordinates, compute the number of bins and
    the distance between bin centres.
    
    Default is nearest-metre precision, which should be
    fine for most seismic surveys.
    """
    # Preliminaries.
    x = np.asanyarray(x)
    assert x.ndim == 1, "Array must be 1D."
    xmax, xmin = x.max(), x.min()
    est = np.sqrt(x.size).astype(int)
    N = max(20 * est, 2500)
    pad = (xmax - xmin) / est

    # Construct the KDE to 'cluster' values.
    kde = gaussian_kde(x, bw_method=5e-3)
    x_eval = np.linspace(xmin - pad, xmax + pad, N)
    x_kde = kde.evaluate(x_eval)

    # Find the peaks in the KDE.
    peaks, _ = find_peaks(x_kde)
    n_peaks = len(peaks)
    
    # Get true positions as indices.
    x_pos, _ = parabolic(x_kde, peaks)

    # Get the coords at the actual peaks.
    M = x_eval.size
    idx = np.linspace(0, M-1, M)  # The indices.
    f = interp1d(idx, x_eval, kind='linear')
    x_best = f(x_pos)
    
    # Figure out the likely spacing.
    # Should be the smallest gap, but data is noisy and
    # the mean (minus any large spacings from gaps) is a
    # better estimate.
    vals = np.sort(np.diff(x_best))
    trim = np.mean(vals[n_peaks//4:-n_peaks//4])  # Central half of data.
    minn = vals[0]

    # If the values are close, take the mean; otherwise
    # take the minimum (may be very sparse data.)
    dx = trim if trim - minn < 1 else minn
    dx = np.round(dx, 2)
    
    # Compute the number of bins from the spacing.
    Nx = 1 + np.round((np.max(x) - np.min(x)) / dx, decimals=0).astype(int)

    return Nx, dx


def xy_to_grid(x, y, data, compute_array=False):
    """
    Bin a bunch of unsorted (x, y) datapoints into a regular grid.

    Returns:
        tuple:

            - arr (ndarray): The binned data.
            - (dx, dy): The spacing between bins in the x and y directions.
            - (addx, addy): The destination of each data point into the grid;
                n.b. this is given in NumPy (row, col) format.
    """
    # Create shapely points.
    X = np.vstack([x, y, data]).T
    
    # Get nearest neighbour and rectify.
    v = nearest_neighbours(x, y)
    p = rectify(X, v)

    x_new, y_new, _ = p.T  # Data has not changed.

    Nx, dx = get_intervals(x_new)
    Ny, dy = get_intervals(y_new)
    
    xedge = np.linspace(np.min(x_new) - dx / 2, np.max(x_new) + dx / 2, Nx + 1)
    yedge = np.linspace(np.min(y_new) - dy / 2, np.max(y_new) + dy / 2, Ny + 1)
    
    assert np.all(data > 0), "Data are not strictly positive; see docs."

    # Don't strictly need to do this if we don't want the array.
    # (Don't need it for the OdT loading workflow.)
    if compute_array:
        arr, *_ = np.histogram2d(y_new, x_new, bins=[yedge, xedge], weights=data)
        arr[arr == 0] = np.nan
    else:
        arr = None
    
    # Find destination 'address' of each sample.
    addx = np.digitize(x_new, xedge) - 1  # No 'outer' bin.
    addy = np.digitize(y_new, yedge) - 1

    # Adjust addy to account for numbering of rows in array.
    addy = Ny - addy

    return arr, (dx, dy), (addy, addx)
