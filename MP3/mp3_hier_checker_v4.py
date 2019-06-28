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
report_mismatch['artist'] = True
report_mismatch['artist2'] = True
report_mismatch['album'] = False
report_mismatch['track'] = True
report_mismatch['title'] = False
generate_md5 = False

substitutions = {
	'artist' : {

		'Bahntier'				: ':Bahntier//',
		'Charles Lindbergh N.E.V'		: 'Charles Lindbergh N.E.V.',
		'Crisk'					: 'Crisk.',
		'De-Vision'				: 'De/Vision',
		'D.I.D'					: 'D.I.D.',
		'D.N.S'					: 'D.N.S.',
		'F-A-V'					: 'F/A/V',
		'Fïx8-Sëd8'				: 'Fïx8:Sëd8',
		'Fixmer-McCarthy'			: 'Fixmer/McCarthy',
		'Goethes Erben - Peter Heppner'		: 'Goethes Erben / Peter Heppner',
		'Golgatha'				: ':Golgatha:',
		'Golgatha And Dawn & Dusk Entwined'	: ':Golgatha: And Dawn & Dusk Entwined',
		'Joy-Disaster'				: 'Joy/Disaster',
		'L.E.A.K'				: 'L.E.A.K.',
		'L.I.N'					: 'L.I.N.',
		'L.S.G'					: 'L.S.G.',
		'Lipps Inc'				: 'Lipps Inc.',
		'Liquid G'				: 'Liquid G.',
		'Mono Inc'				: 'Mono Inc.',
		'O Quam Tristis'			: 'O Quam Tristis...',
		'Of The Wand & The Moon'		: ':Of The Wand & The Moon:',
		'Patenbrigade Wolff'			: 'Patenbrigade: Wolff',
		'[SITD]'				: '[:SITD:]',
		'Six Comm - Freya Aswynn'		: 'Six Comm / Freya Aswynn',
		'Sixth Comm - Mother Destruction'	: 'Sixth Comm / Mother Destruction',
		'Soon'					: '[Soon]',
		'S.P.O.C.K'				: 'S.P.O.C.K.',
		'Star Inc'				: 'Star Inc.',
		'Still Patient'				: 'Still Patient?',
		'System-Eyes'				: 'System\\Eyes',
		'Test Dept. - Brith Gof'		: 'Test Dept. / Brith Gof',
		'T.A.C'					: 'T.A.C.',
		'T.C'					: 'T.C.',
		'T.C.H'					: 'T.C.H.',
		'T.G.V.T'				: 'T.G.V.T.',
		'T.H.D'					: 'T.H.D.',
		'T.H.E'					: 'T.H.E.',
		'T.O.Y'					: 'T.O.Y.',
		'T.O.Y'					: 'T.O.Y.',
		'U.D.O'					: 'U.D.O.',
		'Undergod'				: 'Undergod.',
		'V.28'					: 'V:28',
		'V.S.B'					: 'V.S.B.',
		'W.A.S.P'				: 'W.A.S.P.',
		'Welle Erdball'				: 'Welle: Erdball',
		'Witt - Heppner'			: 'Witt / Heppner',
		'Wumpscut'				: ':Wumpscut:',
		'Zos Kia - Coil'			: 'Zos Kia/Coil'
	}
}

### files
unique_artists_file = "unique_artists.txt"
unique_albums_file = "unique_albums.txt"

def compare_tag(fname, item, fn, tag):


	t_item = tag[item]
	if item == 'artist2':
		f_item = fn['artist']
		if t_item == 'Various Artists' or t_item == 'N/A':
			### Skip compilations or missing TPE2 fields
			return
	else:
		f_item = fn[item]

	if (item == 'artist' or item == 'artist2') and f_item in substitutions['artist']:
		f_item = substitutions['artist'][f_item]


	if (t_item != f_item) and report_mismatch[item]:
		print('Mismatch in {}, file: {} tag: {} (file: {})'.format(item, f_item, t_item, fname))

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
				if k not in f and k != 'TPE2':
					print('missing field: {}'.format(k))
					has_missing_fields = True

			if has_missing_fields:
				num_violations += 1
				print('violation: One or more missing fields in file: {}'.format(full_path))
			else:
				tag['artist'] = f['TPE1'].text[0]
				if 'TPE2' in f:
					tag['artist2'] = f['TPE2'].text[0]
				else:
					tag['artist2'] = 'N/A'
				tag['album'] = f['TALB'].text[0]
				tag['title'] = f['TIT2'].text[0]
				tag['track'] = f['TRCK'].text[0]

		if not has_missing_fields:
			unique_artists.add(tag['artist'])
			unique_albums.add(tag['album'])
			for item in ['track', 'artist', 'artist2', 'album', 'title']:
				compare_tag(path_rel, item, fn, tag)

			if debug:
				print('-----------------------------')
				print(fn['track'])
				print(fn['artist'])
				print(fn['album'])
				print(fn['title'])
				print(tag['artist'])
				print(tag['artist2'])
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

