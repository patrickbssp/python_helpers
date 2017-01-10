#!/usr/bin/python3

# 10.11.2016 Ported to Python3, using mutagen
# 16.11.2016 Added list of unique artists

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
#
# Test cases:
#
# - Track number containing letter O instead of digit 0
# - Double spaces
# - File suffix mixed or all upper-case
# - Empty Artist folder 
# - Empty Album folder 
# - Files in Artist folder
# - Non-MP3-Files in any folder
 

import sys
import re
import os.path
import pathlib
import mutagen

num_files = 0
num_mp3 = 0
num_violations = 0

unique_artists = set()
unique_albums = set()

### Enable/disable debugging (True/False)
debug = False

report_mismatch = {}
report_mismatch['artist'] = False
report_mismatch['album'] = False
report_mismatch['track'] = True
report_mismatch['title'] = False
generate_md5 = False

### files
unique_artists_file = "unique_artists.txt"
unique_albums_file = "unique_albums.txt"

def compare_tag(item, fn, tag):
	if (tag[item] != fn[item]) and report_mismatch[item]:
		print('Mismatch in {}, file: {}, id: {}'.format(item, fn[item], tag[item]))

# fname is filename including path
def check_file(full_path):
	global num_mp3
	global num_violations

	tag = {}
	fn = {}

	path_rel = pathlib.PurePath(full_path).relative_to(start_dir)

	if len(path_rel.parts) != 3:
		num_violations += 1
		print('violation: invalid file: {}'.format(full_path))
		return

	fn['artist'] = path_rel.parts[0]
	fn['album']	= path_rel.parts[1]
	fname = path_rel.parts[2]

	m = re.match("^(\d\d) - (.*)\.mp3", fname)
	if m:
		num_mp3 += 1
		if generate_md5:
			os.system("md5sum \"" + full_path + "\"")

		### Extract info from file and path
		fn['track'] = m.group(1)
		fn['title'] = m.group(2)

		### Extract info from ID3 tag
		f = mutagen.File(full_path)
		if f:
			required_fields = ['TRCK', 'TALB', 'TPE1', 'TPE2', 'TIT2']
			has_missing_fields = False

			for k in required_fields:
				if k not in f:
					print('missing field: {}'.format(k))
					has_missing_fields = True

			if has_missing_fields:
				num_violations += 1
				print('violation: One or more missing fields in file: {}'.format(full_path))
			else:
				tag['artist'] = f['TPE1'].text[0]
				tag['album'] = f['TALB'].text[0]
				tag['title'] = f['TIT2'].text[0]
				tag['track'] = f['TRCK'].text[0]

		if not has_missing_fields:
			unique_artists.add(tag['artist'])
			unique_albums.add(tag['album'])
			for item in ['track', 'artist', 'album', 'title']:
				compare_tag(item, fn, tag)

			if debug:
				print('-----------------------------')
				print(fn['track'])
				print(fn['title'])
				print(fn['artist'])
				print(fn['album'])
				print(tag['artist'])
				print(tag['album'])


	else:
		num_violations += 1
		print("violation: rule_3b: filenames must have format 'xx - Trackname.mp3'")
		print("file: {}".format(fname))

def main():
	global start_dir

	if len(sys.argv) != 2:
		print('Usage: {} folder_name'.format(sys.argv[0]))
		sys.exit(1)
		
	start_dir = pathlib.PurePath(sys.argv[1])
#	check_dir(sys.argv[1])
	check_dir(str(start_dir))
	print('-------------------------------------------------------------')
	print("{} file(s) checked".format(num_files))
	print("{} MP3 file(s) found".format(num_mp3))
	print("{} violation(s) found".format(num_violations))

	### Dump unique artists to file
	with open(unique_artists_file, "w") as f:
		for artist in sorted(unique_artists):
			f.write('{}\n'.format(artist))
	
	### Dump unique albumss to file
	with open(unique_albums_file, "w") as f:
		for album in sorted(unique_albums):
			f.write('{}\n'.format(album))

	sys.exit(0)

def check_dir(work_dir):
	global num_files
	global num_violations
	for dirpath, dirnames, filenames in os.walk(work_dir):

		if (len(dirnames) == 0) and (len(filenames) == 0):
			num_violations += 1
			print("violation: rule_xx: empty folder detected: {}".format(dirpath))

		### then, iterate over files
		for fname in filenames:
			num_files += 1
			check_file(os.path.join(dirpath, fname))

main()

