#! /usr/bin/env python

# Change the #! line occurring in Python scripts.  The new interpreter
# pathname must be given with a -i option.
#
# Command line arguments are files or directories to be processed.
# Directories are searched recursively for files whose name looks
# like a python module.
# Symbolic links are always ignored (except as explicit directory
# arguments).  Of course, the original file is kept as a back-up
# (with a "~" attached to its name).
#
# Undoubtedly you can do this using find and sed or perl, but this is
# a nice example of Python code that recurses down a directory tree
# and uses regular expressions.  Also note several subtleties like
# preserving the file's mode and avoiding to even write a temp file
# when no changes are needed for a file.
#
# NB: by changing only the function fixfile() you can turn this
# into a program for a different change to Python programs...

import sys
import re
import os
import getopt

def main():
    usage = ('usage: %s -i /interpreter file-or-directory ...\n' %
             sys.argv[0])
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:')
    except getopt.error as msg:
        sys.stderr.write(msg + '\n')
        sys.stderr.write(usage)
        sys.exit(2)
    for o, a in opts:
        if o == '-i':
            new_interpreter = a
    if not new_interpreter or new_interpreter[0] != '/' or not args:
        sys.stderr.write('-i option or file-or-directory missing\n')
        sys.stderr.write(usage)
        sys.exit(2)
    bad = 0
    for arg in args:
        if os.path.isdir(arg):
            if recursedown(arg): bad = 1
        elif os.path.islink(arg):
            sys.stderr.write(arg + ': will not process symbolic links\n')
            bad = 1
        else:
            if fix(arg): bad = 1
    sys.exit(bad)

ispythonprog = re.compile('^[a-zA-Z0-9_]+\.py$')
def ispython(name):
    return ispythonprog.match(name) >= 0

def recursedown(dirname):
    sys.stderr.write('recursedown(' + str(dirname) + ')\n')
    bad = 0
    try:
        names = os.listdir(dirname)
    except OSError as msg:
        sys.stderr.write(dirname + ': cannot list directory: ' + str(msg) + '\n')
        return 1
    names.sort()
    subdirs = []
    for name in names:
        if name in (os.curdir, os.pardir): continue
        fullname = os.path.join(dirname, name)
        if os.path.islink(fullname): pass
        elif os.path.isdir(fullname):
            subdirs.append(fullname)
        elif ispython(name):
            if fix(fullname): bad = 1
    for fullname in subdirs:
        if recursedown(fullname): bad = 1
    return bad

def fix(filename):
    try:
        f = open(filename, 'r')
    except OSError as msg:
        sys.stderr.write(filename + ': cannot open: ' + str(msg) + '\n')
        return 1
    line = f.readline()
    fixed = fixline(line)
    if line == fixed:
        sys.stdout.write(filename+': no change\n')
        f.close()
        return
    head, tail = os.path.split(filename)
    tempname = os.path.join(head, '@' + tail)
    try:
        g = open(tempname, 'w')
    except OSError as msg:
        f.close()
        sys.stderr.write(tempname+': cannot create: '+str(msg)+'\n')
        return 1
    sys.stdout.write(filename + ': updating\n')
    g.write(fixed)
    BUFSIZE = 8*1024
    while 1:
        buf = f.read(BUFSIZE)
        if not buf: break
        g.write(buf)
    g.close()
    f.close()

    # Finishing touch -- move files

    # First copy the file's mode to the temp file
    try:
        statbuf = os.stat(filename)
        os.chmod(tempname, statbuf.st_mode & 07777)
    except OSError as msg:
        sys.stderr.write(tempname + ': warning: chmod failed (' + str(msg) + ')\n')
    # Then make a backup of the original file as filename~
    try:
        os.rename(filename, filename + '~')
    except OSError as msg:
        sys.stderr.write(filename + ': warning: backup failed (' + str(msg) + ')\n')
    # Now move the temp file to the original file
    try:
        os.rename(tempname, filename)
    except OSError as msg:
        sys.stderr.write(filename + ': rename failed (' + str(msg) + ')\n')
        return 1
    # Return succes
    return 0

def fixline(line):
    if line[:2] != '#!':
        return line
    if line.find("python") < 0:
        return line
    return '#! %s\n' % new_interpreter

main()