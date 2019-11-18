import os
from pathlib import Path

import click
from lark.exceptions import UnexpectedToken
from geomet3_mapfile.utils.utils import clean_style


@click.group()
def utils():
    """geomet3-mapfile utility functions"""
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
        raise click.ClickException('Missing --file/-f, --directory/-d option, -output_dir/-o option')

    files_to_process = []

    if file_ is not None:
        files_to_process = [file_]
    elif directory is not None:
        for root, dirs, files in os.walk(directory):
            for f in [f for f in files if any([f.endswith('.inc'), f.endswith('.map')])]:
                files_to_process.append(os.path.join(root, f))

    converted_files = []
    for file_to_process in files_to_process:
        try:
            converted_files.append(
            (file_to_process,
            clean_style(file_to_process, output_format=output_format)))
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
