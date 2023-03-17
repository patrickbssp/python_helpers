#! /usr/bin/python3

import sys,re,os.path, chardet, helpers

def check_dupes(in_fname):
	tot_num_files = 0
	num_dupes = 0
	result = {}

	data = helpers.open_and_decode_file(in_fname)

	for line in data.splitlines():
		item = helpers.split_hash_filename(line)
		if item:
			if not item['hash'] in result:
				# First file with this hash
				result[item['hash']] = [item['file']]
			else:
				# Add file to hash array
				result[item['hash']].append(item['file'])

	# Iterate over array and dump dupes
	for hash in result:
		num_files = len(result[hash])
		tot_num_files += num_files
		if num_files > 1:
			num_dupes += 1
			print('Duplicates with MD5 {}:'.format(hash))
			for f in result[hash]:
				print('  {}'.format(f))

	print('{} files scanned'.format(tot_num_files))
	print('{} hashes found with duplicates'.format(num_dupes))

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Error: Invalid number of arguments.')
		sys.exit()

	check_dupes(sys.argv[1])
