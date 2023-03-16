#! /usr/bin/python3

# Compare two files containing hashes and filenames, usually to compare two different
# snapshots of the same folder, e.g. a NAS.
# Both files are expected to be generated by md5sum or md5 -r.
# The input file is opened in encoding UTF-8 first, expecting that it was created with md5sum on UNIX.
# If that fails, the file is opened in encoding Latin-1 (ISO-8859-15) instead, as if created with
# MD5Summer on Windows.
#
# TODO: Add variant comparing whether files in LHS checksum file are contained in RHS checksum file.
# Don't care about files present in RHS checksum file, but missing in LHS checksum file.
# If considering the LHS file as the older list, and the RHS file as the newer one respectively,
# then LHS only files are files were deleted, and RHS only files were added.

import sys,re,os.path, chardet, helpers

def print_usage_and_die():
	print('Error: Invalid number of arguments.')
	print('Usage: {} <left_file> <right_file>'.format(sys.argv[0]))
	sys.exit()

def read_file(in_fname, pos, work_list):

		data = helpers.open_and_decode_file(in_fname)

		# Validate pos
		if ((pos != "left") and (pos != "right")):
			return

		lines = data.splitlines()
		for line in lines:
			m = helpers.split_hash_filename(line)
			if m:
				m_hash = m['hash']
				m_file = m['file']

				if not m_hash in work_list:
					# First file with this hash, create empty entry
					work_list[m_hash] = {"left" : [], "right" : []}

				work_list[m_hash][pos].append(m_file)

def analyse_results(work_list):

	rhs_only = {}
	lhs_only = {}
	both = {}

	for m_hash in work_list:
		v = work_list[m_hash]

		if((len(v["left"]) == 0) and len(v["right"]) > 0):
			# New files
			if not m_hash in rhs_only:
				rhs_only[m_hash] = []
			for f in v["right"]:
				rhs_only[m_hash].append(f)
		elif((len(v["right"]) == 0) and len(v["left"]) > 0):
			# Removed files
			if not m_hash in lhs_only:
				lhs_only[m_hash] = []
			for f in v["left"]:
				lhs_only[m_hash].append(f)
		elif((len(v["right"]) > 0) and len(v["left"]) > 0):
			# Identical files
			if not m_hash in both:
				both[m_hash] = []
			for f in v["right"]:
				both[m_hash].append(f)
			for f in v["left"]:
				both[m_hash].append(f)
		else:
			print("Error")

	print("\nIdentical files:\n")
	for m_hash in both:
		for f in both[m_hash]:
			print("{} {}".format(m_hash, f))

	print("\nRHS files:\n")
	for m_hash in rhs_only:
		for f in rhs_only[m_hash]:
			print("{} {}".format(m_hash, f))

	print("\nLHS files:\n")
	for m_hash in lhs_only:
		for f in lhs_only[m_hash]:
			print("{} {}".format(m_hash, f))

	print("\nStatistics")
	print("  RHS files: {}".format(len(rhs_only)))
	print("  LHS files: {}".format(len(lhs_only)))
	print("  Both:      {}".format(len(both)))

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print_usage_and_die()

	work_list = {}

	l_file = sys.argv[1];
	r_file = sys.argv[2];

	read_file(l_file, "left", work_list)
	read_file(r_file, "right", work_list)

	analyse_results(work_list)
