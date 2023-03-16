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
#	2023-03-16	Improved file import
#

import sys,re,os.path, chardet, helpers

def sort_file(data, out_f):

	table = [];
	lines = data.splitlines()
	for line in lines:

		item = helpers.split_hash_filename(line)
		if item:
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

data = helpers.open_and_decode_file(in_fname)
sort_file(data, out_f)
