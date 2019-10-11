import json
import os
from pathlib import Path
from lark.exceptions import UnexpectedToken

import click
import mappyfile


def convert_style_to_json(file):
    with open(file, 'r') as f:
        file = f.readlines()
        for index, line in enumerate(file):
            if "CLASS\n" in line:
                start_position = index
                break
        return json.dumps(mappyfile.loads("".join(file[start_position:])), indent=4)