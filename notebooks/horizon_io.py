import numpy as np

def load_horizon(filename):
    def expand_range(value, the_range):
        if (value < the_range[0]):
            the_range[0] = value
        if (value > the_range[1]):
            the_range[1] = value
        return the_range
    inline_range = [9999999,-1]
    xline_range = [9999999,-1]
    z_range = [9999999,-1]
    values = []
    try:
        f = open(filename, 'r')
    except IOError:
        print('Count not open', filename)
        return None
    
    for line in f:
        il_xl_z = [float(x) for x in line.split()]
        inline_range = expand_range(int(il_xl_z[0]), inline_range)
        xline_range = expand_range(int(il_xl_z[1]), xline_range)
        z_range = expand_range(il_xl_z[2], z_range)
        values.append(il_xl_z)
        
    info = {}
    info['inline_range'] = inline_range
    info['xline_range'] = xline_range
    info['z_range'] = z_range
        
    # not taking into account increments > 1
    h = -1*np.ones((inline_range[1]-inline_range[0]+1, xline_range[1]-xline_range[0]+1))
    for v in values:
        il = int(v[0]-inline_range[0])
        xl = int(v[1]-xline_range[0])
        h[il, xl] = v[2]

    h[h == -1] = np.nan
        
    return h, info

def extract_map(volume, horizon):
    map_seismic = np.zeros_like(horizon, dtype=float)
    for i in range(map_seismic.shape[0]):
        for x in range(map_seismic.shape[1]):
            map_seismic[i,x] = volume[horizon[i,x],i,x]
    return map_seismic

def extract_map_i(volume, horizon):
    from scipy import ndimage
    map_seismic = np.zeros_like(horizon, dtype=float)
    dx, di = np.meshgrid(range(map_seismic.shape[1]), range(map_seismic.shape[0]))
    print(volume.shape, di.shape)
    map_seismic = ndimage.interpolation.map_coordinates(volume, [horizon, di, dx], order=1)
    return map_seismic