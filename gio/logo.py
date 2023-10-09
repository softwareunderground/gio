"""
Make gio's logo.

Author: Matt Hall
License: Apache 2.0
"""
import hashlib

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap

from .random import generate_random_surface


def plot(ax=None, fname=None):
    """
    Plots as a side effect. Pass in a 3d Axes if you want. Pass a filename
    to save the plot.
    """
    seed = int(hashlib.sha1("gio".encode()).hexdigest(), 16)

    if ax is None:
        fig = plt.figure(figsize=(12, 12))
        fig.patch.set_facecolor('none')
        ax = fig.add_subplot(projection='3d', facecolor='none')

    ax.set_box_aspect(aspect = (1,1,0.75))
    X = np.arange(0, 32)
    Y = np.arange(0, 32)
    X, Y = np.meshgrid(X, Y)
    Z = generate_random_surface(32, res=2, octaves=2, random_seed=seed)
    Z = 240 * Z + 240
    ax.axis('off')

    ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='RdBu')
    ax.plot_wireframe(X, Y, Z, color='k', lw=0.5, alpha=0.75)
    c = get_cmap('gray')
    ax.text(-10, 20, 220, r"$\mathbf{gio}$", size=240, zorder=10, color=c(0.15))
    ax.set_zlim(0, 1200)

    if fname is not None:
        plt.savefig(fname, dpi=200, bbox_inches='tight')
    else:
        plt.show()

    return ax
