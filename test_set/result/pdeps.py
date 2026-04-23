#!/usr/bin/env python3

# pdeps
#
# Find dependencies between a bunch of Python modules.
#
# Usage:
#	pdeps file1.py file2.py ...
#
# Output:
# Four tables separated by lines like '--- Closure ---':
# 1) Direct dependencies, listing which module imports which other modules
# 2) The inverse of (1)
# 3) Indirect dependencies, or the closure of the above
# 4) The inverse of (3)
#
# To do:
# - command line options to select output type
# - option to automatically scan the Python library for referenced modules
# - option to limit output to particular modules

import sys
import os
import string

# Compiled regular expressions to search for import statements
m_import = r'^\s*from\s+\S+\s*\('
m_from = r'^\s*import\s+\S+\s*\('

# Main program
def main():
    args = sys.argv[1:]
    if not args:
        print('usage: pdeps file.py file.py ...')
        return 1

    table = {}
    for arg in args:
        process(arg, table)

    print('--- Uses ---')
    print_results(table)

    print('--- Used By ---')
    inv = inverse(table)
    print_results(inv)

    print('--- Closure of Uses ---')
    reach = closure(table)
    print_results(reach)

    print('--- Closure of Used By ---')
    invreach = inverse(reach)
    print_results(invreach)

    return 0


# Collect data from one file
def process(filename, table):
    fp = open(filename, 'r')
    mod = os.path.basename(filename)
    if mod.endswith('.py'):
        mod = mod[:-3]
    table[mod] = []
    while True:
        line = fp.readline()
        if not line:
            break
        while line.endswith('\\'):
            nextline = fp.readline()
            if not nextline:
                break
            line = line[:-1] + nextline
        if m_import.match(line):
            (a, b), (a1, b1) = m_import.regs[:2]
        elif m_from.match(line):
            (a, b), (a1, b1) = m_from.regs[:2]
        else:
            continue
        words = string.splitfields(line[a1:b1], ',')
        for word in words:
            word = string.strip(word)
            if word not in table[mod]:
                table[mod].append(word)


# Compute closure (this is in fact totally general)
def closure(table):
    modules = table.keys()
    reach = {}
    for mod in modules:
        reach[mod] = table[mod][:]
    return reach


# Invert a table (this is again totally general).
# All keys of the original table are made keys of the inverse,
# so there may be empty lists in the inverse.
def inverse(table):
    inv = {}
    for key in table.keys():
        if key not in inv:
            inv[key] = []
        for item in table[key]:
            store(inv, item, key)
    return inv


# Store "item" in "dict" under "key".
# The dictionary maps keys to lists of items.
# If there is no list for the key yet, it is created.
def store(dict, key, item):
    if key in dict:
        dict[key].append(item)
    else:
        dict[key] = [item]


# Tabulate results neatly
def print_results(table):
    modules = table.keys()
    maxlen = max(len(mod) for mod in modules)
    modules.sort()
    for mod in modules:
        list = table[mod]
        list.sort()
        print(f'{mod:>{maxlen}}:', end='')
        if mod in list:
            print('(*)', end='')
        for ref in list:
            print(ref, end='')
        print()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)