from setuptools import setup
from pathlib import Path

CLASSIFIERS = ['Development Status :: 3 - Alpha',
               'Intended Audience :: Science/Research',
               'Natural Language :: English',
               'License :: OSI Approved :: Apache Software License',
               'Operating System :: OS Independent',
               'Programming Language :: Python',
               'Programming Language :: Python :: 3.8',
               'Programming Language :: Python :: 3.9',
               'Programming Language :: Python :: 3.10',
              ]

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='gio',
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    url='https://github.com/agile-geoscience/gio',
    author='Agile Scientific',
    author_email='hello@agilescientific.com',
    description='Create xarray.DataArrays from various subsurface data formats.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['gio'],
    license_files = ('LICENSE',),
    classifiers=CLASSIFIERS,
    install_requires=['xarray', 'shapely'],
    tests_require=['pytest', 'pytest-cov'],
    test_suite='python run_tests.py'
)