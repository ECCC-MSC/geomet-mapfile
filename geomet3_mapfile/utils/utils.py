import json

import click
import mappyfile


def clean_style(file, output_format='json'):
    with open(file, 'r') as f:
        file_ = f.readlines()
        start_postition = None
        for index, line in enumerate(file_):
            if "CLASS\n" in line:
                start_postition = index
                if start_postition > 1:
                    print(file)
                break
        if output_format == 'json':
            return json.dumps(mappyfile.loads("".join(file_[start_postition:])), indent=4)
        elif output_format == 'mapfile':
            return "".join(file_[start_postition:])
