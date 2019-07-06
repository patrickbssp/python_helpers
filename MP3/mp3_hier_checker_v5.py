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
import shlex
import subprocess
import pathlib
import mutagen
import csv

num_files = 0
num_mp3 = 0
num_violations = 0

field_names = [
	'f_artist',			# artist (from filename)
	'f_album',			# album (from filename)
	'f_title',			# title (from filename)
	'f_track',			# track number (from filename)
	't_artist',			# artist (from tag, TPE1)
	't_album_artist',	# album artist (from tag, TPE2)
	't_album', 			# album (from tag, TALB)
	't_title',			# title (from tag, TIT2)
	't_track',			# track number (from tag, TRCK)
]

unique_artists = set()
unique_albums = set()

all_tags = list()

### Enable/disable debugging (True/False)
debug = False

report_mismatch_flags = {
	'artist'	: True,
	'artist2'	: True,
	'album'		: False,
	'track'		: True,		# Don't change this entry!
	'title'		: False
}

tag_mapping = {
	'TRCK'	: 't_track',
	'TALB'	: 't_album',
	'TPE1'	: 't_artist',
	'TPE2'	: 't_album_artist',
	'TIT2'	: 't_title'
}

substitutions = {
	'artist' : {
		"à;Grumh"						: "à;Grumh...",
		"A7IE"							: ":A7IE:",
		"Adult"							: "Adult.",
		"AC-DC"							: "AC/DC",
		"All My Faith Lost"				: "All My Faith Lost...",
		"An Idea"						: "An:Idea",
		"Arcana Obscura - Tapestry"		: "Arcana Obscura / Tapestry",
		"Ascetic"						: "Ascetic:",
		"Ashley-Story"					: "Ashley/Story",
		"Axon Neuron-Vagwa"				: "Axon Neuron/Vagwa",
		"Bahntier"						: ":Bahntier//",
		"B. Says"						: "B. Says...",
		"B.E.F"							: "B.E.F.",
		"Boyd Rice & FriendsNON"		: "Boyd Rice & Friends/NON",
		"C.A.P"							: "C.A.P.",
		"C.O.C"							: "C.O.C.",
		"Carlos Peron - Peter Ehrlich"	: "Carlos Peron/Peter Ehrlich",
		"Charles Lindbergh N.E.V"		: "Charles Lindbergh N.E.V.",
		"Chameleons U.K"				: "Chameleons U.K.",
		"Concrete-Rage"					: "Concrete/Rage",
		"Crisk"							: "Crisk.",
		"De-Vision"						: "De/Vision",
		"D.I.D"							: "D.I.D.",
		"D.N.S"							: "D.N.S.",
		"David Sylvian - Ryuichi Sakamoto"				: "David Sylvian / Ryuichi Sakamoto",
		"DBMG - RAF"					: "DBMG / RAF",
		"Dinosaur Jr"					: "Dinosaur Jr.",
		"Ditto - Destroyer"				: "Ditto ≠ Destroyer",
		"Dope Stars Inc"				: "Dope Stars Inc.",
		"E.C.M"							: "E.C.M.",
		"E.R.R.A"						: "E.R.R.A.",
		"Estampie - L'Ham De Foc"		: "Estampie / L'Ham De Foc",
		"F-A-V"							: "F/A/V",
		"Fïx8-Sëd8"						: "Fïx8:Sëd8",
		"Fixmer-McCarthy"				: "Fixmer/McCarthy",
		"G.L.O.D"						: "G.L.O.D.",
		"Gary Numan - Tubeway Army"			: "Gary Numan/Tubeway Army",
		"Hell Sector"						: "Hell:Sector",
		"Goethes Erben - Peter Heppner"		: "Goethes Erben / Peter Heppner",
		"Golgatha"							: ":Golgatha:",
		"Golgatha And Dawn & Dusk Entwined"	: ":Golgatha: And Dawn & Dusk Entwined",
		"Golgatha & Birthe Klementowski"	: ":Golgatha: & Birthe Klementowski",
		"Hate Dept"						: "Hate Dept.",
                "Herbst9-Z'Ev"  : "Herbst9/Z'Ev",
                "Howden & Wakeford"         : "Howden/Wakeford",
		"I-Scintilla"					: "I:Scintilla",
		"In The Woods"					: "In The Woods...",
		"Ion Javelin - Harald Lömy"		: "Ion Javelin / Harald Lömy",
		"Joy-Disaster"					: "Joy/Disaster",
		"Keen K. Feat. Dorian E"				: "Keen K. Feat. Dorian E.",
		"L.E.A.K"						: "L.E.A.K.",
		"L.I.N"							: "L.I.N.",
		"L.S.G"							: "L.S.G.",
		"Land-Fire"						: "Land:Fire",
		"Lipps Inc"						: "Lipps Inc.",
		"Liquid G"						: "Liquid G.",
		"M-A-R-R-S"						: "M/A/R/R/S",
		"M.A.D"							: "M.A.D.",
		"Manic P"						: "Manic P.",
                "Mind-State"						: "Mind:State",
		"Mono Inc"						: "Mono Inc.",
                "N.D.M.A"                                               : "N.D.M.A.",
		"O.K"				: "O.K.",
		"O Quam Tristis"				: "O Quam Tristis...",
		"Of The Wand & The Moon"		: ":Of The Wand & The Moon:",
                "Osiris T" : "Osiris T.",
		"P1-E"										: "P1/E",
		"Patenbrigade Wolff"						: "Patenbrigade: Wolff",
		"Patenbrigade Wolff Feat. André Hartung"	: "Patenbrigade: Wolff Feat. André Hartung",
		"PP"							: "PP?",
		"Pretentious, Moi"				: "Pretentious, Moi?",
                "Project Komakino"              : "Project: Komakino",
		"ProTech"						: "Pro>Tech",
		"Public Image Ltd"				: "Public Image Ltd.",
		"Punch Inc"						: "Punch Inc.",
		"R.E.M"							: "R.E.M.",
		"Re-Legion"							: "Re:/Legion",
		"Re-Work"							: "Re/Work",
		"REC"								: "REC.",
		"Rozz Williams - Daucus Karota"		: "Rozz Williams/Daucus Karota",
		"[SITD]"							: "[:SITD:]",
		"S.V.D"								: "S.V.D.",
		"Sabotage Qu'est-ce Que C'est"					: "Sabotage Qu'est-ce Que C'est?",
		"Six Comm - Freya Aswynn"			: "Six Comm / Freya Aswynn",
		"Sixth Comm - Mother Destruction"	: "Sixth Comm / Mother Destruction",
		"Soon"						: "[Soon]",
		"S.K.E.T"					: "S.K.E.T.",
		"Shades Of Hell"			: "Shades:Of:Hell",
                "Spasmodique"   : ":Spasmodique:",
		"Star Inc"					: "Star Inc.",
		"Still Patient"				: "Still Patient?",
		"System-Eyes"				: r"System\\Eyes",
		"Temps Perdu"				: "Temps Perdu?",
		"The Dead Sexy Inc"				: "The Dead Sexy Inc.",
		"The Malice Inc"				: "The Malice Inc.",
		"The Sin-Decay"				: "The Sin:Decay",
		"Test Dept. - Brith Gof"	: "Test Dept. / Brith Gof",
		"T.A.C"						: "T.A.C.",
		"T.C"						: "T.C.",
		"T.C.H"						: "T.C.H.",
		"T.G.V.T"					: "T.G.V.T.",
		"T.H.D"						: "T.H.D.",
		"T.H.E"						: "T.H.E.",
		"T.O.Y"						: "T.O.Y.",
		"U.D.O"						: "U.D.O.",
		"Undergod"					: "Undergod.",
		"V.28"						: "V:28",
		"V.S.B"						: "V.S.B.",
		"W.A.S.P"					: "W.A.S.P.",
		"W.O.M.P"					: "W.O.M.P.",
		"Welle Erdball"				: "Welle: Erdball",
		"Witt - Heppner"			: "Witt / Heppner",
		"Wumpscut"					: ":Wumpscut:",
		"X-Dream Feat. Planet B.E.N"	: "X-Dream Feat. Planet B.E.N.",
		"Zoo"						: "//Zoo",
		"Zos Kia - Coil"			: "Zos Kia/Coil"
	}
}

