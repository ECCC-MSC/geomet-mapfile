# GeoMet-Mapfile

## Overview

geomet-mapfile manages [MapServer](https://mapserver.org) mapfiles and provides WMS services on top of [geomet-data-registry](https://github.com/ECCC-MSC/geomet-data-registry).

mapfile management is done either on disk (default) or using a store backend (e.g. Redis).

## Installation

### Requirements

- Python 3
- [virtualenv](https://docs.python.org/3/library/venv.html) or [conda](https://docs.conda.io/en/latest/miniconda.html)

### Dependencies

Dependencies are listed in [requirements.txt](https://github.com/ECCC-MSC/geomet-mapfile/blob/master/requirements.txt). Dependencies are automatically installed during geomet-mapfile installation.

### Installing

```bash
# setup system wide packages
sudo apt-get install python-mapscript

# setup virtualenv
python3 -m venv --system-site-packages geomet-mapfile
cd geomet-mapfile
. bin/activate

# clone codebase and install
git clone https://github.com/ECCC-MSC/geomet-mapfile.git
cd geomet-mapfile
pip install -r requirements.txt
pip install -r requirements-dev.txt
python setup.py install

# configure environment
cp geomet-mapfile.env local.env
vi local.env  # edit paths accordingly
. local.env
```

## Running

```bash
# help
geomet-mapfile --help

# version
geomet-mapfile --version

# see all subcommands
geomet-mapfile

# generate a mapfile for GDPS.ETA_TT without the `MAP` object and write to the configured store
geomet-mapfile mapfile generate -l GDPS.ETA_TT --no-map -o store

# generate complete mapfiles (with `MAP` object) for all layers in the GeoMet configuration and write them to disk
geomet-mapfile mapfile generate -o file

# read an existing GeoMet-Weather style file and removes unnecessary parameters (i.e CLASSGROUP, GEOTRANSFORM, etc.)
# useful for generating acceptable mappyfile style JSON objects from existing GeoMet-Weather styles

# generate mappyfile-ready JSON objects from existing GeoMet-Weather mapfiles
geomet-mapfile utils clean_styles -d /path/to/styles-dir -o . -of json

# store management

# get a key from the store.
geomet-mapfile store get -k GDPS.ETA_TT

# set a key in the store.
geomet-mapfile store set -k GDPS.ETA_TT -m /path/to/geomet-weather-GDPS.ETA_TT_en.map
```

## Development

### Running Tests

```bash
python setup.py test
```

### Cleaning the build of artifacts
```bash
python setup.py cleanbuild
```

## Releasing

```bash
python setup.py sdist bdist_wheel --universal
twine upload dist/*
```

### Code Conventions

* [PEP8](https://www.python.org/dev/peps/pep-0008)

### Bugs and Issues

All bugs, enhancements and issues are managed on [GitHub](https://github.com/ECCC-MSC/geomet-mapfile).

## Contact

* [Etienne Pelletier](https://github.com/Dukestep)
* [Louis-Philippe Rousseau Lambert](https://github.com/RousseauLambertLP)
* [Tom Kralidis](https://github.com/tomkralidis)
