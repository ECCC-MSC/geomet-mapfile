from collections import OrderedDict
from configparser import ConfigParser
from copy import deepcopy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import logging
import os
import re
import shutil

import click
import mappyfile
from yaml import load, CLoader

from geomet3_mapfile import __version__
from geomet3_mapfile.plugin import load_plugin
from geomet3_mapfile.env import BASEDIR, DATADIR, CONFIG, URL, STORE_TYPE, STORE_URL
from geomet3_mapfile.utils.utils import DATEFORMAT

MAPFILE_BASE = f'{os.path.dirname(os.path.realpath(__file__))}{os.sep}resources{os.sep}mapfile-base.json'

LOGGER = logging.getLogger(__name__)

THISDIR = os.path.dirname(os.path.realpath(__file__))

NOW = datetime.utcnow()

CALCULATED_TIME_EXTENTS = {}

PROVIDER_DEF = {
    'type': STORE_TYPE,
    'url': STORE_URL,
}

def layer_time_config(layer_name):
    """
    :param layer_name: name of layer
    :returns: `dict` of time values for layer (default time, time extent, default model run, model run extent)
    """

    model = layer_name.split('.')[0]
    st = load_plugin('store', PROVIDER_DEF)

    time_extent = st.get_key(f'{layer_name}_time_extent') if st.get_key(f'{layer_name}_time_extent') is not None else None  # noqa
    model_run_extent = st.get_key(f'{layer_name}_model_run_extent') if st.get_key(f'{layer_name}_model_run_extent') is not None else None  # noqa
    default_model_run = st.get_key(f'{layer_name}_default_model_run') if st.get_key(f'{layer_name}_default_model_run') is not None else None  # noqa

    if not time_extent:
        LOGGER.error(f'Could not retrieve {layer_name} time extent information from store.'
                     f' Skipping mapfile generation for this layer.')
        return False

    start, end, interval = time_extent.split('/')
    if default_model_run == start:
        key = f'{model}_{interval}'
    else:
        key = f'{model}_{interval}_future'
   
    if key not in CALCULATED_TIME_EXTENTS:
    
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

        intervals = []

        if start != end and relative_delta != timedelta(minutes=0):
            while start <= end:
                intervals.append(start)
                start += relative_delta
            nearest_interval = min(intervals, key=lambda interval: abs(interval - NOW)).strftime(DATEFORMAT)
        else:
            nearest_interval = end.strftime(DATEFORMAT)

        CALCULATED_TIME_EXTENTS[key] = nearest_interval

    else:
        nearest_interval = CALCULATED_TIME_EXTENTS[key]

    time_config_dict = {
        'default_time': nearest_interval,
        'time_extent': time_extent,
        'model_run_extent': model_run_extent,
        'default_model_run': default_model_run
    }

    return time_config_dict


