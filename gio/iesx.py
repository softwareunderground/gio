import re
import warnings

import numpy as np
import pandas as pd
from shapely.geometry import Point, LineString

try:
    import geopandas as gp
    geopandas_is_available = True
except ImportError:
    geopandas_is_available = False


def read_iesx_from_petrel(filename, threed=False):
    """
    Read a Petrel IESX file and create a GeoPandas DataFrame.
    """
    warnings.warn("This function is broken.")
    with open(filename, 'rt') as f:
        points, linestrings, names, datasets, linenames = [], [], [], [], []
        last_cdp = 0
        skip = False
        
        for line in f:
            line = line.strip()        
            if not line:
                # End of file
                break
            elif line.startswith('EOD'):
                # End of horizon
                last_cdp = 0 # Force capture
            elif line.startswith('SNAPPING'):
                continue
            elif line.startswith('PROFILE'):
                name = re.search(r'PROFILE (.+?) +TYPE', line).group(1)
                
                # Some 'label' horizons slipped though, skip 'em.
                if name.startswith('---'):
                    skip = True
                else:
                    skip = False
            else:
                if skip == True:
                    continue
                
                line = line.split()
                x, y = float(line[0]), float(line[1])
                twtt = float(line[4])
                linename, dataset = line[-1].split('::')

                if threed:
                    this_cdp = int(line[5]) + int(line[9])
                else:
                    this_cdp = int(line[7])

                if abs(this_cdp - last_cdp) < 2:
                    # Then it's a regular line, so keep adding.
                    points.append(Point(x, y, twtt))
                    last_cdp = this_cdp
                else:
                    if len(points) < 2:
                        last_cdp = this_cdp
                        continue

                    # Capture what we have.
                    linestrings.append(LineString(points))
                    names.append(name)
                    linenames.append(linename)
                    datasets.append(dataset)
                    zs = [p.z for p in points]

                    # Reset segment and carry on.
                    last_cdp = this_cdp
                    points = [Point(x, y, twtt)]

    data_dict = {'geometry': linestrings,
                 'horizon': names,
                 'linename': linenames,
                 'dataset': datasets,
                 'min': np.min(zs),
                 'max': np.max(zs),
                 'mean': np.mean(zs),
                 'points': len(points)
                 }

    if geopandas_is_available: 
        return gp.GeoDataFrame(data_dict, geometry='geometry')
    else:
        return pd.DataFrame(data_dict)


def check_dialect(fname):
    """
    Decide if IESX file is from Petrel or OpendTect.
    """
    pass
