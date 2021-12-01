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

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from glob import glob
import json
import logging
import os
import re
from urllib.parse import urlencode

import click
import mappyfile
from yaml import load, CLoader

from geomet_mapfile import __version__
from geomet_mapfile.env import (BASEDIR, CONFIG, STORE_TYPE,
                                STORE_URL, URL, MAPFILE_STORAGE)
from geomet_mapfile.plugin import load_plugin
from geomet_mapfile.util import DATEFORMAT, get_nearest


LOGGER = logging.getLogger(__name__)

THISDIR = os.path.dirname(os.path.realpath(__file__))

MAPFILE_BASE = os.path.join(THISDIR, 'resources', 'mapfile-base.json')

NOW = datetime.utcnow()

PROVIDER_DEF = {
    'type': STORE_TYPE,
    'url': STORE_URL
}


def mcf2layer_metadata(mcf_file):
    """
    Helper function to create partial LAYER.METADATA object

    :param mcf_file: path to MCF file on disk

    :returns: `dict` of LAYER.METADATA object
    """

    dict_ = {}
    keywords_en = []
    keywords_fr = []
    metadata_identifier = None

    with open(mcf_file) as f:
        mcf = load(f, Loader=CLoader)

        dict_['ows_abstract'] = mcf['identification']['abstract']['en']
        dict_['ows_abstract_fr'] = mcf['identification']['abstract']['fr']

        keywords_en = \
            mcf['identification']['keywords']['default']['keywords']['en']
        keywords_fr = \
            mcf['identification']['keywords']['default']['keywords']['fr']

        if 'gc_cst' in mcf['identification']['keywords'].keys():
            keywords_en.extend(mcf['identification']['keywords']['gc_cst']['keywords']['en'])  # noqa
            keywords_fr.extend(mcf['identification']['keywords']['gc_cst']['keywords']['fr'])  # noqa

        dict_['ows_identifier_value'] = mcf['metadata']['dataseturi']

    dict_['ows_keywordlist'] = ', '.join(keywords_en)
    dict_['ows_keywordlist_fr'] = ', '.join(keywords_fr)

    csw_url_params = urlencode({
        'service': 'CSW',
        'version': '2.0.2',
        'request': 'GetRecordById',
        'outputschema': 'csw:IsoRecord',
        'elementsetname': 'full',
        'id': metadata_identifier
    })

    url = 'https://csw.open.canada.ca/geonetwork/srv/csw?' + csw_url_params
    dict_['ows_metadataurl_href'] = url

    return dict_


def layer_time_config(layer_name):
    """
    # TODO: add description

    :param layer_name: name of layer

    :returns: `dict` of time values for layer (default time, time extent,
              default model run, model run extent)
    """

    st = load_plugin('store', PROVIDER_DEF)

    time_extent = st.get_key(
        f'geomet-data-registry_{layer_name}_time_extent', raw=True
    )
    default_time = st.get_key(
        f'geomet-data-registry_{layer_name}_default_time', raw=True
    )
    model_run_extent = st.get_key(
        f'geomet-data-registry_{layer_name}_model_run_extent', raw=True
    )
    default_model_run = st.get_key(
        f'geomet-data-registry_{layer_name}_default_model_run', raw=True
    )

    if not time_extent:
        msg = (
            f'Could not retrieve {layer_name} time extent'
            f' information from store. Skipping mapfile generation'
            f' for this layer.'
        )
        LOGGER.error(msg)
        raise LayerTimeConfigError(msg)

    intervals = []

    intervals = []

    if (time_extent and default_time) and not (
        model_run_extent and default_model_run
    ):
        nearest_interval = default_time
    else:
        start, end, interval = time_extent.split('/')

        start = datetime.strptime(start, DATEFORMAT)
        end = datetime.strptime(end, DATEFORMAT)
        regex_result = re.search('^P(T?)(\\d+)(.)', interval)
        time_ = regex_result.group(1)
        duration = regex_result.group(2)
        unit = regex_result.group(3)

        if time_ is None:
            # this means the duration is a date
            if unit == 'M':
                relative_delta = relativedelta(months=int(duration))
        else:
            # this means the duration is a time
            if unit == 'H':
                relative_delta = timedelta(hours=int(duration))
            elif unit == 'M':
                relative_delta = timedelta(minutes=int(duration))

        if start != end and relative_delta != timedelta(minutes=0):
            while start <= end:
                intervals.append(start)
                start += relative_delta
            nearest_interval = min(
                intervals, key=lambda interval: abs(interval - NOW)
            ).strftime(DATEFORMAT)
        else:
            nearest_interval = end.strftime(DATEFORMAT)

    time_config_dict = {
        'default_time': nearest_interval,
        'available_intervals': intervals,
        'time_extent': time_extent,
        'model_run_extent': model_run_extent,
        'default_model_run': default_model_run
    }

    return time_config_dict


