#! /usr/bin/python3

import sys,re,os.path


def analyse_file(in_f):
	tot_num_files = 0
	num_dupes = 0
	result = {}

	lines = in_f.read().splitlines()
	for line in lines:
		pattern = re.compile("([0-9a-f]{32})(\s+\**)(.*)")
		m = re.search(pattern, line)
		if m:
			m_hash = m.group(1)
			m_file = m.group(3)

			if not m_hash in result:
				# First file with this hash
				result[m_hash] = [m_file]

			else:
				# Add file to hash array
				result[m_hash].append(m_file)

	# Iterate over array and dump dupes
	for m_hash in result:
		num_files = len(result[m_hash])
		tot_num_files += num_files
		if num_files > 1:
			num_dupes += 1
			print('Duplicates with MD5 {}:'.format(m_hash))
			for f in result[m_hash]:
				print('  {}'.format(f))

	print('{} files scanned'.format(tot_num_files))
	print('{} hashes found with duplicates'.format(num_dupes))

in_fname = sys.argv[1];
(root, ext) = os.path.splitext(in_fname);

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Error: Invalid number of arguments.')
		sys.exit()

	encoding = 'utf-8'
	print('Opening file {} with encoding {}'.format(in_fname, encoding))
	with open(in_fname, encoding=encoding) as in_f:
		analyse_file(in_f)
