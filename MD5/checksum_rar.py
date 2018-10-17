#!/usr/bin/python3

# Note: this script will only work with the 'real' unrar, not the unrar_wrapper provided by opensuse-oss!

import sys, os, subprocess
import rarfile

MIN_PYTHON = (3, 6)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON)

# Return MD5 hash of file
def get_md5(fname):
	cp = subprocess.run(["md5sum", fname], stdout=subprocess.PIPE, encoding='UTF-8')
	md5 = cp.stdout.split()[0]
	return md5

def md5_rar(fname):
	rf = rarfile.RarFile(fname)
	for f in rf.infolist():
		tmp_dir = '/tmp'
		tmp_path = os.path.join(tmp_dir, f.filename)

		# Extract current file to temp folder
		rf.extract(f.filename, path=tmp_dir)

		# Calculate MD5 hash
		md5 = get_md5(tmp_path)

		# Delete temp file
		os.remove(tmp_path)

		str = '{}    {}'.format(md5, f.filename)
		print(str)


if __name__ == '__main__':
	fname = sys.argv[1]

	md5 = get_md5(fname)
	str = '{}  {}'.format(md5, fname)
	print(str)

	md5_rar(fname)

