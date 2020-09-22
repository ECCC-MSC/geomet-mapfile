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

import json
import logging
import os
from pathlib import Path

import click
from lark.exceptions import UnexpectedToken
import mappyfile

DATEFORMAT = '%Y-%m-%dT%H:%M:%SZ'

LOGGER = logging.getLogger(__name__)


def str2bool(value):
    """
    helper function to return Python boolean
    type (source: https://stackoverflow.com/a/715468)
    :param value: value to be evaluated
    :returns: `bool` of whether the value is boolean-ish
    """

    value2 = False

    if isinstance(value, bool):
        value2 = value
    else:
        value2 = value.lower() in ('yes', 'true', 't', '1', 'on')

    return value2


def remove_prefix(text, prefix):
    """
    Utility function to remove a given prefix from a string if is present

    :param text: `str` to parse
    :param prefix: `str` to remove from text

    :returns: `str` of text without prefix, or text if no prefix found
    """
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def clean_style(filepath, output_format='json'):
    # TODO: docstring
    with open(filepath, 'r') as f:
        file_ = f.readlines()
        start_position = None
        for index, line in enumerate(file_):
            if 'CLASS\n' in line:
                start_position = index
                if start_position > 1:
                    LOGGER.debug(filepath)
                break
        if output_format == 'json':
            content = ''.join(file_[start_position:])
            data = json.dumps(mappyfile.loads(content), indent=4)
        elif output_format == 'mapfile':
            data = ''.join(file_[start_position:])

        return data


@click.group()
def utils():
    """Utility functions"""
    pass


@click.command()
@click.option('--file', '-f', 'file_',
              type=click.Path(exists=True, resolve_path=True),
              help='Path to file')
@click.option('--directory', '-d', 'directory',
              type=click.Path(exists=True, resolve_path=True,
                              dir_okay=True, file_okay=False),
              help='Path to directory')
@click.option('--output_dir', '-o', 'output_directory',
              type=click.Path(exists=False, resolve_path=True,
                              dir_okay=True, file_okay=False),
              help='Path to output directory')
@click.option('--output_format', '-of', 'output_format',
              type=click.Choice(['json', 'mapfile'], case_sensitive=False),
              help='Output format')
def clean_styles(file_, directory, output_directory, output_format):
    """
    Cleans existing GeoMet-Weather styles and writes
    back out to mapfile or to mappyfile dictionnary object
    """

    if all([file_ is None, directory is None]):
        msg = 'Missing --file/-f, --directory/-d option, -output_dir/-o option'
        raise click.ClickException(msg)

    files_to_process = []

    if file_ is not None:
        files_to_process = [file_]
    elif directory is not None:
        for root, dirs, files in os.walk(directory):
            for f in [f for f in files if f.endswith(('.inc', '.map'))]:
                files_to_process.append(os.path.join(root, f))

    converted_files = []
    for file_to_process in files_to_process:
        try:
            converted_files.append((file_to_process,
                                    clean_style(file_to_process,
                                                output_format=output_format)))
        except UnexpectedToken:
            click.echo(f'Could not convert {file_to_process}!')
            pass

    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    if output_format == 'json':
        output_extension = '.json'

    elif output_format == 'mapfile':
        output_extension = '.inc'

    for file, converted_file in converted_files:
        output_file_name = f'{Path(file).name.split(".")[0]}{output_extension}'
        with open(os.path.join(output_directory, output_file_name), 'w') as f:
            f.write(converted_file)


utils.add_command(clean_styles)
