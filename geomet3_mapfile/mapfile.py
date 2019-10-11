from collections import OrderedDict
from datetime import datetime
import io
import json
import logging
import os
from pprint import pprint as pp

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
#
# with io.open(MAPFILE_BASE) as fh:
#     mapfile = json.load(fh, object_pairs_hook=OrderedDict)
#     symbols_file = os.path.join(THISDIR, 'resources/mapserv/symbols.json')
#     with io.open(symbols_file) as fh2:
#         mapfile['symbols'] = json.load(fh2)
#
# with io.open('/local/drive1/cmdd/afssepe/repos/geomet3-mapfile/geomet.yml') as fh:
#     cfg = yaml.load(fh, Loader=Loader)