def gen_web_metadata(m, c, url):
    """
    update mapfile MAP.WEB.METADATA section
    :param m: base mapfile JSON object
    :param c: configuration YAML metadata object
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
    d['ows_updatesequence'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    d['encoding'] = 'UTF-8'
    d['ows_srs'] = m['web']['metadata']['ows_srs']

    LOGGER.debug('Setting contact information')

    d['ows_addresstype'] = 'postal'
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

    if time_dict:

        # layer_tileindex = {
        #     '__type__': 'layer',
        #     'name': f'{layer_name}_idx'
        # }

        layer['__type__'] = 'layer'
        layer['tolerance'] = 15
        layer['template']: 'ttt.html'

    #    # build tileindex LAYER object (only for raster, uv and wind layers)
    #    if layer_info['type'] == 'raster' or ('conntype' in layer_info and
    #                                          layer_info['conntype'].lower() in ['uvraster', 'contour']):
    #        layer_tileindex['type'] = 'POLYGON'
    #        layer_tileindex['status'] = 'OFF'
    #        layer_tileindex['CONNECTIONTYPE'] = 'OGR'
    #
    #        layer_tileindex['CONNECTION'] = f'"{TILEINDEX_URL}"'
    #        layer_tileindex['metadata'] = {
    #            '__type__': 'metadata',
    #            'ows_enable_request': '!*',
    #        }
    #        layer_tileindex['filter'] = ''
    #
    #        layers.append(layer_tileindex)

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

    #    # add reference to tileindex if tileindex is being used
    #    if layer_tileindex in layers:
    #        layer['tileindex'] = layer_tileindex['name']
    #        layer['tileitem'] = 'properties.filepath'

        # set layer projection
        with open(os.path.join(THISDIR, 'resources', layer_info['forecast_model']['projection'])) as f:
            lines = [line.replace("\n", "").replace('"', "") for line in f.readlines()]
            layer['projection'] = lines

        # set layer processing directives
        layer['processing'] = []
        if 'processing' in layer_info:
            for item in layer_info['processing']:
                layer['processing'].append(item)
        if 'processing' in layer_info['forecast_model']:
            for item in layer_info['forecast_model']['processing']:
                layer['processing'].append(item)

        # set type
        if 'type' in layer_info:
            layer['type'] = layer_info['type']

        # set connectiontype
        if 'conntype' in layer_info:
            layer['CONNECTIONTYPE'] = layer_info['conntype']
            # if uvraster also set the layer extent
            if layer_info['conntype'] == 'uvraster' and 'extent' in layer_info['forecast_model']:
                layer['extent'] = layer_info['forecast_model']['extent']

        # set additional layer params
        if 'layer_params' in layer_info:
            for params in layer_info['layer_params']:
                param, value = params.split()
                layer[param] = value

        # set layer classes
        layer['classgroup'] = layer_info['styles'][0].split("/")[-1].strip(".inc")
        layer['include'] = [os.path.join(DATADIR, style) for style in layer_info['styles']]

        # set layer metadata
        layer['metadata'] = {}

        # source = yaml config
        layer['metadata']['ows_extent'] = layer_info['forecast_model']['extent']
        layer['metadata']['ows_title'] = layer_info['label_en']
        layer['metadata']['ows_title_fr'] = layer_info['label_fr']
        layer['metadata']['wms_layer_group'] = f'/{layer_info["forecast_model"]["label_en"]}'
        layer['metadata']['wms_layer_group_fr'] = f'/{layer_info["forecast_model"]["label_fr"]}'
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
            layer['metadata']['ows_size'] = f'{layer_info["forecast_model"]["dimensions"][0]} ' \
                f'{layer_info["forecast_model"]["dimensions"][1]}'

        if time_dict:
            layer['metadata']['wms_dimensionlist'] = 'reference_time'
            layer['metadata']['wms_reference_time_item'] = 'properties.reference_datetime'
            layer['metadata']['wms_reference_time_units'] = 'ISO8601'
            layer['metadata']['wms_timeextent'] = time_dict['time_extent']
            layer['metadata']['wms_timedefault'] = time_dict['default_time']
            layer['metadata']['wms_reference_time_extent'] = time_dict['model_run_extent']
            layer['metadata']['wms_reference_time_default'] = time_dict['default_model_run']

        if 'forecast_hour_interval' in layer_info['forecast_model']:
            seconds = layer_info['forecast_model']['forecast_hour_interval'] * 60 * 60
            layer['metadata']['geomet_ows_http_max_age'] = f'{seconds}'
        elif 'observations_interval_min' in layer_info['forecast_model']:
            seconds = layer_info['forecast_model']['observations_interval_min'] * 60
            layer['metadata']['geomet_ows_http_max_age'] = f'{seconds}'
        else:
            layer['metadata']['geomet_ows_http_max_age'] = ''

        # source = mcf
        # TODO: For Geomet3 we should get rid of all .mcf files and replace them with .yml files?
        if layer_info['forecast_model']['mcf'].endswith('.mcf'):
            mcf = ConfigParser()
            with open(os.path.join(THISDIR, 'resources/mcf', layer_info['forecast_model']['mcf'])) as f:
                mcf.read_file(f)
            layer['metadata']['ows_abstract'] = mcf.get('identification', 'abstract_en')
            layer['metadata']['ows_abstract_fr'] = mcf.get('identification', 'abstract_fr')
            layer['metadata']['ows_keywordlist'] = ', '.join([mcf.get('identification', 'keywords_en')])
            layer['metadata']['ows_keywordlist_fr'] = ', '.join([mcf.get('identification', 'keywords_fr')])
            if mcf.has_option('identification', 'keywords_gc_cst_en'):
                layer['metadata']['ows_keywordlist'] += f', {", ".join([mcf.get("identification", "keywords_gc_cst_en")])}'  # noqa
            if mcf.has_option('identification', 'keywords_gc_cst_fr'):
                layer['metadata']['ows_keywordlist_fr'] += f', {", ".join([mcf.get("identification", "keywords_gc_cst_fr")])}'  # noqa
            layer['metadata']['ows_identifier_value'] = mcf.get('metadata', 'dataseturi')
            layer['metadata']['ows_metadataurl_href'] = ('https://csw.open.canada.ca/geonetwork/srv/csw?'
                                                         'service=CSW&'
                                                         'version=2.0.2&'
                                                         'request=GetRecordById&'
                                                         'outputschema=csw:IsoRecord&'
                                                         'elementsetname=full&'
                                                         f'id={mcf.get("metadata", "identifier")}')

        elif layer_info['forecast_model']['mcf'].endswith('.yml'):
            with open(os.path.join(THISDIR, 'resources/mcf', layer_info['forecast_model']['mcf'])) as f:
                mcf = load(f, Loader=CLoader)
                layer['metadata']['ows_abstract'] = mcf['identification']['abstract_en']
                layer['metadata']['ows_abstract_fr'] = mcf['identification']['abstract_fr']
                layer['metadata']['ows_keywordlist'] = ', '.join(mcf['identification']
                                                                 ['keywords']['default']['keywords_en'])
                layer['metadata']['ows_keywordlist_fr'] = ', '.join(mcf['identification']
                                                                    ['keywords']['default']['keywords_fr'])
                if 'gc_cst' in mcf['identification']['keywords'].keys():
                    layer['metadata']['ows_keywordlist'] += f', {", ".join(mcf["identification"]["keywords"]["gc_cst"]["keywords_en"])}'   # noqa
                    layer['metadata']['ows_keywordlist_fr'] += f', {", ".join(mcf["identification"]["keywords"]["gc_cst"]["keywords_fr"])}'   # noqa
                layer['metadata']['ows_identifier_value'] = mcf['metadata']['dataseturi']
                layer['metadata']['ows_metadataurl_href'] = ('https://csw.open.canada.ca/geonetwork/srv/csw?'
                                                             'service=CSW&'
                                                             'version=2.0.2&'
                                                             'request=GetRecordById&'
                                                             'outputschema=csw:IsoRecord&'
                                                             'elementsetname=full&'
                                                             f'id={mcf["metadata"]["identifier"]}')
        # generic metadata
        layer['metadata']['gml_include_items'] = 'all'
        layer['metadata']['ows_authorityurl_name'] = 'msc'
        layer['metadata']['ows_authorityurl_href'] = 'https://dd.weather.gc.ca'
        layer['metadata']['ows_identifier_authority'] = 'msc'
        layer['metadata']['ows_include_items'] = 'all'
        layer['metadata']['ows_keywordlist_vocabulary'] = 'http://purl.org/dc/terms/'
        layer['metadata']['ows_geomtype'] = 'Geometry'
        layer['metadata']['ows_metadataurl_format'] = 'text/xml'
        layer['metadata']['ows_metadataurl_type'] = 'TC211'
        layer['metadata']['wcs_rangeset_name'] = 'Default Range'
        layer['metadata']['wcs_rangeset_label'] = 'Default Range'
        layer['metadata']['wfs_metadataurl_format'] = 'XML'

        layers.append(layer)

    return layers


@click.group(name='mapfile')
def generate_mapfile():
    """Generate mapfile(s)"""
    pass

@click.command()
@click.pass_context
@click.option('--layer', '-lyr', help='GeoMet-Weather layer ID')
@click.option('--map/--no-map', 'map_', default=True, help="Output with or without mapfile MAP object")
@click.option('--output', '-o', type=click.Choice(['store', 'mapfile']),
              help="Write to configured store or to disk", required=True)
def generate(ctx, layer, map_, output):
    """generate mapfile"""

    st = load_plugin('store', PROVIDER_DEF)

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
        mapfiles = {
          layer: cfg['layers'][layer]
        }
    else:
        mapfiles = cfg['layers']

    mapfile['web']['metadata'] = gen_web_metadata(mapfile, cfg['metadata'], URL)

    for key, value in mapfiles.items():
        mapfile_copy = deepcopy(mapfile)
        mapfile_copy['layers'] = []

        layers = gen_layer(key, value)

        if layers:
            for lyr in layers:
                mapfile_copy['layers'].append(lyr)
                all_layers.append(lyr)

            if 'outputformats' in value['forecast_model']:
                mapfile_copy['outputformats'] = [format_ for format_ in mapfile_copy['outputformats']
                                                 if format_['name'] in value['forecast_model']['outputformats']]

            if 'symbols' in value:
                mapfile_copy['symbols'] = [symbol for symbol in mapfile_copy['symbols'] if symbol['name'] in
                                           value['symbols'] or any(symbol_ in symbol['name']
                                                                   for symbol_ in value['symbols'])]
            else:
                mapfile_copy['symbols'] = []

            filename = f'geomet-weather-{key}.map' if map_ else f'geomet-weather-{key}_layer.map'
            filepath = f'{output_dir}{os.sep}{filename}'

            if output == 'mapfile':
                with open(filepath, 'w', encoding='utf-8') as fh:
                    if map_:
                        mappyfile.dump(mapfile_copy, fh)
                    else:
                        mappyfile.dump(mapfile_copy['layers'], fh)

            elif output == 'store':

                if map_:
                    st.set_key(f'{key}_mapfile', mappyfile.dumps(mapfile_copy))
                else:
                    st.set_key(f'{key}_layer', mappyfile.dumps(mapfile_copy['layers']))

    if layer is None:  # generate entire mapfile

        mapfile['layers'] = all_layers

        if output == 'mapfile':
            filename = 'geomet-weather.map'
            filepath = f'{output_dir}{os.sep}{filename}'

            with open(filepath, 'w', encoding='utf-8') as fh:
                mappyfile.dump(mapfile, fh)

        if output == 'store':
            st.set_key(f'geomet-weather_mapfile', mappyfile.dumps(mapfile))

    epsg_file = os.path.join(THISDIR, 'resources', 'mapserv', 'EPSG')
    shutil.copy2(epsg_file, os.path.join(BASEDIR, output_dir))


generate_mapfile.add_command(generate)
