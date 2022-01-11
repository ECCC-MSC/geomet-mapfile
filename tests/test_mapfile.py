###############################################################################
#
# Copyright (C) 2021 Philippe Théroux
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
import datetime
import json
import os
import re
import unittest
from unittest.mock import ANY, call, mock_open, Mock, patch

import mappyfile
from yaml import load, CLoader

import geomet_mapfile.mapfile
from geomet_mapfile.mapfile import (
    mcf2layer_metadata,
    layer_time_config,
    gen_web_metadata,
    gen_layer,
    generate_mapfile,
    find_replace_wms_timedefault,
    update_mapfile,
    LayerTimeConfigError,
)


THISDIR = os.path.dirname(os.path.realpath(__file__))
PARENTDIR = os.path.dirname(THISDIR)
MCF_DIR = f'{THISDIR}/resources/mcf'
MAPFILE_BASE = f'{PARENTDIR}/geomet_mapfile/resources/mapfile-base.json'
SYMBOLS_FILE = f'{PARENTDIR}/geomet_mapfile/resources/mapserv/symbols.json'
URL = 'https://api.weather.gc.ca/geomet'
TEST_MAPFILE = f'{THISDIR}/resources/mapfile/geomet-GDPS.ETA_TT.map'


class Store:
    """
    To avoid using a redis store for the unit tests
    This way we mimic the store function and simply use the yamls.
    The `get_key` try/except is there to replicate redis-py's get command
    which returns None if a key does not exist.
    """

    def __init__(self):
        self.calls = []
        self.data = {
            'geomet-data-registry_GDPS.ETA_TT_time_extent': '2020-01-14T00:00:00Z/2020-01-24T00:00:00Z/PT3H',  # noqa
            'geomet-data-registry_GDPS.ETA_TT_default_time': '2020-01-14T00:00:00Z',  # noqa
            'geomet-data-registry_GDPS.ETA_TT_model_run_extent': '2020-01-12T00:00:00Z/2020-01-14T00:00:00Z/PT12H',  # noqa
            'geomet-data-registry_GDPS.ETA_TT_default_model_run': '2020-01-14T00:00:00Z',  # noqa
            'geomet-data-registry_GDPS.ETA_UU_time_extent': '2020-01-14T00:00:00Z/2020-01-24T00:00:00Z/PT3H',  # noqa
            'geomet-data-registry_GDPS.ETA_UU_default_time': '2020-01-14T00:00:00Z',  # noqa
            'geomet-data-registry_GDPS.ETA_UU_model_run_extent': '2020-01-12T00:00:00Z/2020-01-14T00:00:00Z/PT12H',  # noqa
            'geomet-data-registry_GDPS.ETA_UU_default_model_run': '2020-01-14T00:00:00Z',  # noqa
            'geomet-data-registry_GDPS.ETA_GZ_time_extent': '2021-12-13T00:00:00Z/2021-12-13T00:00:00Z/PT0H',  # noqa
            'geomet-data-registry_GDPS.ETA_GZ_model_run_extent': '2021-12-11T00:00:00Z/2021-12-13T00:00:00Z/PT12H',  # noqa
            'geomet-data-registry_GDPS.ETA_GZ_default_model_run': '2021-12-13T00:00:00Z',  # noqa
            'geomet-data-registry_GDPS.ETA_GZ-CONTOUR_time_extent': '2021-12-13T00:00:00Z/2021-12-13T00:00:00Z/PT0H',  # noqa
            'geomet-data-registry_GDPS.ETA_GZ-CONTOUR_model_run_extent': '2021-12-11T00:00:00Z/2021-12-13T00:00:00Z/PT12H',  # noqa
            'geomet-data-registry_GDPS.ETA_GZ-CONTOUR_default_model_run': '2021-12-13T00:00:00Z',  # noqa
            'geomet-data-registry_RADAR_1KM_RRAI_time_extent': '2020-01-14T00:00:00Z/2020-01-24T00:00:00Z/PT3H',  # noqa
            'geomet-data-registry_RADAR_1KM_RRAI_default_time': '2020-01-14T00:00:00Z',  # noqa
            'geomet-mapfile_GDPS.ETA_TT_layer': 'GDPS_ETA_TT.map',
            'geomet-mapfile_GDPS.ETA_UU_layer': 'GDPS_ETA_UU.map',
            'geomet-mapfile_GDPS.ETA_GZ_layer': 'GDPS_ETA_GZ.map',
            'geomet-mapfile_GDPS.ETA_GZ-CONTOUR_layer': 'GDPS_ETA_GZ-CONTOUR.map',  # noqa
            'geomet-mapfile_RADAR_1KM_RRAI_layer': 'RADAR_1KM_RRAI.map',
        }

    def get_key(self, key, raw=False):
        try:
            if raw:
                return self.data[key]
            return self.data[f'geomet-mapfile_{key}']
        except KeyError:
            return None

    def list_keys(self, pattern):
        re_pattern = re.compile(pattern.replace('*', '.*'))
        return [key for key in self.data if re_pattern.match(key)]

    def set_key(self, name, mapfile, raw=False):
        self.calls.append((name, mapfile, raw))


