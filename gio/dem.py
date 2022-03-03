"""
Read 2D ASCII/binary Surfer grid files.

:copyright: 2022 Agile Geoscience (this adaptation)
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

    return arr
