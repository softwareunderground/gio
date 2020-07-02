#!/usr/bin/env python

import pandas as pd


def get_header_idx(fname):
    """
    Opens the file from fname and returns the row index corresponding to the
    header row (with all the column name field information)
    """    

    blanks = []
    with open(fname,'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith('Well'):
                blanks.append(i)
    return blanks[0] + 1


def get_colspacers(fname, ignore_blank_lines=True, flag='-'):
    """
    Finds the first line in the file that can be used to find the column spacing
    """
    
    with open(fname) as f:
        ignore = False
        while not ignore:
            line = f.readline()
            sline = line.strip()
            ignore = sline.startswith(flag)
    return line

def substring_indexes(substring, string):
    """ 
    Generate indices of where substring begins in string

    >>> list(find_substring('me', "The cat says meow, meow"))
    [13, 19]
    """

    last_found = -1  # Begin at -1 so the next position to search from is 0
    while True:
        # Find next index of substring, by starting after its last known position
        last_found = string.find(substring, last_found + 1)
        if last_found == -1:  
            break  # All occurrences have been found
        yield last_found
      
    
def read_fwf_with_skips(fname, searchfor=['--','Well'], main_column='Well name'):
    """
    Wraps the Pandas pd.read_fwf method to create a data frame from 
    a fixed with format file. Deals with the ugly situation where you 
    want to skip an unknown number of non-data rows that make a list of
    strings in the searchfo keyword (list)
    
    :param fname: path to file
    
    :param searchfor: list of strings in the first column that you want
      to ignore and not load into the DataFrame 
    :param main_column: type (str) name of the column to test whether row 
    shouuld be skipped
    
    returns: a dataframe of well tops
    """

    spacers = get_colspacers(fname) 
    column_indexes = list(substring_indexes(' ', spacers))
    header = get_header_idx(fname)
    df = pd.read_fwf(fname,  colspec=column_indexes, header=header, skip_blank_lines=True)
    # drop rows with nans in main_column col
    df = df[pd.notna(df[main_column])]
    # remove rows containing things in searchfor
    df = df[~df[main_column].str.contains('|'.join(searchfor))]
    return df