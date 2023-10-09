# Only testing that it functions without error, not that it is correct.
import matplotlib.pyplot as plt
from io import BytesIO

import gio

def test_logo():
    gio.plot(fname=BytesIO())
    plt.close('all')