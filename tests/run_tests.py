###############################################################################
#
# Copyright (C) 2018 Etienne Pelletier
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

from collections import OrderedDict
import json
from unittest.mock import patch
import os
import unittest

from yaml import load, CLoader

from geomet3_mapfile.mapfile import gen_web_metadata, gen_layer
from geomet3_mapfile.plugin import load_plugin
from geomet3_mapfile.store.redis_ import RedisStore

THISDIR = os.path.dirname(os.path.realpath(__file__))


def msg(test_id, test_description):
    """convenience function to print out test id and desc"""
    return '{}: {}'.format(test_id, test_description)


class Store:
    """
    To avoid using a redis store for the unit tests
    This way we mimic the store function and simply use the yamls.
    The `get_key` try/except is there to replicate redis-py's get command
    which returns None if a key does not exist.
    """

    def __init__(self):
        self.data = {
            'GDPS.ETA_TT_time_extent': '2020-01-14T00:00:00Z/2020-01-24T00:00:00Z/PT3H',
            'GDPS.ETA_TT_model_run_extent': '2020-01-12T00:00:00Z/2020-01-14T00:00:00Z/PT12H',
            'GDPS.ETA_TT_default_model_run': '2020-01-14T00:00:00Z'
        }

    def get_key(self, key):
        try:
            return self.data[key]
        except KeyError:
            return None


class GeoMet3MapfileTest(unittest.TestCase):
    """Test suite for geomet3-mapfile package"""

    yml_file = os.path.join(THISDIR, 'geomet-weather-test.yml')

    with open(yml_file) as f:
        cfg = load(f, Loader=CLoader)

    def setUp(self):
        """setup test fixtures, etc."""
        print(msg(self.id(), self.shortDescription()))

    def test_load_plugin(self):
        """test plugin loading"""
        provider_def = {
            'type': 'Redis',
            'url': 'redis://localhost:9200',
        }

        result = load_plugin('store', provider_def)

        self.assertIsInstance(result, RedisStore)

    def test_gen_web_metadata(self):
        """test mapfile MAP.WEB.METADATA section creation"""
        url = "https://fake.url/geomet-weather"
        mapfile = os.path.join(THISDIR, '../geomet3_mapfile/resources/mapfile-base.json')
        with open(mapfile) as f:
            m = json.load(f, object_pairs_hook=OrderedDict)
        c = self.cfg['metadata']

        result = gen_web_metadata(m, c, url)

        self.assertTrue(result['ows_extent'] == '-180,-90,180,90')
        self.assertTrue(result['ows_stateorprovince'] == 'New Brunswick')
        self.assertTrue(result['ows_stateorprovince_fr'] == 'Nouveau-Brunswick')
        self.assertTrue(result['ows_country'] == 'Canada')
        self.assertTrue(result['ows_country_fr'] == 'Canada')
        self.assertTrue(result['ows_contactinstructions'] == 'During hours of service')
        self.assertTrue(result['ows_contactinstructions_fr'] == 'Durant les heures de service')

    @patch('geomet3_mapfile.mapfile.load_plugin', return_value=Store())
    def test_gen_layer(self, mock_load_plugin):
        """returns a list of mappfile layer objects of given layer"""

        layer_name = "GDPS.ETA_TT"
        layer_info = self.cfg['layers'][layer_name]
        ows_title = 'GDPS.ETA - Air temperature [°C]'
        ows_title_fr = 'GDPS.ETA - Température de l\'air [°C]'
        wms_layer_group = '/Global Deterministic Prediction System (GDPS)/GDPS (15 km)'
        wms_layer_group_fr = '/Système Global de Prévision Déterministe (SGPD)/SGPD (15 km)'

        result = gen_layer(layer_name, layer_info)

        self.assertTrue(result[0]['projection'] ==
                        ['proj=longlat', 'R=6371229', 'no_defs'])
        self.assertTrue(result[0]['name'] == layer_name)
        self.assertTrue(result[0]['data'] == [''])
        self.assertTrue(result[0]['metadata']['ows_title'] == ows_title)
        self.assertTrue(result[0]['metadata']['ows_title_fr'] == ows_title_fr)
        self.assertTrue(result[0]['metadata']['wms_layer_group'] == wms_layer_group)
        self.assertTrue(result[0]['metadata']['wms_layer_group_fr'] == wms_layer_group_fr)


if __name__ == '__main__':
    unittest.main()