def gen_web_metadata(m, c, url):
    """
    update mapfile MAP.WEB.METADATA section

    :param m: base mapfile JSON object  # TODO: really a dict?
    :param c: configuration YAML metadata object  # TODO: really a dict?
    :param url: URL of service

    :returns: dict of web metadata
    """

    LOGGER.debug('setting web metadata')

    d = {
        '__type__': 'metadata'
    }

    LOGGER.debug('Setting service identification metadata')

    d['ows_keywordlist_vocabulary'] = 'http://purl.org/dc/terms/'

    d['ows_fees'] = c['identification']['fees']
    d['ows_accessconstraints'] = c['identification']['accessconstraints']
    d['wms_getmap_formatlist'] = 'image/png,image/jpeg'
    d['ows_extent'] = ','.join(str(x) for x in m['extent'])
    d['ows_role'] = c['provider']['role']
    d['ows_http_max_age'] = 604800  # cache for one week
    d['ows_updatesequence'] = datetime.utcnow().strftime(DATEFORMAT)
    d['encoding'] = 'UTF-8'
    d['ows_srs'] = m['web']['metadata']['ows_srs']

    LOGGER.debug('Setting contact information')

    d['ows_addresstype'] = 'postal'

    d['ows_postcode'] = c['provider']['contact']['address']['postalcode']
    d['ows_contactelectronicmailaddress'] = \
        c['provider']['contact']['address']['email']

    d['ows_contactvoicetelephone'] = c['provider']['contact']['phone']['voice']
    d['ows_contactfacsimiletelephone'] = \
        c['provider']['contact']['phone']['fax']
    d['wms_enable_request'] = '*'
    d['wms_getfeatureinfo_formatlist'] = \
        'text/plain,application/json,application/vnd.ogc.gml'
    d['wms_attribution_logourl_format'] = c['provider']['logo']['format']
    d['wms_attribution_logourl_width'] = c['provider']['logo']['width']
    d['wms_attribution_logourl_height'] = c['provider']['logo']['height']
    d['wms_attribution_logourl_href'] = c['provider']['logo']['href']
    d['wcs_enable_request'] = '*'

    for lang in ['en', 'fr']:
        if lang == 'fr':
            _lang = '_fr'
            d['ows_onlineresource_fr'] = f'{url}?lang=fr'
        else:
            _lang = ''
            d['ows_onlineresource'] = url

        d[f'ows_address{_lang}'] = \
            c['provider']['contact']['address']['delivery_point'][lang]
        d[f'ows_keywordlist_http://purl.org/dc/terms/_items{_lang}'] =\
            ','.join(c['identification']['keywords'][lang])
        d[f'ows_contactinstructions{_lang}'] = \
            c['provider']['contact']['instructions'][lang]
        d[f'ows_contactperson{_lang}'] = \
            c['provider']['contact']['name'][lang]
        d[f'ows_contactposition{_lang}'] = \
            c['provider']['contact']['position'][lang]
        d[f'ows_contactorganization{_lang}'] = \
            c['provider']['name'][lang]
        d[f'ows_abstract{_lang}'] = \
            c['identification']['abstract'][lang]
        d[f'ows_service_onlineresource{_lang}'] = \
            c['identification']['url'][lang]
        service_title = f'{c["identification"]["title"][lang]} {__version__}'
        d[f'ows_title{_lang}'] = service_title
        d[f'wcs_label{_lang}'] = service_title
        d[f'ows_hoursofservice{_lang}'] = \
            c['provider']['contact']['hours'][lang]
        d[f'ows_stateorprovince{_lang}'] = \
            c['provider']['contact']['address']['stateorprovince'][lang]
        d[f'ows_city{_lang}'] = \
            c['provider']['contact']['address']['city'][lang]
        d[f'ows_country{_lang}'] = \
            c['provider']['contact']['address']['country'][lang]
        d[f'wms_attribution_title{_lang}'] = \
            c['attribution']['title'][lang]
        d[f'wms_attribution_onlineresource{_lang}'] = \
            c['attribution']['url'][lang]
        d[f'wcs_description{_lang}'] = \
            c['identification']['abstract'][lang]
        d[f'ows_keywordlist{_lang}'] = \
            ','.join(c['identification']['keywords'][lang])

    return d