### files
unique_artists_file = "unique_artists.txt"
unique_albums_file = "unique_albums.txt"

### strip trailing newline and convert to UTF-8
def strip_shell(txt):
	return txt[:-1].decode('utf-8')

def file_md5(file):
	cmd = '/usr/bin/md5sum "{}"'.format(file)
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	txt = strip_shell(p.stdout.read())
	md5 = txt.split()[0]
	return md5

def my_print(str):
	"""
		Wraper to use alternate stdout handle capable of UTF-8 irregarding of environment.
	"""
	print(str, file=uni_stdout)

def parse_file(top_dir, full_path, md5_fh, csv_wh):
	global num_violations

	tag = {}

	path_rel = pathlib.PurePath(full_path).relative_to(top_dir)

	if len(path_rel.parts) != 3:
		num_violations += 1
		print('violation: invalid file: {}'.format(full_path))
		return

	fname = path_rel.parts[2]

	m = re.match("^(\d\d) - (.*)\.mp3", fname)
	if m and len(m.groups()) == 2:

		if md5_fh:
			md5 = file_md5(full_path)
			md5_fh.write('{}  {}\n'.format(md5, path_rel))

		if csv_wh:

			### Extract info from file and path
			tag['f_artist'] = path_rel.parts[0]
			tag['f_album']	= path_rel.parts[1]
			tag['f_track'] = m.group(1)
			tag['f_title'] = m.group(2)

			### Extract info from ID3 tag
			f = mutagen.File(full_path)
			if f:
				for k,v in tag_mapping.items():
					tag[v] = f[k].text[0] if k in f else ''

			if debug:
				print('-----------------------------')
				print(full_path)
				my_print(f.tags.pprint())
