import pprint
import traceback
from pathlib import Path

import lasio
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd



def read_geo_file(filename):
    """Read and parse a .geo file from disk
    
    Args:
        filename (str, pathlib.Path): 
        
    Returns: list of parsed sections
    
    Each section is parsed by :func:`parse_geo_section`.
    
    """
    fn = Path(filename)
    sections = []
    with open(fn, "r") as f:
        sect_type = None
        sect_lines = []
        for line in f:
            line = line.strip()
            if line.startswith("*CONSTANTS"):
                if sect_type is not None:
                    sections.append({"name": sect_type, "contents": sect_lines})
                sect_type = "constants"
                sect_lines = []
                continue
            elif line.startswith("*COMMENTS"):
                if sect_type is not None:
                    sections.append({"name": sect_type, "contents": sect_lines})
                sect_type = "comments"
                sect_lines = []
                continue
            elif line.startswith("*NAMES"):
                if sect_type is not None:
                    sections.append({"name": sect_type, "contents": sect_lines})
                sect_type = "names"
                sect_lines = []
                continue
            elif line.startswith("*DATA"):
                if sect_type is not None:
                    sections.append({"name": sect_type, "contents": sect_lines})
                sect_type = "data"
                sect_lines = []
            else:
                sect_lines.append(line)
        if sect_type is not None:
            sections.append({"name": sect_type, "contents": sect_lines})
    parsed_sections = []
    for section in sections:
        parsed_section = parse_geo_section(**section)
        if isinstance(parsed_section, pd.DataFrame):
            if parsed_section.empty:
                continue
        parsed_sections.append({"name": section["name"], "data": parsed_section})
    return parsed_sections


def parse_geo_section(name, contents):
    """Parse a section from a .geo file.
    
    Args:
        name (str): one of 'constants', 'comments', 'data', 'names'
        contents (list of str): contents of the section
        
    See :func:`parse_geo_constants_section`, :func:`parse_geo_comments_section`,
    :func:`parse_geo_data_section`, and :func:`parse_geo_names_section` for
    where all the action happens.
    
    If *name* is not one of the supported types, an `Exception` is raised.
    
    """
    if name == "constants":
        return parse_geo_constants_section(contents)
    elif name == "comments":
        return parse_geo_comments_section(contents)
    elif name == "data":
        return parse_geo_data_section(contents)
    elif name == "names":
        return parse_geo_names_section(contents)
    else:
        raise Exception("Unknown section type: " + pprint.pformat({"name": name, "contents": contents}))


def parse_geo_comments_section(contents):
    """Parse a COMMENTS section from a .geo file.
    
    Args:
        contents (list of str): contents of the section.
        
    Returns: string
    
    """
    sets = []
    set_lines = []
    for line in contents:
        if len(line) > 3 and line[:3] == "UHL":
            prefix = line[:4]
            value = line[4:]
            if prefix == "UHL1":
                if set_lines:
                    sets.append("\n".join([v for p, v in set_lines]))
                    set_lines = []
            else:
                set_lines.append((prefix, value))
    if set_lines:
        sets.append("\n".join([v for p, v in set_lines]))
    return sets


def parse_geo_constants_section(contents):
    """Parse a CONSTANTS section from a .geo file.
    
    Args:
        contents (list of str): contents of the section.
        
    Returns: pandas.DataFrame with columns header_param, header_value, and header_descr.
    
    """
    records = []
    for line in contents:
        param, line_1 = line.split("=")
        value, descr = line_1.split("/*")
        param = param.strip()
        value = value.strip()
        descr = descr.strip()
        records.append(
            {"header_param": param, "header_value": value, "header_descr": descr}
        )
    return pd.DataFrame(records)


def parse_geo_data_section(contents):
    """Parse a DATA section from a .geo file.
    
    Args:
        contents (list of str): contents of the section.
        
    Returns: pd.DataFrame with contents parsed as numeric values.
    
    """
    df = pd.DataFrame((line.split() for line in contents))
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce", downcast="integer")
    return df


def parse_geo_names_section(contents):
    """Parse a NAMES section from a .geo file.
    
    Args:
        contents (list of str): contents of the section.
        
    Returns: pd.DataFrame with columns curve_name, curve_unit, and curve_data_type.
    
    """
    records = []
    for line in contents:
        if line.startswith("$"):
            pass
        else:
            name, unit, data_type = line.split()
            records.append(
                {"curve_name": name, "curve_unit": unit, "curve_data_type": data_type}
            )
    return pd.DataFrame(records)

