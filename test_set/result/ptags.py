#!/usr/bin/env python3

# ptags
#
# Create a tags file for Python programs, usable with vi.
# Tagged are:
# - functions (even inside other defs or classes)
# - classes
# - filenames
# Warns about files it cannot open.
# No warnings about duplicate tags.

import sys
import re
import os

TAGS_FILE = 'tags'
MAX_TAG_LENGTH = 1024

def main():
    args = sys.argv[1:]
    for file in args:
        treat_file(file)
    if tags:
        with open(TAGS_FILE, 'w') as fp:
            tags.sort()
            for s in tags:
                fp.write(s)

def treat_file(file):
    try:
        with open(file, 'r') as fp:
            base = os.path.basename(file)
            if base.endswith('.py'):
                base = base[:-3]
            tags.append(f'{base}\t{file}\t1\n')
            while True:
                line = fp.readline()
                if not line:
                    break
                m = matcher.match(line)
                if m:
                    content = m.group(0)
                    name = m.group(2)
                    tags.append(f'{name}\t{file}\t/^{content}/\n')
    except Exception as e:
        sys.stderr.write(f'Cannot open {file}: {e}\n')

expr = '^[ \t]*(def|class)[ \t]+([a-zA-Z0-9_]+)[ \t]*[:\(]'
matcher = re.compile(expr)

tags = []  # Local variable!

if __name__ == '__main__':
    main()