#			for k,v in tag.items():
#				my_print('{} : {}'.format(k, v))

			csv_wh.writerow(tag)

	else:
		num_violations += 1
		print("violation: rule_3b: filenames must have format 'xx - Trackname.mp3'")
		print("file: {}".format(fname))
	return tag

def report_mismatch(fname, item, f_item, t_item):
	global num_violations

	num_violations += 1
	print('Mismatch in {}, file: {} tag: {} (file: {})'.format(item, f_item, t_item, fname))


def is_mismatch(f_item, t_item, item):
	return True if f_item != t_item and report_mismatch_flags[item] else False

def check_tag(tag):
	"""
		Check file for errors or inconsistencies.

		Return value: Tag entry if no errors occured; None otherwise
	"""

	global num_mp3
	global num_violations

	full_path = '{}/{}/{} - {}.mp3'.format(tag['f_artist'], tag['f_album'], tag['f_track'], tag['f_title'])

	### Check tags

	unique_artists.add(tag['t_artist'])
	unique_albums.add(tag['t_album'])

	### Track number must match exactly. No excuses...
	if is_mismatch(tag['f_track'], tag['t_track'], 'track'):
		report_mismatch(full_path, "Track number", tag['f_track'], tag['t_track'])

	### Artist may not match exactly due to folder name restrictions
	f_artist = tag['f_artist']
	if is_mismatch(f_artist, tag['t_artist'], 'artist'):

		### Check, whether there is a substitution available
		if f_artist in substitutions['artist']:
			f_artist = substitutions['artist'][f_artist]

			if is_mismatch(f_artist, tag['t_artist'], 'artist'):
				### Still not matching -> error
				report_mismatch(full_path, "Artist", tag['f_artist'], tag['t_artist'])

		else:
			### No substitute found -> error
			report_mismatch(full_path, "Artist", tag['f_artist'], tag['t_artist'])

	if is_mismatch(tag['f_album'], tag['t_album'], 'album'):
		report_mismatch(full_path, "Album", tag['f_album'], tag['t_album'])

	return tag

