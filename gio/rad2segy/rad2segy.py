#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert USRadar RA? files to SEG-Y.

:copyright: 2017 Agile Geoscience

:license: GNU Lesser General Public License, Version 3
"""
import os
import argparse
import glob

from obspy.core import Stats
from obspy.core import Trace, Stream
from obspy.io.segy.segy import SEGYBinaryFileHeader
from obspy.io.segy.segy import SEGYTraceHeader

from notice import Notice
from rad2np import read_rad

BANDS = {
    '.RA1': 'CH2',
    '.RA2': 'CH3',
    '.RAD': 'CH1',
}


def rad2segy(fname, outfile):

    file_header, trace_headers, arr = read_rad(fname)

    dt = int(file_header.get('SPR_SAMPLING_INTERVAL', 0))

    out = Stream()
    out.stats = Stats()

    # Text header.
    header = ['Created by seg22segy.',
              'More info to come.',
              ]
    out.stats.textual_file_header = ''.encode()
    for line in header:
        out.stats.textual_file_header += '{:80s}'.format(line).encode()

    # Binary header.
    out.stats.binary_file_header = SEGYBinaryFileHeader()
    out.stats.binary_file_header.trace_sorting_code = 4
    out.stats.binary_file_header.sample_interval_in_microseconds_of_original_field_recording = dt
    out.stats.binary_file_header.seg_y_format_revision_number = 0x0100

    # Trace data.
    for i, trace in enumerate(arr):

        # Make the trace.
        tr = Trace(trace)

        # Add required data.
        tr.stats.delta = dt / 1e6  # In microseconds.
        tr.stats.starttime = 0  # Not strictly required.

        # Add yet more to the header (optional).
        tr.stats.segy = {'trace_header': SEGYTraceHeader()}
        tr.stats.segy.trace_header.trace_sequence_number_within_line = i + 1
        tr.stats.segy.trace_header.receiver_group_elevation = 0
        tr.stats.segy.trace_header.sampling_rate = 1 / dt

        # Append the trace to the stream.
        out.append(tr)

    outbase, ext = os.path.splitext(fname)
    outfile = outfile or '{}_{}.sgy'.format(outbase, BANDS[ext])
    out.write(outfile, format='SEGY', data_encoding=3)  # 3:int16, 5:float32

    return outfile


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Convert a RAD file to SEG-Y.')
    parser.add_argument('filename',
                        metavar='RAD file',
                        type=str,
                        nargs='*',
                        default='./*.RA[D,1,2]',
                        help='The path to one or more RAD files. Uses Unix-style pathname expansion. Omit to find all RAD files in current directory.')
    parser.add_argument('-o', '--out',
                        metavar='output file',
                        type=str,
                        nargs='?',
                        default='',
                        help='The path to an output file. Default: same as input file, but with the nominal frequency and sgy file extension.')
    args = parser.parse_args()

    Notice.header("This is rad2segy. Stand back.")
    for f in args.filename:
        Notice.info("{}".format(f), hold=True)
        Notice.ok(" >>> ", hold=True)
        outfile = rad2segy(f, args.out)
        Notice.info(outfile)
    Notice.header("Done")
