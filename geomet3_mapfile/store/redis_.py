import logging

import redis

from geomet3_mapfile import __version__
from geomet3_mapfile.store.base import BaseStore, StoreError

LOGGER = logging.getLogger(__name__)


class RedisStore(BaseStore):
    """Redis key-value store implementation"""

    def __init__(self, provider_def):
        """
        Initialize object
        :param provider_def: provider definition dict
        :returns: `geomet_data_registry.store.redis_.RedisStore`
        """

        BaseStore.__init__(self, provider_def)

        try:
            self.redis = redis.Redis.from_url(self.url)
        except redis.exceptions.ConnectionError as err:
            msg = 'Cannot connect to Redis {}: {}'.format(self.url, err)
            LOGGER.exception(msg)
            raise StoreError(msg)

    def setup(self):
        """
        Create the store
        :returns: `bool` of process status
        """

        return self.redis.set('geomet3-mapfile-version', __version__)

    def teardown(self):
        """
        Delete the store
        :returns: `bool` of process status
        """

        return self.redis.delete('geomet3-mapfile-version')

    def get_key(self, key):
        """
        Get key from store
        :param key: key to fetch
        :returns: string of key value from Redis store
        """

        return self.redis.get(key)

    def set_key(self, key, value):
        """
        Set key value from
        :param key: key to set value
        :param value: value to set
        :returns: `bool` of set success
        """

        return self.redis.set(key, value)

    def __repr__(self):
        return '<BaseStore> {}'.format(self.type)