def parse_dir(top_dir, md5_fh, csv_wh):
	global num_files
	global num_violations
	global num_mp3

	for dirpath, dirnames, filenames in os.walk(top_dir):
		dirnames.sort()
		filenames.sort()
		if (len(dirnames) == 0) and (len(filenames) == 0):
			num_violations += 1
			print("violation: rule_xx: empty folder detected: {}".format(dirpath))

		### then, iterate over files
		for fname in filenames:
			num_files += 1
			tag = parse_file(top_dir, os.path.join(dirpath, fname), md5_fh, csv_wh)
			if tag:
				all_tags.append(tag)
				num_mp3 += 1

def generate_list(top_dir, csv_file=None, md5_file=None):

	md5_fh = None
	csv_wh = None

	### Open MD5 file
	if md5_file:
		md5_fh = open(md5_file, mode='w+', encoding='utf-8')

	### Open CSV file
	if csv_file:
		csv_fh = open(csv_file, mode='w+', encoding='utf-8', errors='surrogateescape')
		csv_wh = csv.DictWriter(csv_fh, fieldnames=field_names, dialect='mp3_csv')
		csv_wh.writeheader()

	parse_dir(str(pathlib.PurePath(top_dir)), md5_fh, csv_wh)

	if md5_file:
		md5_fh.write('-------------------------------------------------------------\n')
		md5_fh.write("Top folder: {}\n".format(top_dir))
		md5_fh.write("{} file(s) checked\n".format(num_files))
		md5_fh.write("{} MP3 file(s) found\n".format(num_mp3))
		md5_fh.write("{} violation(s) found\n".format(num_violations))

	if md5_file:
		md5_fh.close()

	if csv_file:
		csv_fh.close()

	sys.exit(0)

def analyse_csv(csv_file):

	### Open and parse CSV file
	with open(csv_file, mode='r', encoding='utf-8', errors='surrogateescape') as f:
		reader = csv.DictReader(f, fieldnames=field_names, dialect='mp3_csv')
		for row in reader:
			if reader.line_num > 1:
				check_tag(row)

	### Dump unique artists to file
	with open(unique_artists_file, "w", encoding='utf8') as f:
		for artist in sorted(unique_artists):
			f.write('{}\n'.format(artist))
	
	### Dump unique albums to file
	with open(unique_albums_file, "w", encoding='utf8') as f:
		for album in sorted(unique_albums):
			f.write('{}\n'.format(album))

def print_usage_and_die():
	print("""Usage:
	-m <top_dir> <md5_file>             Check file hierarchy, naming rules etc. and dump MD5 hashes.
	-e <top_dir> <csv_file>        	    Extract MP3 tags starting from folder <top_dir> and dump tags to CSV file.
	-c <top_dir> <csv_file> <md5_file>	Combines options -m and -c.
	-a <csv_file>                  Analyse CSV file.
	""".format(sys.argv[0]))
	sys.exit(1)

def main():
	global uni_stdout

	### Register dialect
	csv.register_dialect('mp3_csv', delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\')

	### Open another filehandle to stdout supporting UTF8 to prevent unicode issues with print()
	### Note:	These problems may be only present when running the script locally and work flawless
	###			over SSH.
	uni_stdout = open(1, 'w', encoding='utf-8', closefd=False)

	if len(sys.argv) == 3 and sys.argv[1] == '-a':
		analyse_csv(sys.argv[2])
	elif len(sys.argv) == 4 and sys.argv[1] == '-e':
		generate_list(sys.argv[2], csv_file=sys.argv[3])
	elif len(sys.argv) == 4 and sys.argv[1] == '-m':
		generate_list(sys.argv[2], md5_file=sys.argv[3])
	elif len(sys.argv) == 5 and sys.argv[1] == '-c':
		generate_list(sys.argv[2], csv_file=sys.argv[3], md5_file=sys.argv[4])
	else:
		print_usage_and_die()

	sys.exit(0)

main()

