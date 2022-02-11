# Installation

At the command line:

    $ pip install redflag

Or, if you use Conda environments:

    $ conda create -n redflag python=3.9
    $ conda activate redflag
    $ pip install redflag

Installing `scikit-learn` allows you to access some extra options for outlier detection:

    pip install redflag[sklearn]

For developers, there are also options for installing `tests`, `docs` and `dev` dependencies.

If you want to help develop Redflag, please read [Development](development.md).
