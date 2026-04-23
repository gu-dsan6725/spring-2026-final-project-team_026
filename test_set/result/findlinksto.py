#! /usr/bin/env python

# findlinksto
#
# find symbolic links to a path matching a regular expression

import os
import sys
import re
import getopt

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], '')
		if len(args) < 2:
			raise getopt.error, 'not enough arguments'
	except getopt.error as msg:
		sys.stderr.write(msg + '\n')
		print('usage: findlinksto pattern directory ...')
		sys.exit(2)
	pat, dirs = args[0], args[1:]
	prog = re.compile(pat)
	for dirname in dirs:
		for root, _, names in os.walk(dirname):
			for name in names:
				name = os.path.join(root, name)
				try:
					if os.path.islink(name):
						continue
					linkto = os.readlink(name)
					if prog.search(linkto) >= 0:
						print(name, '->', linkto)
				except OSError:
					pass

if __name__ == "__main__":
	main()