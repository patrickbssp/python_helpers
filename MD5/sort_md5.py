#! /usr/bin/python3



import sys,re,os.path

def main():
	sort_md5(sys.argv[1]);
	print("check finished");
	sys.exit(0)

def sort_md5(file):

	with open(file) as f:
		lines = f.read().splitlines()
		for line in lines:
			print(line)
			pattern = re.compile("([0-9a-f]{32}) (.*)")
			m = re.search(pattern, line)
			if m:
				print('{} XXX {}'.format(m.group(1), m.group(2)))

main()

