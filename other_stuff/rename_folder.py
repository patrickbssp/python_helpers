#!/usr/bin/python3

# Scan a folder recursively and collect all existing file extensions

import sys, re, os.path

file_ext_list = {}

#pattern = r'\d*_\d\s(.*)'

pattern = r'(\d+_\d+)\s(.*)'

def check_dir(work_dir):

	for x in os.listdir(work_dir): # traverse all dirs and files in work_dir
		full_path = os.path.join(work_dir,x)
		if (os.path.isdir(full_path)):

			print('old name: {}'.format(x))
			m = re.match(pattern, x)
			if m:
				old_name = x
				new_name = m.group(2)+' (XXL) '+m.group(1)
				print('Renaming "{}" to "{}"'.format(old_name, new_name))
				os.rename(old_name, new_name)


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