def gen_layer(layer_name, layer_info):
    """
    mapfile layer object generator

    :param layer_name: name of layer
    :param layer_info: layer information

    :returns: list of mappyfile layer objects of layer
    """

    layers = []

    LOGGER.debug('Setting up layer configuration')

    layer = {}

    # get layer time information
    time_dict = layer_time_config(layer_name)

    layer['__type__'] = 'layer'
    layer['tolerance'] = 15
    layer['template'] = 'ttt.html'

    # build LAYER object
    layer['name'] = layer_name
    layer['debug'] = 5
    layer['data'] = ['']
    layer['type'] = 'RASTER'
    layer['template'] = "ttt.html"
    layer['tolerance'] = 15

    layer['metadata'] = {
        '__type__': 'metadata',
        'gml_include_items': 'all',
        'ows_include_items': 'all'
    }

    # set layer projection
    LOGGER.debug('Setting up layer projection')
    proj_file = os.path.join(THISDIR, 'resources',
                             layer_info['forecast_model']['projection'])
    with open(proj_file) as f:
        lines = [l.replace('\n', '').replace('"', '') for l in f.readlines()]  # noqa
        layer['projection'] = lines

    # set layer processing directives
    LOGGER.debug('Setting up layer processing directives')
    layer['processing'] = []
    if 'processing' in layer_info:
        for item in layer_info['processing']:
            layer['processing'].append(item)
    if 'processing' in layer_info['forecast_model']:
        for item in layer_info['forecast_model']['processing']:
            layer['processing'].append(item)

    # set type
    if 'type' in layer_info:
        LOGGER.debug('Setting up layer type')
        layer['type'] = layer_info['type']

    # set connectiontype
    if 'conntype' in layer_info:
        LOGGER.debug('Setting up layer connection type')
        layer['connectiontype'] = layer_info['conntype']
        # if uvraster also set the layer extent
        if (layer_info['conntype'] == 'uvraster'
                and 'extent' in layer_info['forecast_model']):
            layer['extent'] = layer_info['forecast_model']['extent']

    # set additional layer params
    if 'layer_params' in layer_info:
        LOGGER.debug('Setting up additional layer params')
        for params in layer_info['layer_params']:
            param, value = params.split()
            layer[param] = value

    # set layer classes
    LOGGER.debug('Setting layer styles')
    layer['classgroup'] = layer_info['styles'][0].split("/")[-1].strip('.json')

    layer['classes'] = []
    for style in layer_info['styles']:
        with open(
            os.path.join(THISDIR, 'resources', style)
        ) as json_style:
            for class_ in json.load(json_style):
                layer['classes'].append(class_)

    # set layer metadata
    LOGGER.debug('Setting layer metadata')
    layer['metadata'] = {}

    # source = yaml config
    layer['metadata']['ows_extent'] = layer_info['forecast_model']['extent']  # noqa
    layer['metadata']['ows_title'] = layer_info['label_en']
    layer['metadata']['ows_title_fr'] = layer_info['label_fr']
    layer['metadata']['wms_layer_group'] = f'/{layer_info["forecast_model"]["label_en"]}'  # noqa
    layer['metadata']['wms_layer_group_fr'] = f'/{layer_info["forecast_model"]["label_fr"]}'  # noqa
    layer['metadata']['wcs_label'] = layer_info['label_en']
    layer['metadata']['wcs_label_fr'] = layer_info['label_fr']

    if 'metadata' in layer_info:
        for md in layer_info['metadata']:
            md_key, md_value = md.split('=')
            layer['metadata'][md_key] = md_value

    if 'metadata' in layer_info['forecast_model']:
        for md in layer_info['forecast_model']['metadata']:
            md_key, md_value = md.split('=')
            layer['metadata'][md_key] = md_value

    if 'dimensions' in layer_info["forecast_model"]:
        size = (
            f'{layer_info["forecast_model"]["dimensions"][0]} '
            f'{layer_info["forecast_model"]["dimensions"][1]}'
        )
        layer['metadata']['ows_size'] = size

    if time_dict:
        layer['metadata']['wms_dimensionlist'] = 'reference_time'
        layer['metadata']['wms_reference_time_item'] = 'reference_datetime'
        layer['metadata']['wms_reference_time_units'] = 'ISO8601'
        layer['metadata']['wms_timeextent'] = time_dict['time_extent']
        layer['metadata']['wms_reference_time_default'] = \
            time_dict['default_model_run']

        layer['metadata']['wms_timedefault'] = time_dict['default_time']

        if time_dict['available_intervals']:
            layer['metadata']['wms_available_intervals'] = ','.join(
                [
                    dt.strftime(DATEFORMAT)
                    for dt in time_dict['available_intervals']
                ]
            )

        if time_dict['default_model_run']:
            layer['metadata']['wms_reference_time_extent'] = \
                time_dict['model_run_extent']

    if 'forecast_hour_interval' in layer_info['forecast_model']:
        seconds = layer_info['forecast_model']['forecast_hour_interval'] * 60 * 60  # noqa
    elif 'observations_interval_min' in layer_info['forecast_model']:
        seconds = layer_info['forecast_model']['observations_interval_min'] * 60  # noqa
    else:
        seconds = ''

    layer['metadata']['geomet_ows_http_max_age'] = seconds

    # generic metadata
    layer['metadata']['gml_include_items'] = 'all'
    layer['metadata']['ows_authorityurl_name'] = 'msc'
    layer['metadata']['ows_authorityurl_href'] = 'https://dd.weather.gc.ca'
    layer['metadata']['ows_identifier_authority'] = 'msc'
    layer['metadata']['ows_include_items'] = 'all'
    layer['metadata']['ows_keywordlist_vocabulary'] = 'http://purl.org/dc/terms/'  # noqa
    layer['metadata']['ows_geomtype'] = 'Geometry'
    layer['metadata']['ows_metadataurl_format'] = 'text/xml'
    layer['metadata']['ows_metadataurl_type'] = 'TC211'
    layer['metadata']['wcs_rangeset_name'] = 'default range'
    layer['metadata']['wcs_rangeset_label'] = 'default range'
    layer['metadata']['wfs_metadataurl_format'] = 'XML'

    LOGGER.debug('Reading MCF and updating layer metadata')

    mcf_file = os.path.join(THISDIR, 'resources', 'mcf',
                            layer_info['forecast_model']['mcf'])

    layer['metadata'].update(mcf2layer_metadata(mcf_file))

    layers.append(layer)

    return layers


