###############################################################################
#
# Copyright (C) 2020 Etienne Pelletier
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

from celery import Celery
from geomet_mapfile.env import (
    CELERY_BROKER_URL,
    MAPFILE_STORAGE,
)
from geomet_mapfile.mapfile import generate_mapfile

LOGGER = logging.getLogger(__name__)

if CELERY_BROKER_URL is not None:
    app = Celery(
        'geomet-mapfile', backend=CELERY_BROKER_URL, broker=CELERY_BROKER_URL
    )

    @app.task(name='refresh_mapfile')
    def refresh_mapfile(layer_name, output=MAPFILE_STORAGE):
        result = generate_mapfile(layer_name, output)
        if isinstance(result, Exception):
            raise result
        return True

else:
    LOGGER.debug(
        'Celery broker URL is not defined. '
        'GEOMET_CELERY_BROKER_URL environment variable not found.'
    )
