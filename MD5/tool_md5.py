#! /usr/bin/python3

# This script serves two purposes:
#
# 1. With operation argument 'convert', it opens the file given as parameter
#		and converts the file format from latin-1 (as provided by md5summer) to UTF-8.
#		The converted file receives the suffix '_converted'. The original file is not touched.
#
# 2. With operation argument 'sort', it opens the file given as parameter
#		and sorts the content (hash plus filename) by the filenames.
#		The sorted file receives the suffix '_sorted'. The original file is not touched.
#
# History:
#	2017-10-06	Improved recognition/treatment of white-space.
#

import sys,re,os.path

table = [];

if len(sys.argv) != 3:
	print("wrong arguments")
	print("Usage: {} convert|sort <file>".format(sys.argv[0]))
	sys.exit(0)


op = sys.argv[1];
in_fname = sys.argv[2];
(root, ext) = os.path.splitext(in_fname);

if op == 'convert':
	out_fname = root+"_converted"+ext;
	out_f = open(out_fname, 'w')
	with open(in_fname, encoding='latin-1') as in_f:
		lines = in_f.read().splitlines()
		for line in lines:
			out_f.write(line+'\n')
	out_f.close()

elif op == 'sort':
	out_fname = root+"_sorted"+ext;
	out_f = open(out_fname, 'w', encoding='utf-8')

	with open(in_fname, encoding='utf-8') as in_f:
		lines = in_f.read().splitlines()
		for line in lines:
			pattern = re.compile("([0-9a-f]{32}) \*(.*)")
			m = re.search(pattern, line)
			if m:
				item = {'hash': m.group(1), 'file': m.group(2)}
			pattern = re.compile("([0-9a-f]{32})(\s+\**)(.*)")
			m = re.search(pattern, line)
			if m:
				item = {'hash': m.group(1), 'ws': m.group(2), 'file': m.group(3)}
				table.append(item)
			else:
				### line does not match, copy verbatim
				out_f.write(line+'\n')

	### sort table in place by key 'file'
	table.sort(key=lambda tup: tup['file'])

	### append sorted list to out file
	for item in table:
		out_f.write(item['hash']+item['ws']+item['file']+'\n')
	out_f.close()

