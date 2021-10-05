#! /usr/bin/python3

# Open the file given as parameter, expecting MD5 sums from md5summer from Sony Camera photos on an SD card.
# Such checksum files contain RAW and JPG files in the same sub folder. This tool splits JPG and RAW files
# into separate subfolders, prepended by JPG/ or RAW/
#
# Example:
#
# Before:
#
# 7f58214080a07ac5435357a1d1d0ba4d *10010910/DSC05798.JPG
# d9b3a9d75845f12a09777b871bf5a711 *10010910/DSC05798.ARW
# 43f76adf6f1097a1d2fd7929515d2375 *10010910/DSC05799.JPG
# 2d5afd335dad0f8ba6b658d4c1f2a482 *10010910/DSC05799.ARW
#
# After:
#
# 7f58214080a07ac5435357a1d1d0ba4d *10010910/JPG/DSC05798.JPG
# 43f76adf6f1097a1d2fd7929515d2375 *10010910/JPG/DSC05799.JPG
# d9b3a9d75845f12a09777b871bf5a711 *10010910/RAW/DSC05798.ARW
# 2d5afd335dad0f8ba6b658d4c1f2a482 *10010910/RAW/DSC05799.ARW
#
# Output is written to a new file with the original name plus suffix _splitted.
#
# History:
#	2021-10-05	First version
#

import sys,re,os.path

def split_file(in_f, out_f):

	table = [];
	lines = in_f.read().splitlines()
	for line in lines:
		pattern = re.compile("([0-9a-f]{32})(\s+\**)(.*)")
		m = re.search(pattern, line)
		if m:
			item = {'hash': m.group(1), 'ws': m.group(2), 'file': m.group(3)}

			splitted_path = item['file'].split('/')
			fname = splitted_path[-1]
			ext = fname.split('.')[-1]

			# create intermediate folder if not existent
			if ext == "JPG" and splitted_path[-2] != "JPG":
				splitted_path.insert(-1, "JPG")
			elif ext == "ARW" and splitted_path[-2] != "RAW":
				splitted_path.insert(-1, "RAW")

			# Replace filename
			item['file'] = "/".join(splitted_path)

			table.append(item)
		else:
			### line does not match, copy verbatim
			out_f.write(line+'\n')

	### sort table in place by key 'file'
	table.sort(key=lambda tup: tup['file'])

	### append sorted list to out file
	for item in table:
		out_f.write(item['hash']+item['ws']+item['file']+'\n')


in_fname = sys.argv[1];
(root, ext) = os.path.splitext(in_fname);

out_fname = root+"_splitted"+ext;
out_f = open(out_fname, 'w', encoding='utf-8')

try:
	encoding = 'utf-8'
	print('Opening file {} with encoding {}'.format(in_fname, encoding))
	with open(in_fname, encoding=encoding) as in_f:
		split_file(in_f, out_f)
except:
	print('Failed to open file {} with encoding {}, trying again with different encoding'.format(in_fname, encoding))
	encoding = 'latin-1'
	print('Opening file {} with encoding {}'.format(in_fname, encoding))
	with open(in_fname, encoding=encoding) as in_f:
		split_file(in_f, out_f)
