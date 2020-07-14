###############################################################################
#
# Copyright (C) 2020 Etienne Pelletier
# Copyright (C) 2020 Louis-Philippe Rousseau-Lambert
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import io
import os
import re
from setuptools import Command, find_packages, setup
import sys


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        errno = subprocess.call([sys.executable,
                                 'tests/run_tests.py'])
        raise SystemExit(errno)


class PyCoverage(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess

        errno = subprocess.call(['coverage', 'run', '--source=mscGeoUsage',
                                 '-m', 'unittest',
                                 'geomet_mapfile.tests.run_tests'])
        errno = subprocess.call(['coverage', 'report', '-m'])
        raise SystemExit(errno)


def read(filename, encoding='utf-8'):
    """read file contents"""
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with io.open(full_path, encoding=encoding) as fh:
        contents = fh.read().strip()
    return contents


def get_package_version():
    """get version from top-level package init"""
    version_file = read('geomet_mapfile/__init__.py')
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


try:
    import pypandoc
    LONG_DESCRIPTION = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError, OSError):
    print('Conversion to rST failed.  Using default (will look weird on PyPI)')
    LONG_DESCRIPTION = read('README.md')

DESCRIPTION = ('Extension of GeoUsage that indexes GeoMet log records in ES '
               'and adds further business logic of analyzing and creating '
               'metrics records.')

if os.path.exists('MANIFEST'):
    os.unlink('MANIFEST')

setup(
    name='geomet-mapfile',
    version=get_package_version(),
    description=DESCRIPTION.strip(),
    long_description=LONG_DESCRIPTION,
    license='MIT',
    platforms='all',
    keywords=' '.join([
        'geomet',
        'development'
    ]),
    author='Meteorological Service of Canada',
    author_email='etienne.pelletier@canada.ca',
    maintainer='Meteorological Service of Canada',
    maintainer_email='etienne.pelletier@canada.ca',
    url='https://gccode.ssc-spc.gc.ca/ec-msc/geomet-mapfile',
    install_requires=read('requirements.txt').splitlines(),
    packages=find_packages(exclude=['geomet_mapfile.tests']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'geomet-mapfile=geomet_mapfile:cli'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
    cmdclass={'test': PyTest, 'coverage': PyCoverage}
)
