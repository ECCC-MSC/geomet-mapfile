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

import logging
import os

from geomet_mapfile.util import str2bool


LOGGER = logging.getLogger(__name__)

LOGGER.info('Fetching environment variables')

BASEDIR = os.environ.get('GEOMET_MAPFILE_BASEDIR', None)
CONFIG = os.environ.get('GEOMET_MAPFILE_CONFIG', None)
URL = os.environ.get('GEOMET_MAPFILE_URL', None)
STORE_TYPE = os.environ.get('GEOMET_MAPFILE_STORE_TYPE', None)
STORE_URL = os.environ.get('GEOMET_MAPFILE_STORE_URL', None)
TILEINDEX_NAME = os.environ.get('GEOMET_MAPFILE_TILEINDEX_NAME', None)
TILEINDEX_TYPE = os.environ.get('GEOMET_MAPFILE_TILEINDEX_TYPE', None)
TILEINDEX_URL = os.environ.get('GEOMET_MAPFILE_TILEINDEX_URL', None)
MAPFILE_STORAGE = os.environ.get('GEOMET_MAPFILE_STORAGE', 'file')
ALLOW_LAYER_DATA_DOWNLOAD = str2bool(os.environ.get(
    'GEOMET_MAPFILE_ALLOW_LAYER_DATA_DOWNLOAD', False))


LOGGER.debug(BASEDIR)
LOGGER.debug(CONFIG)
LOGGER.debug(STORE_TYPE)
LOGGER.debug(STORE_URL)
LOGGER.debug(TILEINDEX_NAME)
LOGGER.debug(TILEINDEX_URL)
LOGGER.debug(MAPFILE_STORAGE)
LOGGER.debug(ALLOW_LAYER_DATA_DOWNLOAD)

if None in [BASEDIR, CONFIG]:
    msg = 'Environment variables not set!'
    LOGGER.exception(msg)
    raise EnvironmentError(msg)
