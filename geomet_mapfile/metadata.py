###############################################################################
#
# Copyright (C) 2021 Louis-Philippe Rousseau-Lambert
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
import shutil
import zipfile

import click
from urllib.request import urlopen

from geomet_mapfile.env import BASEDIR, MCF_METADATA

LOGGER = logging.getLogger(__name__)


def fetch_mcf():
    """
    Fetch all MCF from specified tags from discovery-metadata.
    :returns: `bool` of update result
    """

    mcf_dir = '{}/geomet_mapfile/resources/mcf'.format(BASEDIR)

    if os.path.isdir(mcf_dir):
        shutil.rmtree(mcf_dir)

    os.makedirs(mcf_dir)
    FH = io.BytesIO(urlopen(MCF_METADATA).read())
    with zipfile.ZipFile(FH) as z:
        z.extractall(mcf_dir)

    tag_path = os.listdir(mcf_dir)
    tag_folder = '{}/{}'.format(mcf_dir, tag_path[0])
    new_folder = '{}/{}'.format(mcf_dir, 'discovery-metadata')

    os.rename(tag_folder, new_folder)

    return True


@click.group()
def metadata():
    """Add the metadata (MCFs)"""
    pass


@click.command()
@click.pass_context
@click.option('--group', '-g', help='group')
def setup(ctx, group=None):
    """create store"""

    click.echo('Fetching metadata from {}'.format(MCF_METADATA))
    fetch_mcf()
    click.echo('Done')


metadata.add_command(setup)
