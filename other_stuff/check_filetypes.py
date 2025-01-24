#!/usr/bin/python3

# Scan a folder recursively and collect all existing file extensions

import sys, re, os.path

file_ext_list = {}

def check_dir(work_dir):

	for x in os.listdir(work_dir): # traverse all dirs and files in work_dir
        	# Skip hidden files/folders
		if x[0] == '.':
			continue
		full_path=os.path.join(work_dir,x)
		if (os.path.isdir(full_path)):
			### descend to folder (recursively)
			check_dir(full_path)
		if (os.path.isfile(full_path)):
			# get extension
			file_name, file_ext = os.path.splitext(full_path)
			file_ext = file_ext[1:]
			if file_ext not in file_ext_list:
				# create a dict with extension as key and the filename as first list entry
				file_ext_list[file_ext] = [file_name]
#				d = { file_ext : [file_name]}
#				file_ext_list.append(d)
			else:
				# Append to existing list
				file_ext_list[file_ext].append(file_name)

def print_usage_and_quit():
	print("usage: {} folder".format(sys.argv[0]))
	sys.exit(0)

if __name__ == '__main__':
	argc = len(sys.argv)
	if argc == 1:
		print_usage_and_quit()

	### last arg is supposed to be the start folder
	start_dir = sys.argv[-1]
	if not os.path.isdir(start_dir):
		print("{} is not a valid folder".format(start_dir))
		print_usage_and_quit()

	check_dir(start_dir)
	for file_ext in file_ext_list:
		print('  {} {}'.format(file_ext, len(file_ext_list[file_ext])))
		
	sys.exit(0)
