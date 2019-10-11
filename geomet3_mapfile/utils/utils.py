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