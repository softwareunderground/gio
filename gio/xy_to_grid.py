import numpy as np
import scipy.spatial.distance as sd

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


def get_intervals(x, precision=0):
    """
    From an unsorted and possibly sparse collection
    of 1D coordinates, compute the number of bins and
    the distance between bin centres.
    
    Default is nearest-metre precision, which should be
    fine for most seismic surveys.
    """
    diffs = np.diff(np.sort(np.unique(np.round(x, decimals=precision))))
    dx = diffs.min()
    Nx = 1 + np.round((np.max(x) - np.min(x)) / dx, decimals=0).astype(int)
    return Nx, dx


def xy_to_grid(x, y, data):
    """
    Bin a bunch of unsorted (x, y) datapoints into a regular grid.

    Data must be positive, otherwise you might lose some data points.
    Anything that sums to 0 in its bin will be turned into NaNs.

    Returns the grid, and the grid cell dimensions (dx, dy).
    """
    X = np.vstack([x, y, data]).T
    
    # Get nearest neighbour and rectify.
    v = nearest_neighbours(x, y)
    p = rectify(X, v)

    x_new, y_new, _ = p.T  # Data has not changed.

    # Infer the geometric parameters.
    Nx, dx = get_intervals(x_new)
    Ny, dy = get_intervals(y_new)
    
    assert np.all(data > 0), "Data are not strictly positive; see docs."

    # Bin the data points into the grid.
    arr, *_ = np.histogram2d(y_new, x_new, bins=[Ny, Nx], weights=data)
    arr[arr == 0] = np.nan

    return arr, (dx, dy)
