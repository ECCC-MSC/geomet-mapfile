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

import io
import logging
import os
import re
from urllib.request import urlopen

import click
import mapscript

from geomet_data_registry.tileindex.base import TileNotFoundError
from geomet_mapfile.env import (
    BASEDIR,
    TILEINDEX_URL,
    TILEINDEX_TYPE,
    TILEINDEX_NAME,
    MAPFILE_STORAGE,
    STORE_TYPE,
    STORE_URL,
    ALLOW_LAYER_DATA_DOWNLOAD
)
from geomet_mapfile.plugin import load_plugin

LOGGER = logging.getLogger(__name__)

TILEINDEX_PROVIDER_DEF = {
    'type': TILEINDEX_TYPE,
    'url': TILEINDEX_URL,
    'name': TILEINDEX_NAME,
    'group': None,
}

# List of all environment variable used by MapServer
MAPSERV_ENV = [
    'CONTENT_LENGTH',
    'CONTENT_TYPE',
    'CURL_CA_BUNDLE',
    'HTTP_COOKIE',
    'HTTP_HOST',
    'HTTPS',
    'HTTP_X_FORWARDED_HOST',
    'HTTP_X_FORWARDED_PORT',
    'HTTP_X_FORWARDED_PROTO',
    'MS_DEBUGLEVEL',
    'MS_ENCRYPTION_KEY',
    'MS_ERRORFILE',
    'MS_MAPFILE',
    'MS_MAPFILE_PATTERN',
    'MS_MAP_NO_PATH',
    'MS_MAP_PATTERN',
    'MS_MODE',
    'MS_OPENLAYERS_JS_URL',
    'MS_TEMPPATH',
    'MS_XMLMAPFILE_XSLT',
    'PROJ_LIB',
    'QUERY_STRING',
    'REMOTE_ADDR',
    'REQUEST_METHOD',
    'SCRIPT_NAME',
    'SERVER_NAME',
    'SERVER_PORT',
]

WCS_FORMATS = {'image/tiff': 'tif', 'image/netcdf': 'nc'}

SERVICE_EXCEPTION = '''<?xml version='1.0' encoding="UTF-8" standalone="no"?>
<ServiceExceptionReport version="1.3.0" xmlns="http://www.opengis.net/ogc"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/ogc
    http://schemas.opengis.net/wms/1.3.0/exceptions_1_3_0.xsd">
  <ServiceException>{}</ServiceException>
</ServiceExceptionReport>'''


def metadata_lang(m, layers, lang):
    """
    function to update the mapfile MAP metadata
    keys in function of the lang of the request

    :param m: mapfile object to update language
    :param layers: `list` of layer names in mapfile
    :param lang: lang of the request

    :returns: `bool` of language update status
    """
    map_fields_to_update = [
        'ows_abstract',
        'ows_address',
        'ows_city',
        'ows_contactinstructions',
        'ows_contactperson',
        'ows_contactorganization',
        'ows_contactposition',
        'ows_country',
        'ows_hoursofservice',
        'ows_keywordlist',
        'ows_keywordlist_http://purl.org/dc/terms/_items',
        'ows_onlineresource',
        'ows_service_onlineresource',
        'ows_stateorprovince',
        'ows_title',
        'wcs_description',
        'wcs_label',
        'wms_attribution_title',
        'wms_attribution_onlineresource',
    ]

    for field in map_fields_to_update:
        m.setMetaData(field, m.getMetaData(f'{field}_{lang}'))

    layer_fields_to_update = [
        'ows_title',
        'wms_layer_group',
        'ows_abstract',
        'wcs_label',
        'ows_keywordlist',
    ]

    for layer in layers:
        for field in layer_fields_to_update:
            layerobj = m.getLayerByName(layer)
            layerobj.setMetaData(
                field, layerobj.getMetaData(f'{field}_{lang}')
            )

    return True


