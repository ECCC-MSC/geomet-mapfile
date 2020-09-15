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

from geomet_mapfile import __version__
from geomet_data_registry.store.redis_ import RedisStore as RedisStore_

LOGGER = logging.getLogger(__name__)


class RedisStore(RedisStore_):
    """Redis key-value store implementation"""

    def setup(self):
        """
        Create the store

        :returns: `bool` of process status
        """

        return self.redis.set('geomet-mapfile-version', __version__)

    def teardown(self):
        """
        Delete the store

        :returns: `bool` of process status
        """

        LOGGER.debug('Deleting all geomet-mapfile Redis keys')
        keys = [
            key
            for key in self.redis.scan_iter()
            if key.startswith('geomet-mapfile')
        ]
        for key in keys:
            LOGGER.debug('Deleting key {}'.format(key))
            self.redis.delete(key)

        return True

    def get_key(self, key, raw=False):
        """
        Get key value from Redis store

        :param key: key to set value
        :param value: value to set

        :returns: `bool` of set success
        """

        if raw:
            return self.redis.get(key)

        return self.redis.get('geomet-mapfile_{}'.format(key))

    def set_key(self, key, value, raw=False):
        """
        Set key value from Redis store

        :param key: key to set value
        :param value: value to set

        :returns: `bool` of set success
        """

        if raw:
            return self.redis.set(key, value)

        return self.redis.set('geomet-mapfile_{}'.format(key), value)
