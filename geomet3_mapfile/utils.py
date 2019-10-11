import json
import os
from pathlib import Path
from lark.exceptions import UnexpectedToken

import click
import mappyfile


def convert_style_to_json(file):
    with open(file, 'r') as f:
        file = f.readlines()
        start_postition = None
        for index, line in enumerate(file):
            if "CLASS\n" in line:
                start_postition = index
                break
        return json.dumps(mappyfile.loads("".join(file[start_postition:])), indent=4)
@click.group()
def utils():
    pass

@click.command()
@click.pass_context
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
def convert(ctx, file_, directory, output_directory):
    """convert mapfile to mappyfile dictionnary object"""

    if all([file_ is None, directory is None]):
        raise click.ClickException('Missing --file/-f or --dir/-d option')

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
            converted_files.append((file_to_process, convert_style_to_json(file_to_process)))
        except UnexpectedToken:
            click.echo(f'Could not convert {file_to_process}!')
            pass

    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    for file, converted_file in converted_files:
        output_file_name = f'{Path(file).name.split(".")[0]}.json'
        with open(os.path.join(output_directory, output_file_name), 'w') as f:
            f.write(converted_file)


if __name__ == '__main__':
    convert()
