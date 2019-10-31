import logging

LOGGER = logging.getLogger(__name__)


class BaseStore(object):
    """generic key-value store ABC"""

    def __init__(self, provider_def):
        """
        Initialize object
        :param provider_def: provider definition dict
        :returns: `geomet_data_registry.store.base.BaseStore`
        """

        self.type = provider_def['type']
        self.url = provider_def['url']

    def setup(self):
        """
        Create the store
        :returns: `bool` of process status
        """

        raise NotImplementedError()

    def teardown(self):
        """
        Delete the store
        :returns: `bool` of process status
        """

        raise NotImplementedError()

    def get_key(self, key):
        """
        Get key from store
        :param key: key to fetch
        :returns: string of key value from Redis store
        """

        raise NotImplementedError()

    def set_key(self, key, value):
        """
        Set key value from
        :param key: key to set value
        :param value: value to set
        :returns: `bool` of set success
        """

        raise NotImplementedError()

    def __repr__(self):
        return '<BaseStore> {}'.format(self.type)


class StoreError(Exception):
    """setup error"""
    pass
