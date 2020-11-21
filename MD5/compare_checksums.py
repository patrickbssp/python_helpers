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

result = {}

new_files = {}
rem_files = {}

def print_usage_and_die():
	print('Error: Invalid number of arguments.')
	print('Usage: {} <left_file> <right_file>'.format(sys.argv[0]))
	sys.exit()

def read_file(in_f, pos):
	# Validate pos
	if ((pos != "left") and (pos != "right")):
		return

	lines = in_f.read().splitlines()
	for line in lines:
		pattern = re.compile("([0-9a-f]{32})(\s+\**)(.*)")
		m = re.search(pattern, line)
		if m:
			m_hash = m.group(1)
			m_file = m.group(3)

			if not m_hash in result:
				# First file with this hash, create empty entry
				result[m_hash] = {"left" : [], "right" : []}

			result[m_hash][pos].append(m_file)

def analyse_results():
	for m_hash in result:
		v = result[m_hash]

		if((len(v["left"]) == 0) and len(v["right"]) > 0):
			print("New files:")
			if not m_hash in new_files:
				new_files[m_hash] = []
			for f in v["right"]:
				print("  {}".format(f))
				new_files[m_hash].append(f)
		elif((len(v["right"]) == 0) and len(v["left"]) > 0):
			print("Removed files:")
			if not m_hash in rem_files:
				rem_files[m_hash] = []
			for f in v["left"]:
				print("  {}".format(f))
				rem_files[m_hash].append(f)
		elif((len(v["right"]) > 0) and len(v["left"]) > 0):
			print("Identical files:")
			for f in v["left"]:
				print("  {}".format(f))
		else:
			print("Error")
 

	print("\nNew files:\n")
	for m_hash in new_files:
		for f in new_files[m_hash]:
			print("{} {}".format(m_hash, f))

	print("\nRemoved files:\n")
	for m_hash in rem_files:
		for f in rem_files[m_hash]:
			print("{} {}".format(m_hash, f))

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print_usage_and_die()

	l_file = sys.argv[1];
	r_file = sys.argv[2];

	encoding = 'utf-8'
	with open(l_file, encoding=encoding) as in_f:
		read_file(in_f, "left")

	with open(r_file, encoding=encoding) as in_f:
		read_file(in_f, "right")

	analyse_results()
