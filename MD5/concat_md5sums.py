#!/usr/bin/python3

import sys,re,os.path

if len(sys.argv) != 2:
	print('Argument missing')
	sys.exit(1)

with open('outfile.txt', 'w') as out_file:
	for i in range(1,291):
		gt = 'GT{:03}'.format(i)
		filename = '{}/{}.md5'.format(sys.argv[1], gt)
		print(filename)
		with open(filename, 'r') as in_file:
			for line in in_file:
				pattern = re.compile("([0-9a-f]{32})(\s+\**)(.*)")
				m = re.search(pattern, line)
				if m:
					m_hash = m.group(1)
					m_file = m.group(3)
				m_file = m_file.replace('/media/cdrom0', gt)
				entry = '{}  {}\n'.format(m_hash, m_file)
				out_file.write(entry)
				print(entry)
		
