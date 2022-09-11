"""
Read E00 format DEM (digital elevation model) files.

THIS IS A WORK IN PROGRESS.  IT DOES NOT WORK YET.

:copyright: 2022 Agile Geoscience
:license: Apache 2.0
"""
import numpy as np
import re


def read_e00_text(fname):
    """
    Parse a bunch of E00 formatted text and emit a NumPy array.
    """
    with open(fname, 'rt') as f:
        text = f.read()

    p = re.compile(r"^EXP\s+\d+\s+(.+?)\s+$", flags=re.MULTILINE)
    exp, = p.search(text).groups()

    p = re.compile(r"GRD\s+\d\s+(\d+)\s+(\d+)\s+[-+.E\d]+\s+(.+?)EOG", flags=re.DOTALL)
    nx, ny, data = p.search(text).groups()

    p = re.compile(r"LOG(.+?)EOL", flags=re.DOTALL)
    log, = p.search(text).groups()

    p = re.compile(r"PRJ(.+?)EOP", flags=re.DOTALL)
    prj, = p.search(text).groups()

    p = re.compile(r"IFO(.+?)EOI", flags=re.DOTALL)
    ifo, = p.search(text).groups()

    # Unflatten this thing.
    values = []
    for row in data:
        for col in row:
            values.append(float(col))

    # Convert to an array and reshape.
    arr = np.array(values).reshape(ny, nx)

    return arr