def generate_mapfile(layer=None, output='file', use_includes=True):
    st = load_plugin('store', PROVIDER_DEF)
    time_errors = False
    output_dir = f'{BASEDIR}{os.sep}mapfile'

    all_layers = []

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(MAPFILE_BASE) as fh:
        mapfile = json.load(fh, object_pairs_hook=OrderedDict)
        symbols_file = os.path.join(THISDIR, 'resources/mapserv/symbols.json')
        with open(symbols_file) as fh2:
            mapfile['symbols'] = json.load(fh2)

    with open(CONFIG) as fh:
        cfg = load(fh, Loader=CLoader)

    if layer is not None:
        mapfiles = {layer: cfg['layers'][layer]}
    else:
        mapfiles = cfg['layers']

    # set PROJ_LIB path
    mapfile['config']['proj_lib'] = os.path.join(
        THISDIR, 'resources', 'mapserv'
    )

    mapfile['web']['metadata'] = gen_web_metadata(
        mapfile, cfg['metadata'], URL
    )

    for key, value in mapfiles.items():
        mapfile_copy = deepcopy(mapfile)
        mapfile_copy['layers'] = []

        try:
            layers = gen_layer(key, value)
        except LayerTimeConfigError:
            layers = None
            time_errors = True

        if layers:
            for lyr in layers:
                mapfile_copy['layers'].append(lyr)

            # TODO: simplify
            if 'outputformats' in value['forecast_model']:
                mapfile_copy['outputformats'] = [
                    format_
                    for format_ in mapfile_copy['outputformats']
                    if format_['name']
                    in value['forecast_model']['outputformats']
                ]

            # TODO: simplify
            if 'symbols' in value:
                mapfile_copy['symbols'] = [
                    symbol
                    for symbol in mapfile_copy['symbols']
                    if symbol['name'] in value['symbols']
                    or any(
                        symbol_ in symbol['name']
                        for symbol_ in value['symbols']
                    )
                ]
            else:
                mapfile_copy['symbols'] = []

        layer_only_filepath = (
            f'{output_dir}{os.sep}geomet-weather-{key}_layer.map'
        )

        # collect and write LAYER-only mapfile to disk in order to use
        # in global mapfile with INCLUDE directive
        all_layers.append(layer_only_filepath)
        with open(layer_only_filepath, 'w', encoding='utf-8') as fh:
            mappyfile.dump(mapfile_copy['layers'], fh)

        if output == 'file' and mapfile_copy['layers']:
            mapfile_filepath = f'{output_dir}{os.sep}geomet-weather-{key}.map'
            with open(mapfile_filepath, 'w', encoding='utf-8') as fh:
                if use_includes:
                    mapfile['include'] = [layer_only_filepath]
                    mappyfile.dump(mapfile, fh)
                else:
                    mappyfile.dump(mapfile_copy, fh)

        elif output == 'store' and mapfile_copy['layers']:
            st.set_key(f'{key}_mapfile', mappyfile.dumps(mapfile_copy))
            st.set_key(f'{key}_layer', mappyfile.dumps(mapfile_copy['layers']))

    if layer is None:  # generate entire mapfile
        # always write global mapfile to disk for caching purposes
        mapfile['include'] = all_layers
        filename = 'geomet-weather.map'
        filepath = f'{output_dir}{os.sep}{filename}'

        with open(filepath, 'w', encoding='utf-8') as fh:
            mappyfile.dump(mapfile, fh)
        # also write to store if required
        if output == 'store':
            st.set_key('geomet-weather_mapfile', mappyfile.dumps(mapfile))

    # returns False if time keys could not be retrieved (meaning empty/no
    # layer mapfiles generated)
    if time_errors:
        return False

    return True