def consolidate_geo_file_sections(parsed_sections):
    """Interpret parsed .geo file as separate frames, with a header.
    
    Args:
        parsed_sections (list): result of :func:`read_geo_file`
        
    Returns: a dict with keys "header" and "frames". 
    
    Each frame has these keys:
    
        - "title": from the CONSTANTS section
        - "comments": from the COMMENTS section
        - "constants": pd.DataFrame (CONSTANTS section)
        - "data": pd.DataFrame (DATA section)
        - "data_step": possible data step - this is not always consistent
        - "names": pd.DataFrame (NAMES section)
    
    """
    frames = []
    constants = []
    names = []
    data = []
    header = pd.DataFrame()
    sect_type_counts = {}
    for section in parsed_sections:
        if not section["name"] in sect_type_counts:
            sect_type_counts[section["name"]] = 0
        n = sect_type_counts[section["name"]]
        if section["name"] == "constants":
            if n == 0:
                header = section["data"]
            else:
                constants.append(section["data"])
        elif section["name"] == "names":
            names.append(section["data"])
        elif section["name"] == "data":
            data.append(section["data"])
        elif section["name"] == "comments":
            comments = section["data"]
        sect_type_counts[section["name"]] += 1
    for i in range(len(data)):
        data[i].columns = names[i].curve_name
        if len(names[i]) > 1:
            title = "_".join(names[i].curve_name[1:].replace(" ", "_"))
        else:
            title = ""
        df = data[i].set_index(data[i].columns[0])
        data_step = df.index[1] - df.index[0]
        frames.append(
            {
                "title": constants[i].header_value.iloc[0],
                "comments": comments[i],
                "constants": constants[i],
                "data": df,
                "data_step": data_step,
                "names": names[i],
            }
        )
    return {"header": header, "frames": frames}


def rename_duplicate_name(dfs, name):
    """Remove duplicates of *name* from the columns in each of *dfs*.

    Args:
        dfs (list of pandas DataFrames)

    Returns: list of pandas DataFrames. Columns renamed
        such that there are no duplicates of *name*.
        
    """
    locations = []
    for i, df in enumerate(dfs):
        for j, col in enumerate(df.columns):
            if col == name:
                locations.append((i, j))
    if len(locations) > 1:
        current_count = 1
        for k, (i, j) in enumerate(locations):
            cols = list(dfs[i].columns)
            cols[j] = name + f":{k + 1:.0f}"
            dfs[i].columns = cols
    return dfs


def rename_duplicate_names(dfs):
    """Remove duplicate columns.

    Args:
        dfs (list of pandas DataFrames)

    Returns: list of pandas DataFrames. Columns renamed
        such that there are no duplicate column names.

    Example:

        >>> dfs = [
        ...     pd.DataFrame({"cat": [1, 2, 3], "dog": [4, 5, 6]}, index=[1, 2, 3]),
        ...     pd.DataFrame({"cow": [1, 2, 3], "sheep": [4, 5, 6]}, index=[1, 2, 3]),
        ...     pd.DataFrame({"cat": [1, 2, 3], "guinea pig": [4, 5, 6]}, index=[1, 2, 3]),
        ...     pd.DataFrame({"dog": [1, 2, 3], "koala": [4, 5, 6]}, index=[1, 2, 3]),
        >>> ]
        >>> dfs = rename_duplicate_names(dfs)
        >>> print(pd.concat(dfs, axis='columns'))
           cat:1  dog:1  cow  sheep  cat:2  guinea pig  dog:2  koala
        1      1      4    1      4      1           4      1      4
        2      2      5    2      5      2           5      2      5
        3      3      6    3      6      3           6      3      6

    """
    existing = []
    for df in dfs:
        for col in df.columns:
            existing.append(col)
    for test_name in set(existing):
        dfs = rename_duplicate_name(dfs, name=test_name)
    return dfs


