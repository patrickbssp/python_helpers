#! /usr/bin/python3

import sys,re,os.path, chardet

# Return tuple consisting of hash and filename, or None
def split_hash_filename(line):
	pattern = re.compile("([0-9a-f]{32})(\s+\**)(.*)")
	m = re.search(pattern, line)
	if m:
		d = dict()
		d['hash'] = m.group(1)
		d['ws'] = m.group(2)
		d['file'] = m.group(3)
		return d

def open_and_decode_file(in_fname):

	with open(in_fname, 'rb', encoding=None) as in_f:
		raw_data = in_f.read()
		det = chardet.detect(raw_data)
		print('File {}, encoding: {} (confidence: {})'.format(in_fname, det['encoding'], det['confidence']))
		data = raw_data.decode(det['encoding'])
		return data
