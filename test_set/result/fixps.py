#!/usr/bin/env python3

import sys
import re
import argparse
import pathlib

def main():
    parser = argparse.ArgumentParser(description='Fix Python script(s) to reference the interpreter via /usr/bin/env python.')
    parser.add_argument('files', nargs='+', help='List of files to fix')
    args = parser.parse_args()

    for file in args.files:
        try:
            with open(file, 'r') as f:
                content = f.read()
        except OSError as e:
            print(f"Error opening file {file}: {e}")
            continue

        if not re.match('^#! */usr/bin/python', content):
            print(f"{file}: not a /usr/bin/python script")
            continue

        new_content = re.sub('/usr/bin/python', '/usr/bin/env python', content)
        try:
            with open(file, "w") as f:
                f.write(new_content)
        except OSError as e:
            print(f"Error writing to file {file}: {e}")

if __name__ == "__main__":
    main()