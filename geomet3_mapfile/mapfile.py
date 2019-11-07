from collections import OrderedDict
from configparser import ConfigParser
from copy import deepcopy
from datetime import datetime
import json
import logging
import os
import shutil

import click
import mappyfile
from yaml import load, CLoader

from geomet3_mapfile import __version__
from geomet3_mapfile.plugin import load_plugin
from geomet3_mapfile.env import BASEDIR, DATADIR, CONFIG, TILEINDEX_URL, URL, STORE_TYPE, STORE_URL

MAPFILE_BASE = f'{os.path.dirname(os.path.realpath(__file__))}{os.sep}resources{os.sep}mapfile-base.json'

LOGGER = logging.getLogger(__name__)

THISDIR = os.path.dirname(os.path.realpath(__file__))


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
            d['ows_onlineresource_fr'] = '{}?lang=fr'.format(url)
        else:
            _lang = ''
            d['ows_onlineresource'] = url

        d['ows_address{}'.format(_lang)] = \
            c['provider']['contact']['address']['delivery_point'][lang]
        d['ows_keywordlist_http://purl.org/dc/terms/_items{}'.format(_lang)] =\
            ','.join(c['identification']['keywords'][lang])
        d['ows_contactinstructions{}'.format(_lang)] = \
            c['provider']['contact']['instructions'][lang]
        d['ows_contactperson{}'.format(_lang)] = \
            c['provider']['contact']['name'][lang]
        d['ows_contactposition{}'.format(_lang)] = \
            c['provider']['contact']['position'][lang]
        d['ows_contactorganization{}'.format(_lang)] = \
            c['provider']['name'][lang]
        d['ows_abstract{}'.format(_lang)] = \
            c['identification']['abstract'][lang]
        d['ows_service_onlineresource{}'.format(_lang)] = \
            c['identification']['url'][lang]
        service_title = u'{} {}'.format(
            c['identification']['title'][lang], __version__)
        d['ows_title{}'.format(_lang)] = service_title
        d['wcs_label{}'.format(_lang)] = service_title
        d['ows_hoursofservice{}'.format(_lang)] = \
            c['provider']['contact']['hours'][lang]
        d['ows_stateorprovince{}'.format(_lang)] = \
            c['provider']['contact']['address']['stateorprovince'][lang]
        d['ows_city{}'.format(_lang)] = \
            c['provider']['contact']['address']['city'][lang]
        d['ows_country{}'.format(_lang)] = \
            c['provider']['contact']['address']['country'][lang]
        d['wms_attribution_title{}'.format(_lang)] = \
            c['attribution']['title'][lang]
        d['wms_attribution_onlineresource{}'.format(_lang)] = \
            c['attribution']['url'][lang]
        d['wcs_description{}'.format(_lang)] = \
            c['identification']['abstract'][lang]
        d['ows_keywordlist{}'.format(_lang)] = \
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

    layer_tileindex = {
        '__type__': 'layer',
        'name': f'{layer_name}_idx'
    }

    layer = {
        '__type__': 'layer',
        'tolerance': 15,
        'template': 'ttt.html'
    }

    # build tileindex LAYER object (only for raster, uv and wind layers)
    if layer_info['type'] == 'raster' or ('conntype' in layer_info and
                                          layer_info['conntype'].lower() in ['uvraster', 'contour']):
        layer_tileindex['type'] = 'POLYGON'
        layer_tileindex['status'] = 'OFF'
        layer_tileindex['CONNECTIONTYPE'] = 'OGR'

        layer_tileindex['CONNECTION'] = f'"{TILEINDEX_URL}"'
        layer_tileindex['metadata'] = {
            '__type__': 'metadata',
            'ows_enable_request': '!*',
        }
        layer_tileindex['filter'] = ''

        layers.append(layer_tileindex)

    # build LAYER object
    layer['name'] = layer_name
    layer['debug'] = 5
    layer['type'] = 'RASTER'
    layer['template'] = "ttt.html"
    layer['tolerance'] = 15

    layer['metadata'] = {
        '__type__': 'metadata',
        'gml_include_items': 'all',
        'ows_include_items': 'all'
    }

    # add reference to tileindex if tileindex is being used
    if layer_tileindex in layers:
        layer['tileindex'] = layer_tileindex['name']
        layer['tileitem'] = 'properties.filepath'

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

    if layer_info['time_enabled'] in ['yes', 'future']:
        layer['metadata']['wms_dimensionlist'] = 'reference_time'
        layer['metadata']['wms_reference_time_item'] = 'properties.reference_datetime'
        layer['metadata']['wms_reference_time_units'] = 'ISO8601'
        layer['metadata']['wms_timeextent'] = ''
        layer['metadata']['wms_timedefault'] = ''
        layer['metadata']['wms_reference_time_extent'] = ''
        layer['metadata']['wms_reference_time_default'] = ''

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


@click.group()
def mapfile():
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

    output_dir = '{}{}mapfile'.format(BASEDIR, os.sep)
    
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

        for lyr in layers:
            mapfile_copy['layers'].append(lyr)
            all_layers.append(lyr)

        if 'outputformats' in value['forecast_model']:
            mapfile_copy['outputformats'] = [format_ for format_ in mapfile_copy['outputformats'] if format_['name'] in
                                             value['forecast_model']['outputformats']]

        if 'symbols' in value:
            mapfile_copy['symbols'] = [symbol for symbol in mapfile_copy['symbols'] if symbol['name'] in
                                       value['symbols'] or any(symbol_ in symbol['name']
                                                               for symbol_ in value['symbols'])]
        else:
            mapfile_copy['symbols'] = []

        filename = 'geomet-weather-{}.map'.format(key) if map_ else 'geomet-weather-{}_layer.map'.format(key)
        filepath = '{}{}{}'.format(output_dir, os.sep, filename)

        if output == 'mapfile':
            with open(filepath, 'w', encoding='utf-8') as fh:
                if map_:
                    mappyfile.dump(mapfile_copy, fh)
                else:
                    mappyfile.dump(mapfile_copy['layers'], fh)

        elif output == 'store':

            provider_def = {
                'type': STORE_TYPE,
                'url': STORE_URL,
            }
            st = load_plugin('store', provider_def)

            if map_:
                st.set_key(f'{key}_mapfile', mappyfile.dumps(mapfile_copy))
            else:
                st.set_key(f'{key}_layer', mappyfile.dumps(mapfile_copy['layers']))

    if layer is None:  # generate entire mapfile

        mapfile['layers'] = all_layers

        if output == 'mapfile':

            filename = 'geomet-weather.map'
            filepath = '{}{}{}'.format(output_dir, os.sep, filename)

            with open(filepath, 'w', encoding='utf-8') as fh:
                mappyfile.dump(mapfile, fh)

        if output == 'store':

            provider_def = {
                'type': STORE_TYPE,
                'url': STORE_URL,
            }

            st = load_plugin('store', provider_def)
            st.set_key(f'geomet-weather_mapfile', mappyfile.dumps(mapfile))

    epsg_file = os.path.join(THISDIR, 'resources', 'mapserv', 'epsg')
    shutil.copy2(epsg_file, os.path.join(BASEDIR, 'mapfile'))


mapfile.add_command(generate)
