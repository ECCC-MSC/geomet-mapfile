__version__ = '0.0.dev0'

import click

# from mapfile import mapfile
from geomet3_mapfile.utils import utils
from geomet3_mapfile.mapfile import generate_mapfile
from geomet3_mapfile.store import store
from geomet3_mapfile.wsgi import serve


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


# cli.add_command(mapfile)
cli.add_command(utils)
cli.add_command(generate_mapfile)
cli.add_command(store)
cli.add_command(serve)
