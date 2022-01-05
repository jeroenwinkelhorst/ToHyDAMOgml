from codecs import open
from os import path

from setuptools import setup, find_packages

import tohydamogml

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=tohydamogml.__title__,
    version=tohydamogml.__version__,
    description=tohydamogml.__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',

    # The project's main homepage.
    url=tohydamogml.__url__,

    # Author details
    author=tohydamogml.__author__,
    author_email=tohydamogml.__author_email__,

    # Choose your license
    license=tohydamogml.__license__,

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Topic :: RHDHV :: Water Management',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3',
    ],

    keywords=tohydamogml.__keywords__,

    packages=find_packages(include=['tohydamogml']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
    'fiona',
    'shapely',
    'pyproj',
    'rtree',
    'lxml',
    'geopandas',
    'arcgis'
    ],

    # You can install these using the following syntax, for example:
    # $ pip install -e .[dev,test]
    # extras_require={
    #     'dev': ['tests'],
    # },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        '': ['examples/*'],
    },
    # include_package_data=True,

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points={
    #     'console_scripts': [
    #         'xsb=xsboringen.scripts.xsb:main',
    #     ],
    # },
)
