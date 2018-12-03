#! /usr/bin/python3

# Open the file given as parameter and sort the content (hash plus filename) by the filenames.
# The sorted file receives the suffix '_sorted'. The original file is not touched.
# The input file is opened in encoding UTF-8 first, expecting that it was created with md5sum on UNIX.
# If that fails, the file is opened in encoding Latin-1 (ISO-8859-15) instead, as if created with
# MD5Summer on Windows.
#
# History:
#	2017-10-06	Improved recognition/treatment of white-space.
#	2018-10-09	Merged convert and sort modes
#	2018-12-03	Removed obsolete regex
#

import sys,re,os.path

def sort_file(in_f, out_f):

	table = [];
	lines = in_f.read().splitlines()
	for line in lines:
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


in_fname = sys.argv[1];
(root, ext) = os.path.splitext(in_fname);

out_fname = root+"_sorted"+ext;
out_f = open(out_fname, 'w', encoding='utf-8')

try:
	encoding = 'utf-8'
	print('Opening file {} with encoding {}'.format(in_fname, encoding))
	with open(in_fname, encoding=encoding) as in_f:
		sort_file(in_f, out_f)
except:
	print('Failed to open file {} with encoding {}, trying again with different encoding'.format(in_fname, encoding))
	encoding = 'latin-1'
	print('Opening file {} with encoding {}'.format(in_fname, encoding))
	with open(in_fname, encoding=encoding) as in_f:
		sort_file(in_f, out_f)
