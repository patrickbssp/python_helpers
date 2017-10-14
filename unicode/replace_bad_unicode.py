#!/usr/bin/python3

import sys

#repl = {
#	{'\x00\xc3', ''},
#}

in_fname = sys.argv[1]

with open(in_fname, encoding='utf-8') as in_f:
	lines = in_f.read().splitlines()
	for line in lines:
		pos = line.find(u'\u00c3')
		if pos>=0:
			print(line)
			print(pos)


