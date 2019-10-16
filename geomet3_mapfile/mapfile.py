import ast
from collections import OrderedDict
from configparser import SafeConfigParser
from datetime import datetime
import json
import logging
import os

import click
import mappyfile
import yaml
from yaml import Loader

MAPFILE_BASE = '{}{}resources{}mapfile-base.json'.format(os.path.dirname(
    os.path.realpath(__file__)), os.sep, os.sep)

LOGGER = logging.getLogger(__name__)

THISDIR = os.path.dirname(os.path.realpath(__file__))


def gen_web_metadata(m, c, lang, service, url):
    """
    update mapfile MAP.WEB.METADATA section

    :param m: base mapfile JSON object
    :param c: configuration YAML metadata object
    :param lang: language (en or fr)
    :param service: service (WMS or WCS)
    :param url: URL of service

    :returns: dict of web metadata
    """

    LOGGER.debug('setting web metadata')

    d = {
        '__type__': 'metadata'
    }

    LOGGER.debug('Language: {}'.format(lang))
    LOGGER.debug('Service: {}'.format(service))

    if lang == 'fr':
        d['ows_onlineresource'] = '{}?lang=fr'.format(url)
    else:
        d['ows_onlineresource'] = url

    LOGGER.debug('URL: {}'.format(d['ows_onlineresource']))

    LOGGER.debug('Setting service identification metadata')

    service_title = u'{} {}'.format(
        c['identification']['title'][lang], 1)

    d['ows_title'] = service_title
    d['ows_abstract'] = c['identification']['abstract'][lang]
    d['ows_keywordlist_vocabulary'] = 'http://purl.org/dc/terms/'
    d['ows_keywordlist_http://purl.org/dc/terms/_items'] = ','.join(
        c['identification']['keywords'][lang])

    d['ows_fees'] = c['identification']['fees']
    d['ows_accessconstraints'] = c['identification']['accessconstraints']
    d['wms_getmap_formatlist'] = 'image/png,image/jpeg'
    d['ows_extent'] = ','.join(str(x) for x in m['extent'])
    d['ows_role'] = c['provider']['role']
    d['ows_http_max_age'] = 604800  # cache for one week
    d['ows_updatesequence'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    d['ows_service_onlineresource'] = c['identification']['url'][lang]
    d['encoding'] = 'UTF-8'
    d['ows_srs'] = m['web']['metadata']['ows_srs']

    LOGGER.debug('Setting contact information')
    d['ows_contactperson'] = c['provider']['contact']['name'][lang]
    d['ows_contactposition'] = c['provider']['contact']['position'][lang]
    d['ows_contactorganization'] = c['provider']['name'][lang]
    d['ows_address'] = \
        c['provider']['contact']['address']['delivery_point'][lang]

    d['ows_addresstype'] = 'postal'
    d['ows_addresstype'] = 'postal'
    d['ows_city'] = c['provider']['contact']['address']['city'][lang]
    d['ows_stateorprovince'] = \
        c['provider']['contact']['address']['stateorprovince'][lang]

    d['ows_postcode'] = c['provider']['contact']['address']['postalcode']
    d['ows_country'] = c['provider']['contact']['address']['country'][lang]
    d['ows_contactelectronicmailaddress'] = \
        c['provider']['contact']['address']['email']

    d['ows_contactvoicetelephone'] = c['provider']['contact']['phone']['voice']
    d['ows_contactfacsimiletelephone'] = \
        c['provider']['contact']['phone']['fax']

    d['ows_contactinstructions'] = \
        c['provider']['contact']['instructions'][lang]

    d['ows_hoursofservice'] = c['provider']['contact']['hours'][lang]

    d['wms_enable_request'] = '*'
    d['wms_getfeatureinfo_formatlist'] = \
        'text/plain,application/json,application/vnd.ogc.gml'
    d['wms_attribution_onlineresource'] = c['attribution']['url'][lang]
    d['wms_attribution_title'] = c['attribution']['title'][lang]
    d['wms_attribution_logourl_format'] = c['provider']['logo']['format']
    d['wms_attribution_logourl_width'] = c['provider']['logo']['width']
    d['wms_attribution_logourl_height'] = c['provider']['logo']['height']
    d['wms_attribution_logourl_href'] = c['provider']['logo']['href']

    d['wcs_enable_request'] = '*'
    d['wcs_label'] = service_title
    d['wcs_description'] = c['identification']['abstract'][lang]
    d['ows_keywordlist'] = ','.join(c['identification']['keywords'][lang])

    return d

def gen_layer(layer_name, layer_info, lang):
    """
    mapfile layer object generator
    :param layer_name: name of layer
    :param layer_info: layer information
    :param lang: language (en or fr)
    :returns: list of mappyfile layer objects of layer
    """

    layers = []

    LOGGER.debug('Setting up layer configuration')

    layer_tileindex = {
        '__type__': 'layer'
    }

    layer = {
        '__type__': 'layer',
        'classes': []
    }

    # for time-enabled layers
    if layer_info['time_enabled'] in ['yes', 'future']:
        # build tileindex LAYER object
        layer_tileindex_name = '{}_idx'.format(layer_name)

        layer_tileindex['type'] = 'POLYGON'
        layer_tileindex['name'] = layer_tileindex_name
        layer_tileindex['status'] = 'OFF'
        layer_tileindex['CONNECTIONTYPE'] = 'OGR'

        layer_tileindex['CONNECTION'] = 'http://geomet-dev-03.cmc.ec.gc.ca/elasticsearch/'
        layer_tileindex['metadata'] = {
            '__type__': 'metadata',
            'ows_enable_request': '!*'
        }

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

        layer['status'] = 'ON'
        layer['tileindex'] = layer_tileindex_name
        layer['tileitem'] = 'properties.filepath'

    # set layer projection
    with open(os.path.join(THISDIR, 'resources', layer_info['forecast_model']['projection'])) as f:
        layer['projection'] = " ".join([line.replace("\n", "").strip('"') for line in f.readlines()])

    # set layer processing directives
    if 'processing' in layer_info['forecast_model']:
        layer['processing'] = layer_info['forecast_model']['processing']

    # set layer classes
    layer['classgroup'] = layer_info['styles'][0].split("/")[-1].strip(".inc")
    layer['classes'] = []
    for style in layer_info['styles']:
        with open(os.path.join(THISDIR, 'resources', style.replace('.inc', '.json'))) as f:
            list_ = ast.literal_eval(f.read())
            for item in list_:
                layer['classes'].append(item)

    # set layer metadata
    # source = yaml config
    yaml_metadata = {
        'ows_extent': layer_info['forecast_model']['extent'],
        'ows_size': f'{layer_info["forecast_model"]["dimensions"][0]} {layer_info["forecast_model"]["dimensions"][1]}',
        'ows_title_en': layer_info['label_en'],
        'ows_title_fr': layer_info['label_fr'],
        'wms_layer_group_en': f'/{layer_info["forecast_model"]["label_fr"]}',
        'wms_layer_group_fr': f'/{layer_info["forecast_model"]["label_en"]}',
        'wcs_label_en': layer_info['label_en'],
        'wcs_label_fr': layer_info['label_fr'],
    }
    # source = mcf
    if layer_info['forecast_model']['mcf'].endswith('.mcf'):
        mcf = SafeConfigParser()
    # generic metadata
    generic_metadata = {
        'ows_authority': 'msc',
        'ows_authorityurl_href': 'https://dd.weather.gc.ca',
        'ows_identifier_value': 'msc',
        'ows_geomtype': 'Geometry',
        'wcs_rangeset_name': 'Default Range',
        'wcs_rangeset_label': 'Default Range',
    }




    layers.append(layer)

    return layers

# @click.group()
# def mapfile():
#     pass
#
#
# @click.command()
# @click.pass_context
# @click.option('--language', '-l', 'lang', type=click.Choice(['en', 'fr']),
#               help='language')
# @click.option('--service', '-s', type=click.Choice(['WMS', 'WCS']),
#               help='service')
# @click.option('--layer', '-lyr', help='layer')


with open(MAPFILE_BASE) as fh:
    mapfile = json.load(fh, object_pairs_hook=OrderedDict)
    symbols_file = os.path.join(THISDIR, 'resources/mapserv/symbols.json')
    with open(symbols_file) as fh2:
        mapfile['symbols'] = json.load(fh2)

with open('/local/drive1/cmdd/afssepe/repos/geomet3-mapfile/geomet.yml') as fh:
    cfg = yaml.load(fh, Loader=Loader)


a = gen_layer('GDPS.ETA_TT', cfg['layers']['GDPS.ETA_TT'], 'en')

print(mappyfile.dumps(a, indent=4))
