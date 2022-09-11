"""
I/O for ZMAP grid formats.

Author: Matt Hall
License: Apache 2.0
"""
import zmapio
import xarray as xr


def read_zmap(fname, add_attrs=True, add_comment='File read by gio.read_zmap'):
    """
    Read a ZMAP file and return an xarray.DataArray.

    Args:
        fname (str): path to ZMAP file.
        add_attrs (bool): if True, add the ZMAP file's metadata as attributes
            on the DataArray.
        add_comment (str or None): if not None, add this comment to the
            DataArray's comment attribute (after any found in the ZMAP file).

    Returns:
        xarray.DataArray
    """
    # Read file and transform to xr.DataArray.
    z = zmapio.ZMAPGrid(fname)
    df = z.to_pandas().set_index(['Y', 'X'])
    da = xr.DataArray.from_series(df['Z'])
    
    # Only way I can find to reorder the coordinates.
    da = xr.DataArray(da.data,
                      dims=['Y', 'X'],
                      coords={'X': da.coords['X'], 'Y': da.coords['Y']},
                      name=z.name
                      )

    if add_comment is None:
        comments = []
    elif isinstance(add_comment, str):
        comments = add_comment.split('\n')
    else:
        comments = add_comment  # list

    if add_attrs:
        attrs = {
            'fname': fname,
            'null_value': z.null_value,
        }

        if z.comments or comments:
            attrs['comment'] = z.comments + comments
    else:
        attrs = {}

    # Capture metadata and return.
    return da.assign_attrs(attrs)


def array_to_zmap(fname,
                  arr,
                  extent=None,
                  comment='File created by gio.array_to_zmap',
                  nodes_per_line=6,
                  field_width=12,
                  precision=3,
                  null_value=-999.25,
                  name='Z',
                  ):
    """
    Write a NumPy array as a ZMAP dat file.

    Args:
        fname (str): path to output file.
        arr (np.ndarray): 2D array to write.
        extent (None or list): if not None, should be a list of 4 numbers
            representing the extent of the array in real-world coordinates, in
            the order [min_x, max_x, min_y, max_y].
        comment (str or list): comment to add to the file.
        nodes_per_line (int): number of values to write per line.
        field_width (int): character width of each value field.
        precision (int): number of decimal places to write.
        null_value (float): value to use for NaN values.
        name (str): name of the variable in the file.

    Returns:
        None
    """
    if arr.ndim != 2:
        raise ValueError('Array arr must be 2D.')

    if extent is None:
        rows, cols = arr.shape
        min_x, max_x, min_y, max_y = 0, cols, 0, rows
    else:
        min_x, max_x, min_y, max_y = extent

    zgrid = zmapio.ZMAPGrid(z_values=arr[::-1].T,  # Horrible; apparently required by zmapio library.
                            min_x=min_x, max_x=max_x,
                            min_y=min_y, max_y=max_y)

    if isinstance(comment, str):
        comments = comment.split('\n')
    else:
        comments = comment

    zgrid.comments = comments
    zgrid.nodes_per_line = nodes_per_line
    zgrid.field_width = field_width
    zgrid.decimal_places = precision
    zgrid.null_value = null_value
    zgrid.name = name

    zgrid.write(fname)

    return None


def dataarray_to_zmap(fname,
                      da,
                      coords=None,
                      comment_attr='comments',
                      add_comment='File created by gio.dataarray_to_zmap',
                      nodes_per_line=6,
                      field_width=12,
                      precision=3,
                      null_value=-999.25,
                      ):
    """
    Write an xarray.DataArray as a ZMAP dat file. For now we assume that dx is
    a DataArray.

    Args:
        fname (str): path to output file.
        da (xarray.DataArray): 2D array to write.
        coords (None or str): If coords is None, then the first two coordinates
            are assumed to represent x and y respectively. If this is not the
            case, pass a single string with a comma separating the names of the
            coordinates to use, eg `"UTMx,UTMy"`. Note that the order of the
            coordinates might be different from the order of the dimensions in
            the DataArray (which is often y, x).
        comment_attr (str or None): the name of the DataArray attribute to use
            as a comment in the file, if any. If None, no comments are passed
            from the DataArray to the file.
        add_comment (str or list or None): comment to add to the end of any
            comments found in the DataArray. If None, no comment is added.
        nodes_per_line (int): number of values to write per line.
        field_width (int): character width of each value field.
        precision (int): number of decimal places to write.
        null_value (float): value to use for NaN values.

    Returns:
        None
    """
    if coords is None:
        x_coord, y_coord = list(da.coords.keys())[:2]  # Rows, columns.
    else:
        try:
            x_coord, y_coord = [i.strip() for i in coords.split(',')]
        except:
            raise ValueError('Could not find coordinates; give a string with commas to separate the coords representing real-world x and y respectively.')

    min_x, max_x = [d.item() for d in da.coords[x_coord][[0, -1]]]
    min_y, max_y = [d.item() for d in da.coords[y_coord][[0, -1]]]

    # Gather metadata from DataArray.
    if comment_attr is None:
        comment = []
    else:
        comment = da.attrs.get(comment_attr, [])
        if isinstance(comment, str):
            comment = comment.split('\n')

    if add_comment is not None:
        comment.extend(add_comment.split('\n'))

    return array_to_zmap(fname,
                         da.data,
                         extent=[min_x, max_x, min_y, max_y],
                         comment=comment,
                         nodes_per_line=nodes_per_line,
                         field_width=field_width,
                         precision=precision,
                         null_value=null_value,
                         name=da.name,
                         )