def get_data_path(layer, fh, mr):
    """
    function to find the datapath
    based on either the layer metadata
    or on the WMS time parameters from the user

    :param mr: TODO
    :param fh: TODO

    :returns: filepath
    """

    model_run = re.sub("[^0-9]", "", mr)
    forecast = re.sub("[^0-9]", "", fh)

    if model_run not in [None, '']:
        id_ = '{}-{}-{}'.format(layer, model_run, forecast)
    else:
        id_ = '{}-{}'.format(layer, forecast)

    ti = load_plugin('tileindex', TILEINDEX_PROVIDER_DEF)

    try:
        res = ti.get(id_)

        filepath = res['properties']['filepath']
        url = res['properties']['url']

        res_arr = [filepath, url]
    except TileNotFoundError as err:
        LOGGER.debug(err)
        raise TileNotFoundError(err)

    return res_arr


def application(env, start_response):
    """WSGI application for WMS/WCS"""

    for key in MAPSERV_ENV:
        if key in env:
            os.environ[key] = env[key]
        else:
            os.unsetenv(key)

    layer = None
    mapfile_ = None

    request = mapscript.OWSRequest()
    request.loadParams()

    lang_ = request.getValueByName('LANG')
    service_ = request.getValueByName('SERVICE')
    request_ = request.getValueByName('REQUEST')
    layers_ = request.getValueByName('LAYERS')
    layer_ = request.getValueByName('LAYER')
    coverageid_ = request.getValueByName('COVERAGEID')

    if lang_ is not None and lang_ in ['f', 'fr', 'fra']:
        lang = 'fr'
    else:
        lang = 'en'
    if layers_ is not None:
        layer = layers_
    elif layer_ is not None:
        layer = layer_
    elif coverageid_ is not None:
        layer = coverageid_
    else:
        layer = None
    if service_ is None:
        service_ = 'WMS'

    if layer is not None and len(layer) == 0:
        layer = None

    time_error = None

    LOGGER.debug('service: {}'.format(service_))
    LOGGER.debug('language: {}'.format(lang))

    if layer == 'GODS':
        banner = os.path.join(BASEDIR, 'geomet_mapfile/resources',
                              'other/banner.txt')
        with open(banner) as fh:
            start_response('200 OK', [('Content-Type', 'text/plain')])
            msg = fh.read()
            return ['{}'.format(msg).encode()]

    # fetch mapfile from store or from disk
    if MAPFILE_STORAGE == 'file':
        # if a single layer is specified in LAYER param fetch mapfile from disk
        if layer is not None and ',' not in layer:
            mapfile_ = '{}/mapfile/geomet-weather-{}.map'.format(
                BASEDIR, layer
            )
        # if mapfile_ is None or its path does not exist
        if mapfile_ is None or not os.path.exists(mapfile_):
            mapfile_ = '{}/mapfile/geomet-weather.map'.format(BASEDIR)
        # if mapfile_ path does not exist set mapfile_ to None
        if not os.path.exists(mapfile_):
            mapfile_ = None
    elif MAPFILE_STORAGE == 'store':
        st = load_plugin('store', {'type': STORE_TYPE, 'url': STORE_URL})
        if layer is not None and ',' not in layer:
            mapfile_ = st.get_key('{}_mapfile'.format(layer))
        if mapfile_ is None:
            mapfile_ = st.get_key('geomet-weather_mapfile')

    # if no mapfile at all is found return a Unsupported service exception
    if not mapfile_:
        start_response(
            '400 Bad Request', [('Content-Type', 'application/xml')]
        )
        msg = 'Unsupported service'
        return [SERVICE_EXCEPTION.format(msg).encode()]

    # if requesting GetCapabilities for entire service, return cache
    if request_ == 'GetCapabilities' and layer is None:
        LOGGER.debug('Requesting global mapfile')
        if service_ == 'WMS':
            filename = 'geomet-weather-1.3.0-capabilities-{}.xml'.format(lang)
            cached_caps = os.path.join(BASEDIR, 'mapfile', filename)

        if os.path.isfile(cached_caps):
            start_response('200 OK', [('Content-Type', 'application/xml')])
            with io.open(cached_caps, 'rb') as fh:
                return [fh.read()]
    else:
        LOGGER.debug('Requesting layer mapfile')
        if os.path.exists(mapfile_):
            # read mapfile from filepath
            LOGGER.debug('Loading mapfile {} from disk'.format(mapfile_))
            mapfile = mapscript.mapObj(mapfile_)
        else:
            # read mapfile from string returned from store
            LOGGER.debug(
                'Loading {}_mapfile from store'.format(
                    layer if layer else 'geomet-mapfile'
                )
            )
            mapfile = mapscript.fromstring(mapfile_)

        layerobj = mapfile.getLayerByName(layer)
        time = request.getValueByName('TIME')
        ref_time = request.getValueByName('DIM_REFERENCE_TIME')

        if any(time_param == '' for time_param in [time, ref_time]):
            time_error = "Valeur manquante pour la date ou l'heure / Missing value for date or time"  # noqa
            start_response('200 OK', [('Content-type', 'text/xml')])
            return [SERVICE_EXCEPTION.format(time_error).encode()]

        if time is None:
            time = layerobj.getMetaData('wms_timedefault')
        if ref_time is None:
            ref_time = layerobj.getMetaData('wms_reference_time_default')

        try:
            filepath, url = get_data_path(layer, time, ref_time)
        except TileNotFoundError as err:
            LOGGER.error(err)
            time_error = 'NoMatch: Date et heure invalides / Invalid date and time'  # noqa
            start_response('200 OK', [('Content-type', 'text/xml')])
            return [SERVICE_EXCEPTION.format(time_error).encode()]

        try:
            if request_ in ['GetMap', 'GetFeatureInfo']:
                if all([filepath.startswith(os.sep),
                        not os.path.isfile(filepath)]):
                    LOGGER.debug('File is not on disk: {}'.format(filepath))
                    if not ALLOW_LAYER_DATA_DOWNLOAD:
                        LOGGER.error('layer data downloading not allowed')
                        _error = 'data not found'
                        start_response('500 Internal Server Error',
                                       [('Content-type', 'text/xml')])
                        return [SERVICE_EXCEPTION.format(_error).encode()]

                    if not os.path.exists(os.path.dirname(filepath)):
                        LOGGER.debug('Creating the filepath')
                        os.makedirs(os.path.dirname(filepath))
                    LOGGER.debug('Downloading url: {}'.format(url))
                    with urlopen(url) as r:
                        with open(filepath, 'wb') as fh:
                            fh.write(r.read())

            layerobj.data = filepath

        except ValueError as err:
            LOGGER.error(err)
            _error = 'NoApplicableCode: Donnée non disponible / Data not available'  # noqa
            start_response('500 Internal Server Error',
                           [('Content-type', 'text/xml')])
            return [SERVICE_EXCEPTION.format(_error).encode()]

        if request_ == 'GetCapabilities' and lang == 'fr':
            metadata_lang(mapfile, layer.split(','), lang)

    mapscript.msIO_installStdoutToBuffer()

    # giving we don't use properly use tileindex due to performance issues
    # we need to remove the time parameter from the request for uvraster layer
    if 'time' in env['QUERY_STRING'].lower():
        query_string = env['QUERY_STRING'].split('&')
        query_string = [x for x in query_string if 'time' not in x.lower()]
        request.loadParamsFromURL('&'.join(query_string))
    else:
        request.loadParamsFromURL(env['QUERY_STRING'])

    try:
        LOGGER.debug('Dispatching OWS request')
        mapfile.OWSDispatch(request)
    except (mapscript.MapServerError, IOError) as err:
        # let error propagate to service exception
        LOGGER.error(err)
        pass

    headers = mapscript.msIO_getAndStripStdoutBufferMimeHeaders()

    headers_ = [
        ('Content-Type', headers['Content-Type']),
    ]

    content = mapscript.msIO_getStdoutBufferBytes()

    start_response('200 OK', headers_)

    return [content]


@click.command()
@click.pass_context
@click.option('--port', '-p', type=int, help='port', default=8099)
def serve(ctx, port):
    """Serve for development"""

    from wsgiref.simple_server import make_server

    httpd = make_server('', port, application)
    click.echo('Serving on port {}'.format(port))
    httpd.serve_forever()