def find_replace_wms_timedefault(mapfile):
    """
    Finds the wms_timedefault and wms_available_intervals and updates the
    wms_timedefault value to the closest interval to the time of call.
    :param layer: `str` of layer ID to update
    :returns: `bool` of update result
    """
    # search for entire wms_timedefault line in mapfile
    wms_timedefault_regex = '(.*"wms_timedefault".")(.*)(")'
    wms_timedefault = re.search(wms_timedefault_regex, mapfile)
    # search for entire wms_available_intervals line in mapfile
    wms_available_intervals_regex = '(.*"wms_available_intervals".")(.*)(")'
    wms_available_intervals = re.search(wms_available_intervals_regex, mapfile)
    if wms_available_intervals:
        # retrieve and split intervals into list
        wms_available_intervals = wms_available_intervals.group(2).split(',')
        intervals = [
            datetime.strptime(dt, DATEFORMAT) for dt in wms_available_intervals
        ]
        # get nearest interval to now and convert to string
        nearest = get_nearest(intervals, datetime.utcnow())
        nearest = nearest.strftime(DATEFORMAT)
        # update wms_timedefault metadata value with nearest
        # interval
        LOGGER.debug(
            f'Updating wms_timedefault from {wms_timedefault.group(2)} to '
            f'{nearest}.'
        )
        mapfile = re.sub(
            wms_timedefault_regex,
            (
                f'{wms_timedefault.group(1)}{nearest}'
                f'{wms_timedefault.group(3)}'
            ),
            mapfile,
        )
    else:
        LOGGER.debug(
            f'Mapfile ({mapfile}) does not contain '
            f'wms_available_intervals metadata. Not updating '
            f'wms_timedefault.'
        )

    return mapfile


