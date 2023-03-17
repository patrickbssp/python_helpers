#! /usr/bin/python3

import sys,re,os.path, chardet, helpers

def analyse_file(in_fname):
	tot_num_files = 0
	num_dupes = 0
	result = {}

	data = helpers.open_and_decode_file(in_fname)

	lines = data.splitlines()
	for line in lines:
		m = helpers.split_hash_filename(line)
		if m:
			if not m['hash'] in result:
				# First file with this hash
				result[m['hash']] = [m['file']]
			else:
				# Add file to hash array
				result[m['hash']].append(m['file'])

	# Iterate over array and dump dupes
	for m['hash'] in result:
		num_files = len(result[m['hash']])
		tot_num_files += num_files
		if num_files > 1:
			num_dupes += 1
			print('Duplicates with MD5 {}:'.format(m['hash']))
			for f in result[m['hash']]:
				print('  {}'.format(f))

	print('{} files scanned'.format(tot_num_files))
	print('{} hashes found with duplicates'.format(num_dupes))

in_fname = sys.argv[1];
(root, ext) = os.path.splitext(in_fname);

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Error: Invalid number of arguments.')
		sys.exit()

	analyse_file(sys.argv[1])
