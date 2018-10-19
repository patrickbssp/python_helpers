#!/usr/bin/python3

# Note: this script will only work with the 'real' unrar, not the unrar_wrapper provided by opensuse-oss!

import sys, os, subprocess
import rarfile
import shutil

MIN_PYTHON = (3, 6)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON)
TMP_DIR = '/run/unrar'

# Return MD5 hash of file
def get_md5(fname):
	cp = subprocess.run(["md5sum", fname], stdout=subprocess.PIPE, encoding='UTF-8')
	md5 = cp.stdout.split()[0]
	return md5

def md5_rar(fname):
	if not rarfile.is_rarfile(fname):
		# Silently ignoring non-RAR files
		return

	# hash the RAR file itself
	md5 = get_md5(fname)
	print('{}  {}'.format(md5, fname))

	# hash the content of the file
	rf = rarfile.RarFile(fname)
	for f in rf.infolist():
		if f.isdir():
			return
		tmp_path = os.path.join(TMP_DIR, f.filename)

		# Extract current file to temp folder, calculate MD5 hash, then delete temp file
		rf.extract(f.filename, path=TMP_DIR)
		md5 = get_md5(tmp_path)
		os.remove(tmp_path)
		print('{}    {}'.format(md5, f.filename))

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Error: Invalid number of arguments.')
		sys.exit()

	fname = sys.argv[1]
	if os.path.isdir(fname):
		for dirpath, dirnames, filenames in os.walk(fname):
			for file in filenames:
				fname = os.path.join(dirpath, file)
				md5_rar(fname)

	elif os.path.isfile(fname):
		md5_rar(fname)

	shutil.rmtree(TMP_DIR)
