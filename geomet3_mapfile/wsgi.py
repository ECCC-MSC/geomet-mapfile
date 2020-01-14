###############################################################################
#
# Copyright (C) 2019 Louis-Philippe Rousseau-Lambert
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
import sys

import click
from elasticsearch import Elasticsearch

sys.path.append('/data/geomet/dev/src/mapserver/mapserver/build/mapscript/python')
# import mapscript

from geomet3_mapfile.env import BASEDIR, TILEINDEX_URL

LOGGER = logging.getLogger(__name__)

# List of all environment variable used by MapServer
MAPSERV_ENV = [
  'CONTENT_LENGTH', 'CONTENT_TYPE', 'CURL_CA_BUNDLE', 'HTTP_COOKIE',
  'HTTP_HOST', 'HTTPS', 'HTTP_X_FORWARDED_HOST', 'HTTP_X_FORWARDED_PORT',
  'HTTP_X_FORWARDED_PROTO', 'MS_DEBUGLEVEL', 'MS_ENCRYPTION_KEY',
  'MS_ERRORFILE', 'MS_MAPFILE', 'MS_MAPFILE_PATTERN', 'MS_MAP_NO_PATH',
  'MS_MAP_PATTERN', 'MS_MODE', 'MS_OPENLAYERS_JS_URL', 'MS_TEMPPATH',
  'MS_XMLMAPFILE_XSLT', 'PROJ_LIB', 'QUERY_STRING', 'REMOTE_ADDR',
  'REQUEST_METHOD', 'SCRIPT_NAME', 'SERVER_NAME', 'SERVER_PORT'
]

WCS_FORMATS = {
    'image/tiff': 'tif',
    'image/netcdf': 'nc'
}

SERVICE_EXCEPTION = '''<?xml version='1.0' encoding="UTF-8" standalone="no"?>
<ServiceExceptionReport version="1.3.0" xmlns="http://www.opengis.net/ogc"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/ogc
    http://schemas.opengis.net/wms/1.3.0/exceptions_1_3_0.xsd">
  <ServiceException>{}</ServiceException>
</ServiceExceptionReport>'''

def metadata_lang(m, l):
    """
    function to update the mapfile MAP metadata
    keys in function of the lang of the request

    :param m: mapfile object to update language
    :param l: lang of the request
    """

    #TODO

def insert_data(layer, fh, mr):
    """
    fucntion to find the datapath
    based on either the layer metadata
    or on the WMS time parameters from the user

    :param mr: 
    "param fh:

    :return filepath 
    """

    model_run = re.sub("[^0-9]", "", mr)
    forecast = re.sub("[^0-9]", "", fh)

    if model_run not in [None, '']:    
        id_ = '{}-{}-{}'.format(layer, model_run, forecast)
    else:
        id_ = '{}-{}'.format(layer, forecast)

    es = Elasticsearch()
    
    res = es.get(index=TILEINDEX_URL.split('/')[-2], id=id_)
    
    return res['_source']['properties']['filepath']

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
    format_ = request.getValueByName('FORMAT')

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

    if layer is not None and ',' not in layer:
        mapfile_ = '{}/mapfile/geomet-weather-{}.map'.format(
            BASEDIR, layer)
    if mapfile_ is None or not os.path.exists(mapfile_):
       mapfile_ = '{}/mapfile/geomet-weather.map'.format(
            BASEDIR)
    if not os.path.exists(mapfile_):
        start_response('400 Bad Request',
                       [('Content-Type', 'application/xml')])
        msg = 'Unsupported service'
        return [SERVICE_EXCEPTION.format(msg)]

    # if requesting GetCapabilities for entire service, return cache
    if request_ == 'GetCapabilities' and layer is None:
        if service_ == 'WMS':
            filename = 'geomet-weather-1.3.0-capabilities.xml'.format(
                lang)
            cached_caps = os.path.join(BASEDIR, 'mapfile', filename)

        if os.path.isfile(cached_caps):
            start_response('200 OK', [('Content-Type', 'application/xml')])
            with io.open(cached_caps, 'rb') as fh:
                return [fh.read()]
    else:
        LOGGER.debug('Loading mapfile: {}'.format(mapfile_))
        mapfile = mapscript.mapObj(mapfile_)
        layerobj = mapfile.getLayerByName(layer)

        time = request.getValueByName('TIME')
        ref_time = request.getValueByName('DIM_REFERENCE_TIME')

        if time is None:
           time = layerobj.getMetaData('wms_timedefault') 
        if ref_time is None:
            ref_time = layerobj.getMetaData('wms_reference_time_default')
                
        try:
            filepath = insert_data(layer, time, ref_time)
            layerobj.data = filepath

        except ValueError as err:
            time_error = err

        if time_error is not None:
            time_error = 'Date et heure invalides / Invalid date and time'
            response = get_custom_service_exception('NoMatch', 'time', time_error)
            start_response('200 OK', [('Content-type', 'text/xml')])
            return [response]


        #if request_ == 'GetCapabilities' and lang == 'fr':
        #    metadata_lang(mapfile, lang)
        #    layerobj = mapfile.getLayerByName(layer)
        #    layerobj.setMetaData('ows_title',
        #                         layerobj.getMetaData('ows_title_{}'.format(lang))) # noqa
        #    layerobj.setMetaData('ows_layer_group',
        #                         layerobj.getMetaData('ows_layer_group_{}'.format(lang))) # noqa

    mapscript.msIO_installStdoutToBuffer()
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

    # for WCS requests, generate useful filename for response
    #if not headers['Content-Type'].startswith('text/xml'):
    #    if service_ == 'WCS' and request_ == 'GetCoverage':
    #        filename = 'geomet-climate-{}.{}'.format(layer,
    #                                                 WCS_FORMATS[format_])
    #        headers_.append(('Content-Disposition',
    #                         'attachment; filename="{}"'.format(filename)))

    content = mapscript.msIO_getStdoutBufferBytes()

    start_response('200 OK', headers_)

    return [content]


@click.command()
@click.pass_context
@click.option('--port', '-p', type=int, help='port', default=8099)
def serve(ctx, port):
    """Serve geomet-weather via wsgiref, for dev"""

    from wsgiref.simple_server import make_server
    httpd = make_server('', port, application)
    click.echo('Serving on port {}'.format(port))
    httpd.serve_forever()
