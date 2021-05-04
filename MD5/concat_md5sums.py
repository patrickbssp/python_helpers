#!/usr/bin/python3

# rules:
# a path to an MP3 file should have following structure:
# Artist/Album/xx - Track.mp3
# where xx is the track number
# so, the directory hierarchy has 3 levels:
# level 1: (Artist)
#   - no files are allowed in this level, only directories
# level 2: (Album)
#   - no files are allowed in this level, only directories
# level 3: (Track)
#   - no directories are allowed in this level, only files
#
# rule_1a: no files are allowed in level 1
# rule_2a: no files are allowed in level 2
# rule_3a: no directories are allowed in level 3
# rule_3b: filenames must have format 'xx - Trackname.mp3'

import sys,re,os.path

no_files = 0;
no_mp3 = 0;
no_violations = 0;

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
		