class GeoFile(object):
    """Container class for .geo files."""
    
    @classmethod
    def read(cls, filename):
        """Parse and read a .geo file.
        
        Args:
            filename (str): name of .geo file.
            
        Returns: :class:`GeoFile` object.
            
        """
        self = cls()
        self.filename = Path(filename)
        self.sections = read_geo_file(filename)
        result = consolidate_geo_file_sections(self.sections)
        self.header = result["header"]
        self.frames = result["frames"]
        return self

    @property
    def frame_steps(self):
        return [f["data_step"] for f in self.frames]

    def to_lasfiles(self, from_frames="original"):
        """Convert .geo file to LAS files.
        
        Args:
            from_frames (str): either "original" or "reindexed".
                "original" creates a LAS file for each frame of the
                geo file. I recommend this. "reindexed" attempts to
                merge the frames together, but because of potentially
                different depth intervals, this does not always work well
                and I don't recommend it (for now).
                
        Returns: list of :class:`lasio.LASFile` objects.
        
        """
        assert from_frames in ("original", "reindexed")
        if from_frames == "original":
            names = [f["title"] for f in self.frames]
            comments = [f["comments"] for f in self.frames]
            dfs = [f["data"] for f in self.frames]
            units = [f["names"].curve_unit.values for f in self.frames]
        elif from_frames == "reindexed":
            reindexed = self.reindex_to_common_dataframes()
            names = []
            comments = []
            dfs = []
            units = []
            for name, reindexed_frame in self.reindex_to_common_dataframes().items():
                names.append(name)
                comments.append(reindexed_frame["comments"])
                dfs.append(reindexed_frame["data"])
                units.append(reindexed_frame["units"])

        las_files = {}
        for i, name in enumerate(names):
            las = lasio.LASFile()
            for idx, row in self.header.iterrows():
                las.params.append(
                    lasio.HeaderItem(
                        mnemonic=row.header_param,
                        value=row.header_value,
                        descr=row.header_descr,
                    )
                )
            las.set_data_from_df(dfs[i])
            for j, curve in enumerate(las.curves):
                curve.unit = units[i][j]
            las.other = comments[i]
            las_files[name] = las
        return las_files

    def reindex_to_common_dataframes(self):
        """Attempts to convert the DATA dataframes for each frame
        into a list of common-indexed dataframes.
        
        This is not likely to work smoothly - use with caution.
        
        """
        steps = set(self.frame_steps)
        reindexed_dfs = {}
        for step in steps:
            curves = []
            names = []
            dfs = []
            frames = [f for f in self.frames if f["data_step"] == step]
            comments = "\n".join(
                [f'------ Set {f["title"]} -------\n' + f["comments"] for f in frames]
            )
            title = "_".join([f["title"] for f in frames]) + f"_{step}"
            index_values = np.sort(
                np.unique(np.hstack([f["data"].index for f in frames]))
            )
            for i, frame in enumerate(frames):
                names = [f"{n}_{i}" for n in frame["names"]]
                frame_df = frame["data"]
                frame_df = (
                    frame_df.groupby(frame_df.index).transform("mean").drop_duplicates()
                )
                dfs.append(frame_df.reindex(index_values, method=None))
            dfs = rename_duplicate_names(dfs)
            df = pd.concat(dfs, axis="columns")
            units = []
            for f in frames:
                units += f["names"].curve_unit.tolist()
            reindexed_dfs[title] = {"comments": comments, "data": df, "units": units}
        return reindexed_dfs


def reindex_las_index_inplace(las):
    """Reindex a LAS file so that any irregularities in the index
    interval are smoothed out.
    
    Args:
        las (lasio.LASFile): input las.
        
    Returns nothing. Changes are made in place.
    
    """
    steps = las.index[1:] - las.index[:-1]
    unique_steps, step_counts = np.unique(steps, return_counts=True)
    if len(unique_steps) > 1:
        step_mode = unique_steps[np.argmax(step_counts)]
        min_index = np.nanmin(las.index)
        max_index = np.nanmax(las.index)
        steps_floor = np.int(np.floor(max_index - min_index) / np.abs(step_mode))
        n_steps = steps_floor + 1
        new_indices = np.round(
            np.linspace(min_index, min_index + n_steps * np.abs(step_mode), n_steps), 3
        )
        old_index = np.array(las.index)
        sorting_keys = np.argsort(old_index)
        for i, curve in enumerate(las.curves):
            if i == 0:
                curve.data = new_indices
            else:
                curve.data = np.interp(
                    new_indices,
                    old_index[sorting_keys],
                    curve.data[sorting_keys],
                    left=np.nan,
                    right=np.nan,
                )


def geo_to_lasfiles(
    fn,
    output_folder,
    reindex_frames=False,
    reindex_las=False,
    convert_to_m=False,
    overwrite=False,
):
    """Convert .geo file to LAS files.
    
    Args:
        fn (str): .geo file to be converted
        output_folder (str): folder in which to place LAS files.
        reindex_frames (bool): whether to attempt to reindex frames
            to a common basis (see :meth:`GeoFile.to_lasfiles`). I recommend
            AGAINST using `True` here, it will not work smoothly.
        reindex_las (bool): whether to reindex the LAS file so that it has a
            regular depth/index interval, which is usually required for many
            pieces of software reading LAS files.
        convert_to_m (bool): attempt to convert any depth units which are not
            metres, back into metres.
        overwrite (bool): overwrite any already-existing LAS files.
        
    """
    fn = Path(fn)
    output_folder = Path(output_folder)
    if reindex_frames:
        from_frames = "reindexed"
    else:
        from_frames = "original"
    geo = GeoFile.read(fn)
    for name, las in geo.to_lasfiles(from_frames=from_frames).items():
        las_fn = output_folder / (f"{fn.name}.{name}.las")
        if reindex_las:
            reindex_las_index_inplace(las)
        if convert_to_m:
            if las.curves[0].unit == "CM":
                las.curves[0].data = las.index / 100
                las.curves[0].unit = "M"
                las.index_unit = "M"
            elif las.index_unit == "FT":
                las.curves[0].data = las.depth_m
                las.curves[0].unit = "FT"
                las.index_unit = "M"
            if las.curves[0].unit == "METERS":
                las.curves[0].unit = "M"
        if not las_fn.is_file() or overwrite:
            with open(las_fn, "w") as f:
                las.write(f, version=2)