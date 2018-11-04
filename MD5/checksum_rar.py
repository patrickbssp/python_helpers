#!/usr/bin/python3

# Note: this script will only work with the 'real' unrar, not the unrar_wrapper provided by opensuse-oss!

import sys, os, subprocess
import rarfile
import zipfile
import shutil

MIN_PYTHON = (3, 6)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON)
TMP_DIR = '/run/unrar'

num_errors = 0
num_warnings = 0

def report_error(str):
	global num_errors
	print('{}    {}'.format('ERROR: ', str))
	num_errors += 1

def report_warning(str):
	global num_warnings
	print('{}    {}'.format('WARNING: ', str))
	num_warnings += 1

# Return MD5 hash of file
def get_md5(fname):
	cp = subprocess.run(["md5sum", fname], stdout=subprocess.PIPE, encoding='UTF-8')
	md5 = cp.stdout.split()[0]
	return md5

def detect_type(fname):
	ftype = ''
	wrong_ext = False
	ext = os.path.splitext(fname)[1][1:]
	if rarfile.is_rarfile(fname):
		ftype = 'rar'
		if ext.lower() not in ['rar', 'cbr']:
			wrong_ext = True
	elif zipfile.is_zipfile(fname):
		ftype = 'zip'
		if ext.lower() not in ['zip', 'cbz']:
			wrong_ext = True
	else:
		report_warning('{} {}'.format('Unknown/unexpected file type', fname))
		ftype = 'unknown'

	if wrong_ext:
		report_warning('Type of file {} is {} but extension is {}'.format(fname, ftype, ext))

	return ftype

def md5_rar(fname):
	global num_errors

	ftype = detect_type(fname)

	if ftype == 'unknown':
		return

	# hash the RAR file itself
	md5 = get_md5(fname)
	print('{}  {}'.format(md5, fname))

	if ftype == 'rar':
		cf = rarfile.RarFile(fname)
	elif ftype == 'zip':
		cf = zipfile.ZipFile(fname)

	# hash the content of the file
	for f in cf.infolist():
		if ftype == 'rar' and f.isdir():
			return
		elif ftype == 'zip' and f.is_dir():
			return

		tmp_path = os.path.join(TMP_DIR, f.filename)

		# Extract current file to temp folder, calculate MD5 hash, then delete temp file
		try:
			cf.extract(f.filename, path=TMP_DIR)
			md5 = get_md5(tmp_path)
			os.remove(tmp_path)
			print('{}    {}'.format(md5, f.filename))
		except rarfile.RarCRCError:
			report_error('{} {}'.format('Bad CRC', f.filename))

if __name__ == '__main__':
	file_list = []

	if len(sys.argv) != 2:
		print('Error: Invalid number of arguments.')
		sys.exit()

	fname = sys.argv[1]
	if os.path.isdir(fname):
		for dirpath, dirnames, filenames in os.walk(fname):
			for file in filenames:
				fname = os.path.join(dirpath, file)
				file_list.append(fname)

	elif os.path.isfile(fname):
		file_list.append(fname)

	file_list.sort()
	for fname in file_list:
		md5_rar(fname)

	shutil.rmtree(TMP_DIR)
	print('FINISHED')
	print('{} error(s)'.format(num_errors))
	print('{} warning(s)'.format(num_warnings))
