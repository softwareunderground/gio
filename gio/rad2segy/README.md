# rad2segy

A utility for converting USRadar RA1/RA2/RAD files to SEG-Y or NumPy array.

Converting to SEG-Y requires ObsPy. Converting to NumPy array does not. All of it requires Python >3.4 and NumPy.


## Converting to SEG-Y

    python rad2segy.py /path/to/RAD/files/*.RA?


## Converting to NumPy

    from rad2np import read_rad
    file_header, trace_headers, arr = read_rad('filename.RA1')

