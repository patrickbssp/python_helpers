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
#	2025-06-04	Use improved file list generation

import sys,glob,os.path
import argparse
import pathlib

# custom modules
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers

def sort_file(in_fname, out_fname):

	out_f = open(out_fname, 'w', encoding='utf-8')

	table = [];
	data = helpers.open_and_decode_file(in_fname)
	for line in data.splitlines():

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

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('path', nargs='+', help='Single or multiple files and/or folders to be processed.')

	args = parser.parse_args()

	filelist = helpers.create_filelist(args.path)

	# Process files
	for in_fname in filelist:
		(root, ext) = os.path.splitext(in_fname);
		out_fname = root+"_sorted"+ext;

		sort_file(in_fname, out_fname)
