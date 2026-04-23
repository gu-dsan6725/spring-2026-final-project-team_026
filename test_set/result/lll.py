#!/usr/bin/env python

# Find symbolic links and show where they point to.
# Arguments are directories to search; default is current directory.
# No recursion.
# (This is a totally different program from "findsymlinks.py"!)

import sys
import os

def lll(dirname):
    """List symbolic links in the given directory."""
    for name in os.listdir(dirname):
        if name not in ('.', '..'):
            full = os.path.join(dirname, name)
            if os.path.islink(full):
                try:
                    print(f"{name} -> {os.readlink(full)}")
                except OSError as e:
                    print(f"Error reading link {name}: {e}")

args = sys.argv[1:]
if not args:
    args = ['.']
first = 1
for arg in args:
    if len(args) > 1:
        if not first:
            print()
        first = 0
        print(arg + ':')
    lll(arg)