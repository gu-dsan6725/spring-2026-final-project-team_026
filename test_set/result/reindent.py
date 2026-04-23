#!/usr/bin/env python3

# Released to the public domain, by Tim Peters, 03 October 2000.

"""reindent [-d][-r][-v] path ...

-d  Dry run.  Analyze, but don't make any changes to, files.
-r  Recurse.  Search for all .py files in subdirectories too.
-v  Verbose.  Print informative msgs; else no output.

Change Python (.py) files to use 4-space indents and no hard tab characters.
Also trim excess whitespace from ends of lines, and empty lines at the ends
of files.  Ensure the last line ends with a newline.

Pass one or more file and/or directory paths.  When a directory path, all
.py files within the directory will be examined, and, if the -r option is
given, likewise recursively for subdirectories.

Overwrites files in place, renaming the originals with a .bak extension.
If reindent finds nothing to change, the file is left alone.  If reindent
does change a file, the changed file is a fixed-point for reindent (i.e.,
running reindent on the resulting .py file won't change it again).

The hard part of reindenting is figuring out what to do with comment
lines.  So long as the input files get a clean bill of health from
tabnanny.py, reindent should do a good job.
"""

__version__ = "1"

import tokenize
import os
import sys
import getopt

verbose = 0
recurse = 0
dryrun  = 0

def errprint(*args):
    sep = ""
    for arg in args:
        sys.stderr.write(sep + str(arg))
        sep = " "
    sys.stderr.write("\n")

def main():
    global verbose, recurse, dryrun
    try:
        opts, args = getopt.getopt(sys.argv[1:], "drv")
    except getopt.error as msg:
        errprint(msg)
        return
    for o, a in opts:
        if o == '-d':
            dryrun += 1
        elif o == '-r':
            recurse += 1
        elif o == '-v':
            verbose += 1
    if not args:
        errprint("Usage:", __doc__)
        return
    for arg in args:
        check(arg)

def check(file):
    if os.path.isdir(file) and not os.path.islink(file):
        if verbose:
            print("listing directory", file)
        names = os.listdir(file)
        for name in names:
            fullname = os.path.join(file, name)
            if ((recurse and os.path.isdir(fullname) and
                 not os.path.islink(fullname))
                or name.lower().endswith(".py")):
                check(fullname)
        return

    if verbose:
        print("checking", file, "..."),
    try:
        f = open(file)
    except IOError as msg:
        errprint("%s: I/O Error: %s" % (file, str(msg)))
        return

    r = Reindenter(f)
    f.close()
    if r.run():
        if verbose:
            print("changed.")
            if dryrun:
                print("But this is a dry run, so leaving it alone.")
        if not dryrun:
            bak = file + ".bak"
            if os.path.exists(bak):
                os.remove(bak)
            os.rename(file, bak)
            if verbose:
                print("renamed", file, "to", bak)
            f = open(file, "w")
            r.write(f)
            f.close()
            if verbose:
                print("wrote new", file)
    else:
        if verbose:
            print("unchanged.")

class Reindenter:

    def __init__(self, f):
        self.find_stmt = 1  # next token begins a fresh stmt?
        self.level = 0      # current indent level

        # Raw file lines.
        self.raw = f.readlines()

        # File lines, rstripped & tab-expanded.  Dummy at start is so
        # that we can use tokenize's 1-based line numbering easily.
        # Note that a line is all-blank iff it's "\n".
        self.lines = [line.rstrip().expandtabs() + "\n"
                      for line in self.raw]
        self.lines.insert(0, None)
        self.index = 1  # index into self.lines of next line

        # List of (lineno, indentlevel) pairs, one for each stmt and
        # comment line.  indentlevel is -1 for comment lines, as a
        # signal that tokenize doesn't know what to do about them;
        # indeed, they're our headache!
        self.stats = []

    def run(self):
        tokenize.tokenize(self.getline, self.token_eater)
        # Remove trailing empty lines.
        lines = self.lines
        while lines and lines[-1] == "\n":
            lines.pop()
        # Sentinel.
        stats = self.stats
        stats.append((len(lines), 0))
        # Map count of leading spaces to # we want.
        have2want = {}
        # Program after transformation.
        after = self.after = []
        for i in range(len(stats)-1):
            this_stmt, this_level = stats[i]
            next_stmt = stats[i+1][0]
            have = get_lspace(lines[this_stmt])
            want = this_level * 4
            if want < 0:
                # A comment line.
                if have:
                    # An indented comment line.  If we saw the same
                    # indentation before, reuse what it most recently
                    # mapped to.
                    want = have2want.get(have, -1)
                    if want < 0:
                        # Then it probably belongs to the next real stmt.
                        for j in range(i+1, len(stats)-1):
                            j_line, j_level = stats[j]
                            if j_level >= 0:
                                if have == get_lspace(lines[j_line]):
                                    want = j_level * 4
                                break
                    if want < 0:           # Maybe it's a hanging
                                           # comment like this one,
                        # in which case we should shift it like its base
                        # line got shifted.
                        for j in range(i-1, -1, -1):
                            j_line, j_level = stats[j]
                            if j_level >= 0:
                                want = have + get_lspace(after[j_line-1]) - \
                                       get_lspace(lines[j_line])
                                break
                    if want < 0:
                        # Still no luck -- leave it alone.
                        want = have
                else:
                    want = 0
            assert want >= 0
            have2want[have] = want
            diff = want - have
            if diff == 0 or have == 0:
                after.extend(lines[this_stmt:next_stmt])
            else:
                for line in lines[this_stmt:next_stmt]:
                    if diff > 0:
                        if line == "\n":
                            after.append(line)
                        else:
                            after.append(" " * diff + line)
                    else:
                        remove = min(get_lspace(line), -diff)
                        after.append(line[remove:])
        return self.raw != self.after

    def write(self, f):
        f.writelines(self.after)

    # Line-getter for tokenize.
    def getline(self):
        if self.index >= len(self.lines):
            line = ""
        else:
            line = self.lines[self.index]
            self.index += 1
        return line

    # Line-eater for tokenize.
    def token_eater(self, type, token, (sline, scol), end, line,
                    INDENT=tokenize.INDENT,
                    DEDENT=tokenize.DEDENT,
                    NEWLINE=tokenize.NEWLINE,
                    COMMENT=tokenize.COMMENT,
                    NL=tokenize.NL):

        if type == NEWLINE:
            # A program statement, or ENDMARKER, will eventually follow,
            # after some (possibly empty) run of tokens of the form
            #     (NL | COMMENT)* (INDENT | DEDENT+)?
            self.find_stmt = 1

        elif type == INDENT:
            self.find_stmt = 1
            self.level += 1

        elif type == DEDENT:
            self.find_stmt = 1
            self.level -= 1

        elif type == COMMENT:
            if self.find_stmt:
                self.stats.append((sline, -1))
                # but we're still looking for a new stmt, so leave
                # find_stmt alone

        elif type == NL:
            pass

        elif self.find_stmt:
            # This is the first "real token" following a NEWLINE, so it
            # must be the first token of the next program statement, or an
            # ENDMARKER.
            self.find_stmt = 0
            if line:   # not endmarker
                self.stats.append((sline, self.level))

# Count number of leading blanks.
def get_lspace(line):
    i, n = 0, len(line)
    while i < n and line[i] == " ":
        i += 1
    return i

if __name__ == '__main__':
    main()