class GeoMetMapfileTest(unittest.TestCase):
    """Test suite for geomet-mapfile package"""

    @classmethod
    def setUpClass(cls):
        """Code that executes only once before the entire test suite"""
        cls.yml_file = os.path.join(
            THISDIR, 'resources/geomet-weather-test.yml'
        )
        with open(cls.yml_file) as f:
            cls.cfg = load(f, Loader=CLoader)

        expected_config = os.path.join(
            THISDIR, 'resources/expected-values.yml'
        )
        with open(expected_config) as f:
            cls.expected_values = load(f, Loader=CLoader)

        cls.maxDiff = None

    def test_mcf2layer_metadata_gdps_eta_uu(self):
        """
        Test that the GDPS.ETA_UU LAYER.METADATA dictionary returned by the
        geomet_mapfile.mapfile.mcf2layer_metadata() function returns the
        expected value.
        """
        layer_path = os.path.join(
            MCF_DIR,
            GeoMetMapfileTest.cfg['layers']['GDPS.ETA_UU']['forecast_model']['mcf']  # noqa
        )
        self.assertDictEqual(
            mcf2layer_metadata(layer_path),
            GeoMetMapfileTest.expected_values['mcf2layer_metadata']['GDPS.ETA_UU']  # noqa
        )

    def test_mcf2layer_metadata_radar_1km_rrai(self):
        """
        Test that the RADAR_1KM_RRAI LAYER.METADATA dictionary returned by the
        geomet_mapfile.mapfile.mcf2layer_metadata() function returns the
        expected value.
        """
        layer_path = os.path.join(
            MCF_DIR,
            GeoMetMapfileTest.cfg['layers']['RADAR_1KM_RRAI']['forecast_model']['mcf']  # noqa
        )
        self.assertDictEqual(
            mcf2layer_metadata(layer_path),
            GeoMetMapfileTest.expected_values['mcf2layer_metadata']['RADAR_1KM_RRAI']  # noqa
        )

    @patch('geomet_mapfile.mapfile.load_plugin', return_value=Store())
    def test_layer_time_config_layertimeconfigerror(self, mock_load_plugin):
        """
        Test that a LayerTimeConfigError is raised when an invalid layer name
        is passed to the geomet_mapfile.mapfile.layer_time_config() function.
        """
        with self.assertLogs('geomet_mapfile.mapfile', level='ERROR') as err:
            with self.assertRaises(LayerTimeConfigError):
                layer_time_config('invalid_layer_name')
        self.assertEqual(len(err.records), 1)

    @patch('geomet_mapfile.mapfile.load_plugin', return_value=Store())
    def test_layer_time_config_gdps_eta_uu(self, mock_load_plugin):
        """
        Test that the dictionnary returned from
        geomet_mapfile.mapfile.layer_time_config() for GDPS.ETA_UU
        is equal to the expected value.
        """
        self.assertDictEqual(
            layer_time_config('GDPS.ETA_UU'),
            GeoMetMapfileTest.expected_values['layer_time_config']['GDPS.ETA_UU']  # noqa
        )

    @patch('geomet_mapfile.mapfile.load_plugin', return_value=Store())
    def test_layer_time_config_gdps_eta_gz(self, mock_load_plugin):
        """
        Test that the dictionnary returned from
        geomet_mapfile.mapfile.layer_time_config() for GDPS.ETA_GZ
        is equal to the expected value.
        """
        self.assertDictEqual(
            layer_time_config('GDPS.ETA_GZ'),
            GeoMetMapfileTest.expected_values['layer_time_config']['GDPS.ETA_GZ']  # noqa
        )

    @patch('geomet_mapfile.mapfile.load_plugin', return_value=Store())
    def test_layer_time_config_radar_1km_rrai(self, mock_load_plugin):
        """
        Test that the dictionnary returned from
        geomet_mapfile.mapfile.layer_time_config() for RADAR_1KM_RRAI
        is equal to the expected value.
        """
        self.assertDictEqual(
            layer_time_config('RADAR_1KM_RRAI'),
            GeoMetMapfileTest.expected_values['layer_time_config']['RADAR_1KM_RRAI']  # noqa
        )

    @patch('geomet_mapfile.mapfile.datetime')
    def test_gen_web_metadata(self, mock_date_now):
        """
        Test that the MAP.WEB.METADATA dictionnary returned by
        geomet_mapfile.mapfile.gen_web_metadata() is equal
        to the expected value.
        """
        mock_date_now.utcnow.return_value.strftime.return_value = (
            '2021-12-06T20:03:31Z'
        )
        with open(MAPFILE_BASE) as fh:
            mapfile = json.load(fh, object_pairs_hook=OrderedDict)
        self.assertDictEqual(
            gen_web_metadata(mapfile, GeoMetMapfileTest.cfg['metadata'], URL),
            GeoMetMapfileTest.expected_values['gen_web_metadata']
        )

    @patch('geomet_mapfile.mapfile.layer_time_config')
    @patch('geomet_mapfile.mapfile.mcf2layer_metadata')
    def test_gen_layer_gdps_eta_uu(self, mock_mcf2l_meta, mock_ltc):
        """
        Test that the GDPS.ETA_UU LAYER mapfile dictionnary returned by
        geomet_mapfile.mapfile.gen_layer() is equal to the expected value.
        """
        mock_ltc.return_value = GeoMetMapfileTest.expected_values['layer_time_config']['GDPS.ETA_UU']  # noqa
        mock_mcf2l_meta.return_value = GeoMetMapfileTest.expected_values['mcf2layer_metadata']['GDPS.ETA_UU']  # noqa
        layer_info = GeoMetMapfileTest.cfg['layers']['GDPS.ETA_UU']
        self.assertDictEqual(
            gen_layer('GDPS.ETA_UU', layer_info),
            GeoMetMapfileTest.expected_values['gen_layer']['GDPS.ETA_UU']
        )

    @patch('geomet_mapfile.mapfile.layer_time_config')
    @patch('geomet_mapfile.mapfile.mcf2layer_metadata')
    def test_gen_layer_radar_1km_rrai(self, mock_mcf2l_meta, mock_ltc):
        """
        Test that the RADAR_1KM_RRAI LAYER mapfile dictionnary returned by
        geomet_mapfile.mapfile.gen_layer() is equal to the expected value.
        """
        mock_ltc.return_value = GeoMetMapfileTest.expected_values['layer_time_config']['RADAR_1KM_RRAI']  # noqa
        mock_mcf2l_meta.return_value = GeoMetMapfileTest.expected_values['mcf2layer_metadata']['RADAR_1KM_RRAI']  # noqa
        layer_info = GeoMetMapfileTest.cfg['layers']['RADAR_1KM_RRAI']
        self.assertDictEqual(
            gen_layer('RADAR_1KM_RRAI', layer_info),
            GeoMetMapfileTest.expected_values['gen_layer']['RADAR_1KM_RRAI']
        )

    @patch('geomet_mapfile.mapfile.layer_time_config')
    @patch('geomet_mapfile.mapfile.mcf2layer_metadata')
    def test_gen_layer_gdps_eta_gz_contour(self, mock_mcf2l_meta, mock_ltc):
        """
        Test that the GDPS.ETA_GZ-CONTOUR mapfile dictionnary returned by
        geomet_mapfile.mapfile.gen_layer() is equal to the expected value.
        """
        mock_ltc.return_value = GeoMetMapfileTest.expected_values['layer_time_config']['GDPS.ETA_GZ-CONTOUR']  # noqa
        mock_mcf2l_meta.return_value = GeoMetMapfileTest.expected_values['mcf2layer_metadata']['GDPS.ETA_GZ-CONTOUR']  # noqa
        layer_info = GeoMetMapfileTest.cfg['layers']['GDPS.ETA_GZ-CONTOUR']
        self.assertDictEqual(
            gen_layer('GDPS.ETA_GZ-CONTOUR', layer_info),
            GeoMetMapfileTest.expected_values['gen_layer']['GDPS.ETA_GZ-CONTOUR']  # noqa
        )

    @patch('geomet_mapfile.mapfile.BASEDIR', '/geomet-mapfile')
    @patch('geomet_mapfile.mapfile.os.path.exists', Mock(return_value=False))
    @patch('geomet_mapfile.mapfile.mappyfile')
    @patch('geomet_mapfile.mapfile.gen_layer')
    @patch('geomet_mapfile.mapfile.os.makedirs')
    @patch('geomet_mapfile.mapfile.load_plugin', return_value=Store())
    def test_generate_mapfile_nolayer_store_use_includes(
        self,
        mock_load_plugin,
        mock_makedirs,
        mock_gen_layer,
        mock_mappyfile,
    ):
        """
        Test that the creation of a global mapfile
        and all individual mapfiles are created on disk and in
        the store when no specific layer name is given to the
        geomet_mapfile.mapfile.generate_mapfile() and that it
        uses Mapfile INCLUDE directives.
        """
        with open(MAPFILE_BASE) as fh:
            mapfile = json.load(fh, object_pairs_hook=OrderedDict)
        with open(SYMBOLS_FILE) as fh2:
            symbols = json.load(fh2)

        # mock opening base mapfile/symbols json files and the GeoMet
        # yaml config and call geomet_mapfile with store as output
        # and using include directives.
        with patch('builtins.open', new_callable=mock_open):
            with patch('json.load') as mock_json_load:
                with patch('geomet_mapfile.mapfile.load') as mock_yaml_load:
                    mock_json_load.side_effect = [mapfile, symbols]
                    mock_yaml_load.return_value = GeoMetMapfileTest.cfg
                    self.assertTrue(
                        generate_mapfile(output='store', use_includes=True)
                    )

        # assert that the output directory was created
        mock_makedirs.assert_called_once_with(
            f'/geomet-mapfile{os.sep}mapfile'
        )

        # assert that that the mapfile was written to disk via
        # 6 mappyfile.dump() calls (5 layers + 1 global mapfile) and
        # 11 mappyfile.dumps() calls, populating the store with a _mapfile.map
        # and _layer.map for each layer in config and a global mapfile with
        # include directives.
        self.assertListEqual(
            [mock_mappyfile.dump.call_count, mock_mappyfile.dumps.call_count],
            [6, 11]
        )

        # assert that the mappyfile.dump() was called with the mapfile
        # dictionnary
        mock_mappyfile.dump.assert_called_with(mapfile, ANY)

        # assert that mappyfile.dumps() was called and that the
        # store's set_key() method was called with the expected values
        # when generating the global mapfile in the store.
        mock_mappyfile.dumps.assert_called_with(mapfile)
        mock_store = mock_load_plugin.return_value
        calls = mock_store.calls[-1]
        expected_calls = (
            'geomet-weather_mapfile',
            mock_mappyfile.dumps.return_value,
            False
        )
        self.assertTupleEqual(calls, expected_calls)

    @patch('geomet_mapfile.mapfile.BASEDIR', '/geomet-mapfile')
    @patch('geomet_mapfile.mapfile.THISDIR', '/geomet-mapfile/tests')
    @patch('geomet_mapfile.mapfile.os.path.exists', Mock(return_value=False))
    @patch('geomet_mapfile.mapfile.mappyfile')
    @patch('geomet_mapfile.mapfile.gen_layer')
    @patch('geomet_mapfile.mapfile.gen_web_metadata')
    @patch('geomet_mapfile.mapfile.os.makedirs')
    @patch('geomet_mapfile.mapfile.load_plugin', return_value=Store())
    def test_generate_mapfile_layer_store(
        self,
        mock_load_plugin,
        mock_makedirs,
        mock_gen_web_metadata,
        mock_gen_layer,
        mock_mappyfile,
    ):
        """
        Test that when passing a layer name to
        geomet_mapfile.mapfile.gen_layer() (GDPS.ETA_TT) generates a mapfile
        on disk and that both the GDPS.ETA_TT_layer and GDPS.ETA_TT_mapfile
        keys are created in the store when output is set to store.
        """
        with open(MAPFILE_BASE) as fh:
            mapfile = json.load(fh, object_pairs_hook=OrderedDict)
        with open(SYMBOLS_FILE) as fh2:
            symbols = json.load(fh2)
        mock_gen_web_metadata.return_value = GeoMetMapfileTest.expected_values['gen_web_metadata']  # noqa
        mock_gen_layer.return_value = GeoMetMapfileTest.expected_values['gen_layer']['GDPS.ETA_TT']  # noqa
        with patch('builtins.open', new_callable=mock_open):
            with patch('json.load') as mock_json_load:
                with patch('geomet_mapfile.mapfile.load') as mock_yaml_load:
                    mock_json_load.side_effect = [mapfile, symbols]
                    mock_yaml_load.return_value = GeoMetMapfileTest.cfg
                    self.assertTrue(
                        generate_mapfile('GDPS.ETA_TT', output='store')
                    )

        # assert that the output directory was created
        mock_makedirs.assert_called_once_with(
            f'/geomet-mapfile{os.sep}mapfile'
        )

        # assert that that the GDPS.ETA_TT layer mapfile was written to disk
        # via 1 mappyfile.dump() call and 2 mappyfile.dumps() calls,
        # populating the store with a GDPS.ETA_TT_mapfile.map
        # and GDPS.ETA_TT_layer.map.
        self.assertListEqual(
            [mock_mappyfile.dump.call_count, mock_mappyfile.dumps.call_count],
            [1, 2]
        )

        # assert that the store's set_key() method was called twice to
        # set both the GDPS.ETA_TT_layer and GDPS.ETA_TT_mapfile keys in the
        # store.
        mock_store = mock_load_plugin.return_value

        expected_calls = [
            ('GDPS.ETA_TT_mapfile', mock_mappyfile.dumps.return_value, False),
            ('GDPS.ETA_TT_layer', mock_mappyfile.dumps.return_value, False)
        ]
        self.assertListEqual(mock_store.calls, expected_calls)

        # simulate mapfile configuration
        mapfile['symbols'] = []
        mapfile['web']['metadata'] = GeoMetMapfileTest.expected_values[
            'gen_web_metadata'
        ]  # noqa
        mapfile['config']['proj_lib'] = '/geomet-mapfile/tests/resources/mapserv'  # noqa
        mapfile['layers'] = [mock_gen_layer.return_value]
        mapfile['outputformats'] = [
            format_
            for format_ in mapfile['outputformats']
            if format_['name'] in ['GEOTIFF_16', 'AAIGRID']
        ]

        # assert that the calls to mappyfile.dumps() are made
        # with the expected arguments and the arguments' content are
        # identical.
        expected_calls = [call(mapfile), call(mapfile['layers'])]
        mock_mappyfile.dumps.assert_has_calls(expected_calls)

        # assert that mappyfily.dump() was called
        # with the expected GDPS.ETA_TT LAYER directive.
        mock_mappyfile.dump.assert_called_with(mapfile['layers'], ANY)

    @patch('geomet_mapfile.mapfile.BASEDIR', '/geomet-mapfile')
    @patch('geomet_mapfile.mapfile.os.path.exists', Mock(return_value=False))
    @patch('geomet_mapfile.mapfile.mappyfile')
    @patch('geomet_mapfile.mapfile.gen_layer')
    @patch('geomet_mapfile.mapfile.gen_web_metadata')
    @patch('geomet_mapfile.mapfile.os.makedirs')
    @patch('geomet_mapfile.mapfile.load_plugin', return_value=Store())
    def test_generate_mapfile_layer_file_with_includes(
        self,
        mock_load_plugin,
        mock_makedirs,
        mock_gen_web_metadata,
        mock_gen_layer,
        mock_mappyfile,
    ):
        """
        Test that when passing a layer name to
        geomet_mapfile.mapfile.gen_layer() (GDPS.ETA_UU) it generates a
        complete mapfile using INCLUDE directive (GDPS.ETA_UU_mapfile.map)
        and a layer mapfile (GDPS.ETA_TT_layer.map) and uses mappyfile.dump()
        to write these to disk.
        """
        with open(MAPFILE_BASE) as fh:
            mapfile = json.load(fh, object_pairs_hook=OrderedDict)
        with open(SYMBOLS_FILE) as fh2:
            symbols = json.load(fh2)
        mock_gen_web_metadata.return_value = GeoMetMapfileTest.expected_values['gen_web_metadata']  # noqa
        mock_gen_layer.return_value = GeoMetMapfileTest.expected_values['gen_layer']['GDPS.ETA_UU']  # noqa
        with patch('builtins.open', new_callable=mock_open):
            with patch('json.load') as mock_json_load:
                with patch('geomet_mapfile.mapfile.load') as mock_yaml_load:
                    mock_json_load.side_effect = [mapfile, symbols]
                    mock_yaml_load.return_value = GeoMetMapfileTest.cfg
                    self.assertTrue(
                        generate_mapfile('GDPS.ETA_UU', output='file')
                    )

        # assert that the output directory was created
        mock_makedirs.assert_called_once_with(
            f'/geomet-mapfile{os.sep}mapfile'
        )

        # assert that 2 calls were made with mappyfile.dump () to
        # ensure that both GDPS.ETA_UU_mapfile.map and GDPS.ETA_UU_layer.map
        # would have been writen to disk.
        self.assertEqual(mock_mappyfile.dump.call_count, 2)

        # assert that mappyfile.dumps() was not called ensuring
        # no mapfile strings were dumped to store.
        mock_mappyfile.dumps.assert_not_called()

        # simulate mapfile configuration and ensure it uses includes
        mapfile['symbols'] = [
            symbol
            for symbol in mapfile['symbols']
            if symbol['name'] in ['circle_wind', 'arrow_wind']
        ]
        mapfile['include'] = [
            '/geomet-mapfile/mapfile/geomet-weather-GDPS.ETA_UU_layer.map'
        ]
        mapfile['web']['metadata'] = GeoMetMapfileTest.expected_values['gen_web_metadata']  # noqa
        mapfile['config']['proj_lib'] = '/geomet-mapfile/tests/resources/mapserv'  # noqa
        mapfile['layers'] = [mock_gen_layer.return_value]
        mapfile['outputformats'] = [
            format_
            for format_ in mapfile['outputformats']
            if format_['name'] in ['GEOTIFF_16', 'AAIGRID']
        ]

        # assert that the calls to mappyfile.dump() are made
        # with the expected arguments and the arguments' content are
        # identical.
        expected_calls = [call(mapfile['layers'], ANY), call(mapfile, ANY)]
        mock_mappyfile.dump.assert_has_calls(expected_calls)

    @patch('geomet_mapfile.mapfile.BASEDIR', '/geomet-mapfile')
    @patch('geomet_mapfile.mapfile.THISDIR', '/geomet-mapfile/tests')
    @patch('geomet_mapfile.mapfile.os.path.exists', Mock(return_value=False))
    @patch('geomet_mapfile.mapfile.mappyfile')
    @patch('geomet_mapfile.mapfile.gen_layer')
    @patch('geomet_mapfile.mapfile.gen_web_metadata')
    @patch('geomet_mapfile.mapfile.os.makedirs')
    def test_generate_mapfile_layer_file_no_includes(
        self,
        mock_makedirs,
        mock_gen_web_metadata,
        mock_gen_layer,
        mock_mappyfile,
    ):
        """
        Test that when passing a layer name to
        geomet_mapfile.mapfile.gen_layer() (GDPS.ETA_UU) it generates a
        complete mapfile without INCLUDE directive (GDPS.ETA_UU_mapfile.map)
        and a layer mapfile (GDPS.ETA_TT_layer.map) and uses mappyfile.dump()
        to write these to disk.
        """
        with open(MAPFILE_BASE) as fh:
            mapfile = json.load(fh, object_pairs_hook=OrderedDict)
        with open(SYMBOLS_FILE) as fh2:
            symbols = json.load(fh2)
        mock_gen_web_metadata.return_value = GeoMetMapfileTest.expected_values['gen_web_metadata']  # noqa
        mock_gen_layer.return_value = GeoMetMapfileTest.expected_values['gen_layer']['GDPS.ETA_TT']  # noqa
        with patch('builtins.open', new_callable=mock_open):
            with patch('json.load') as mock_json_load:
                with patch('geomet_mapfile.mapfile.load') as mock_yaml_load:
                    mock_json_load.side_effect = [mapfile, symbols]
                    mock_yaml_load.return_value = GeoMetMapfileTest.cfg
                    self.assertTrue(
                        generate_mapfile(
                            'GDPS.ETA_TT', output='file', use_includes=False
                        )
                    )

        # assert that the output directory was created
        mock_makedirs.assert_called_once_with(
            f'/geomet-mapfile{os.sep}mapfile'
        )

        # assert that 2 calls were made with mappyfile.dump () to
        # ensure that both GDPS.ETA_TT_mapfile.map and GDPS.ETA_TT_layer.map
        # would have been writen to disk.
        self.assertEqual(mock_mappyfile.dump.call_count, 2)

        # assert that mappyfile.dumps() was not called ensuring
        # no mapfile strings were dumped to store.
        mock_mappyfile.dumps.assert_not_called()

        # simulate mapfile configuration
        mapfile['symbols'] = []
        mapfile['web']['metadata'] = GeoMetMapfileTest.expected_values['gen_web_metadata']  # noqa
        mapfile['config']['proj_lib'] = '/geomet-mapfile/tests/resources/mapserv'  # noqa
        mapfile['layers'] = [mock_gen_layer.return_value]
        mapfile['outputformats'] = [
            format_
            for format_ in mapfile['outputformats']
            if format_['name'] in ['GEOTIFF_16', 'AAIGRID']
        ]

        # assert that the calls to mappyfile.dump() are made
        # with the expected arguments and the arguments' content are
        # identical.
        expected_calls = [call(mapfile['layers'], ANY), call(mapfile, ANY)]
        mock_mappyfile.dump.assert_has_calls(expected_calls)

    @patch('geomet_mapfile.mapfile.BASEDIR', '/geomet-mapfile')
    @patch('geomet_mapfile.mapfile.os.path.exists', Mock(return_value=False))
    @patch('geomet_mapfile.mapfile.mappyfile')
    @patch('geomet_mapfile.mapfile.gen_layer')
    @patch('geomet_mapfile.mapfile.gen_web_metadata')
    @patch('geomet_mapfile.mapfile.os.makedirs')
    def test_generate_mapfile_layertimeconfigerror(
        self,
        mock_makedirs,
        mock_gen_web_metadata,
        mock_gen_layer,
        mock_mappyfile,
    ):
        """
        Test that when passing a layer name (for example GDPS.ETA_TT) to
        geomet_mapfile.mapfile.gen_layer() for which insuffient temporal
        metadata is available (no time extent available), mappyfile.dump()
        is called with an empty list as an argument, which would generate an
        empty GPDS.ETA_TT_layer.map file.
        """
        with open(MAPFILE_BASE) as fh:
            mapfile = json.load(fh, object_pairs_hook=OrderedDict)
        with open(SYMBOLS_FILE) as fh2:
            symbols = json.load(fh2)
        mock_gen_web_metadata.return_value = GeoMetMapfileTest.expected_values['gen_web_metadata']  # noqa

        # ensure that a LayerTimeConfigError is thrown when
        # geomet_mapfile.mapfile.gen_layer() is called
        mock_gen_layer.side_effect = LayerTimeConfigError

        with patch('builtins.open', new_callable=mock_open):
            with patch('json.load') as mock_json_load:
                with patch('geomet_mapfile.mapfile.load') as mock_yaml_load:
                    mock_json_load.side_effect = [mapfile, symbols]
                    mock_yaml_load.return_value = GeoMetMapfileTest.cfg
                    self.assertFalse(
                        generate_mapfile(
                            'GDPS.ETA_TT', output='file', use_includes=False
                        )
                    )

        # assert that the output directory was created
        mock_makedirs.assert_called_once_with(
            f'/geomet-mapfile{os.sep}mapfile'
        )

        # assert that mappyfile.dump was only called once to write the empty
        # layer mapfile
        self.assertEqual(mock_mappyfile.dump.call_count, 1)

        # assert that the function call was made with an
        # empty list as the first argument
        mock_mappyfile.dump.assert_called_with([], ANY)

    @patch.object(geomet_mapfile.mapfile, 'datetime', Mock(wraps=datetime.datetime))  # noqa
    def test_find_replace_wms_timedefault(self):
        """
        Test that the geomet_mapfile.mapfile.find_replace_wms_timedefault()
        function properly updates a mapfile's LAYER.METADATA.wms_timedefault
        value.
        """
        # force datetime.utcnow() call to return given value
        geomet_mapfile.mapfile.datetime.utcnow.return_value = (
            datetime.datetime(2020, 1, 15, 13, 31, 31)
        )

        # initial mapfile to string
        mapfile = GeoMetMapfileTest.expected_values['gen_layer']['GDPS.ETA_TT']  # noqa
        mapfile_str = mappyfile.dumps(mapfile)

        # change mapfile wms_timedefault to expected value returned by
        # geomet_mapfile.mapfile.find_replace_wms_timedefault() function
        # if datetime.utcnow() equal to 2020-01-15T13:31:31
        mapfile['metadata']['wms_timedefault'] = '2020-01-15T15:00:00Z'
        expected_mapfile = mappyfile.dumps(mapfile)

        # assert the returned mapfile string is identical to the expected
        # from findmapfile.
        self.assertEqual(
            find_replace_wms_timedefault('GDPS.ETA_TT', mapfile_str),
            expected_mapfile
        )

    def test_find_replace_wms_timedefault_not_updating(self):
        """
        Test that logging.debug() is called when
        LAYER.METADATA.wms_available_intervals is not found in a
        layer mapfile when updating wms_timedefault value.
        """
        with open(TEST_MAPFILE, 'r+') as fp:
            with self.assertLogs(
                'geomet_mapfile.mapfile', level='DEBUG'
            ) as debug:
                mapfile_ = fp.read()
                self.assertEqual(
                    find_replace_wms_timedefault('GDPS.ETA_TT', mapfile_),
                    mapfile_
                )
        self.assertEqual(len(debug.records), 1)

    @patch('geomet_mapfile.mapfile.BASEDIR', '/geomet-mapfile')
    @patch('geomet_mapfile.mapfile.MAPFILE_STORAGE', 'store')
    @patch('geomet_mapfile.mapfile.find_replace_wms_timedefault')
    @patch('geomet_mapfile.mapfile.load_plugin', return_value=Store())
    def test_update_mapfile_layer_given(
        self, mock_load_plugin, mock_wms_timedefault
    ):
        """
        Test that the geomet_mapfile.mapfile.update mapfile() function
        accesses only a specific mapfile when given a layer name, and writes
        to disk and store the updated mapfile.
        """
        # update following layers
        names = ['GDPS.ETA_TT', 'GDPS.ETA_UU', 'RADAR_1KM_RRAI']
        # load the expected mapfile
        for layer_name in names:
            expected = GeoMetMapfileTest.expected_values['gen_layer'][layer_name]  # noqa

            # mock the output of the find_replace_wms_timedefault() function
            mock_wms_timedefault.return_value = mappyfile.dumps(expected)

            # assert that the correct path of mapfile would have been accessed
            # given BASEDIR value
            with patch('builtins.open', mock_open()) as mapfile_open:
                update_mapfile(layer_name)
            mapfile_open.assert_called_once_with(
                f'/geomet-mapfile{os.sep}mapfile{os.sep}geomet-weather-{layer_name}_layer.map',  # noqa
                'r+',
            )

            # assert that the written mapfile matches the mocked
            # return value of find_replace_wms_timedefault()
            mapfile_open.return_value.write.assert_called_once_with(
                mock_wms_timedefault.return_value
            )

        # assert that mapfile keys in store would have been updated with the
        # appropriate values
        mock_store = mock_load_plugin.return_value
        expected_calls = [
            (
                'geomet-mapfile_GDPS.ETA_TT_layer',
                mappyfile.dumps(GeoMetMapfileTest.expected_values['gen_layer']['GDPS.ETA_TT']),  # noqa
                True
            ),
            (
                'geomet-mapfile_GDPS.ETA_UU_layer',
                mappyfile.dumps(GeoMetMapfileTest.expected_values['gen_layer']['GDPS.ETA_UU']),  # noqa
                True
            ),
            (
                'geomet-mapfile_RADAR_1KM_RRAI_layer',
                mappyfile.dumps(GeoMetMapfileTest.expected_values['gen_layer']['RADAR_1KM_RRAI']),  # noqa
                True
            ),
        ]
        self.assertListEqual(mock_store.calls, expected_calls)

    @patch('geomet_mapfile.mapfile.BASEDIR', '/geomet-mapfile')
    @patch('geomet_mapfile.mapfile.MAPFILE_STORAGE', 'store')
    @patch('geomet_mapfile.mapfile.find_replace_wms_timedefault')
    @patch('geomet_mapfile.mapfile.load_plugin', return_value=Store())
    def test_update_mapfile_layer_none(
        self, mock_load_plugin, mock_wms_timedefault
    ):
        """
        Test that the geomet_mapfile.mapfile.update mapfile() function
        accesses all mapfiles when no layer name is passed, and writes
        to disk and store the updated mapfiles.
        """

        # simulate getting all layers from config and
        # returning mapfile strings from find_replace_wms_timedefault()
        # as a list of side effects.
        layers = [layer for layer in GeoMetMapfileTest.cfg['layers']]
        mapfiles_str = []
        for layer in layers:
            expected = GeoMetMapfileTest.expected_values['gen_layer'][layer]
            mapfiles_str.append(mappyfile.dumps(expected))
        mock_wms_timedefault.side_effect = mapfiles_str

        # assert that when no layer name is given all mapfiles are retrieved
        # from BASEDIR/mapfile/. In this case, no mapfiles are returned
        # meaning the function should return True without having to parse
        # any mapfiles.
        with patch('geomet_mapfile.mapfile.glob') as mock_glob:
            mock_glob.return_value = []
            self.assertTrue(update_mapfile())

        # assert that mapfile keys in store would have been updated with the
        # appropriate values for all layers in sample config.
        mock_store = mock_load_plugin.return_value
        expected_calls = [
            (
                'geomet-mapfile_GDPS.ETA_TT_layer',
                mappyfile.dumps(GeoMetMapfileTest.expected_values['gen_layer']['GDPS.ETA_TT']),  # noqa
                True
            ),
            (
                'geomet-mapfile_GDPS.ETA_UU_layer',
                mappyfile.dumps( GeoMetMapfileTest.expected_values['gen_layer'][ 'GDPS.ETA_UU' ] ),  # noqa
                True
            ),
            (
                'geomet-mapfile_GDPS.ETA_GZ_layer',
                mappyfile.dumps( GeoMetMapfileTest.expected_values['gen_layer'][ 'GDPS.ETA_GZ' ] ),  # noqa
                True
            ),
            (
                'geomet-mapfile_GDPS.ETA_GZ-CONTOUR_layer',
                mappyfile.dumps( GeoMetMapfileTest.expected_values['gen_layer'][ 'GDPS.ETA_GZ-CONTOUR' ] ),  # noqa
                True
            ),
            (
                'geomet-mapfile_RADAR_1KM_RRAI_layer',
                mappyfile.dumps( GeoMetMapfileTest.expected_values['gen_layer'][ 'RADAR_1KM_RRAI' ] ),  # noqa
                True
            )
        ]
        self.assertListEqual(mock_store.calls, expected_calls)

    @patch('geomet_mapfile.mapfile.BASEDIR', '/geomet-mapfile')
    @patch('geomet_mapfile.mapfile.MAPFILE_STORAGE', 'not store')
    def test_update_mapfile_filenotfounderror(self):
        """
        Test that logging.error() is called when a layer's
        associated mapfile is not found on disk when trying
        to update a mapfile's LAYER.METADATA wms_timedefault value.
        """

        # assert logger.error() was called when invalid path given
        with patch('geomet_mapfile.mapfile.glob') as mock_glob:
            with self.assertLogs(
                'geomet_mapfile.mapfile', level='ERROR'
            ) as err:
                mock_glob.return_value = ['not/a/valid/path/']
                update_mapfile()
        self.assertEqual(len(err.records), 1)


if __name__ == '__main__':
    unittest.main()