def update_mapfile(layer=None):
    """
    Updates a mapfile.
    :param layer: `str` of layer ID to update
    :returns: `bool` of update result
    """
    if layer:
        mapfiles = [
            f'{BASEDIR}{os.sep}mapfile{os.sep}geomet-weather-{layer}_layer.map'
        ]
    else:
        mapfiles = glob(f'{BASEDIR}{os.sep}mapfile{os.sep}*_layer.map')
    for mapfile in mapfiles:
        try:
            LOGGER.debug(f'Updating {mapfile}.')
            with open(mapfile, 'r+') as fp:
                mapfile_ = fp.read()
                mapfile_ = find_replace_wms_timedefault(mapfile_)
                # go to start of file and re-write mapfile
                fp.seek(0)
                fp.write(mapfile_)
        except FileNotFoundError as e:
            LOGGER.error(e)
            pass

    # update mapfiles in store if MAPFILE_STORAGE set to store
    if MAPFILE_STORAGE == 'store':
        st = load_plugin('store', PROVIDER_DEF)
        if layer:
            mapfiles = [st.get_key(f'{layer}_layer')]
        else:
            mapfile_dicts = [
                {'key': key, 'mapfile': st.get_key(f'{key}', raw=True)}
                for key in st.list_keys('geomet-mapfile*_layer')
            ]
        for mapfile_dict in mapfile_dicts:
            LOGGER.debug(f'Updating {mapfile_dict["key"]} in store.')
            mapfile_ = find_replace_wms_timedefault(mapfile_dict['mapfile'])
            st.set_key(mapfile_dict['key'], mapfile_, raw=True)

    return True


@click.group()
def mapfile():
    """mapfile management"""
    pass


@click.command()
@click.pass_context
@click.option('--layer', '-l', help='layer name')
@click.option(
    '--output',
    '-o',
    type=click.Choice(['store', 'file']),
    default='file',
    help='Write to configured store or to disk',
    required=True,
)
@click.option(
    '--includes/--no-includes',
    default=True,
    help='Indicated whether to use INCLUDE directives in mapfile',
)
def generate(ctx, layer, output, includes):
    generate_mapfile(layer, output, includes)


@click.command(name='update')
@click.pass_context
@click.option('--layer', '-l', help='layer name')
def update(ctx, layer):
    """update mapfile(s) wms_timedefault value"""
    update_mapfile(layer)


mapfile.add_command(generate)
mapfile.add_command(update)


class LayerTimeConfigError(Exception):
    pass
