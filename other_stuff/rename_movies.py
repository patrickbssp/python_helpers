#!/usr/bin/python3

# Rename movies/series titles

import sys, re, glob, os.path

tests = {
    '2025-10-18_20-15_Der-Bozen-Krimi_season-1_familienehre_episode-16_hr_hd.mp4' :
    'Der Bozen-Krimi - S01E16 - familienehre (HR HD, 2025-10-18).mp4',
	'2025-10-20_22-00_Tatort_season-1_rache-engel_episode-614_hr_hd.mp4' :
	'Tatort - E614 - rache engel (HR HD, 2025-10-20).mp4',
	'2025-10-22_21-45_Nord-Nord-Mord_season-1_sievers-sieht-gespenster_episode-18_zdf-neo_hd.mp4' :
	'Nord Nord Mord - S01E18 - sievers sieht gespenster (ZDF Neo HD, 2025-10-22).mp4',
	'2025-10-22_22-00_Tatort_season-1_angriff-auf-wache-08_episode-1105_sr-fernsehen_hd.mp4' : 
	'Tatort - E1105 - angriff auf wache 08 (SR Fernsehen HD, 2025-10-22).mp4',
	'2025-10-24_22-15_Gremlins-Kleine-Monster_super-rtl_hq.mp4' :
	'Gremlins Kleine Monster (Super RTL HQ, 2025-10-24).mp4',
	'2025-10-25_20-15_Hitlers-Volk_krieg-verbrechen-1939-1941_episode-3_ard-alpha_hd.mp4' :
	'Hitlers Volk - E03 - krieg verbrechen 1939 1941 (ARD Alpha HD, 2025-10-25).mp4',
	'2025-10-21_20-15_Tatort-3x-Schwarzer-Kater_season-1_3-x-schwarzer-kater_episode-543_br_hd.mp4' :
	'Tatort-3x-Schwarzer-Kater_season-1_3-x-schwarzer-kater_episode-543 (BR HD, 2025-10-21).mp4'
}

series_without_seasons = [
	'Tatort',
	'Hitlers Volk'
]

series_translations = {
	'Der Bozen Krimi' : 'Der Bozen-Krimi'
}

broadcaster_list = {
	'ard_hd'			: 'ARD HD',
	'ard-alpha_hd'		: 'ARD Alpha HD',
	'br_hd'				: 'BR HD',
	'hr_hd'				: 'HR HD',
	'mdr_hd'			: 'MDR HD',
	'ndr_hd'			: 'NDR HD',
	'n-tv_hq'			: 'N-TV HQ',
	'one_hd'			: 'One HD',
	'rbb_hd'			: 'RBB HD',
	'sr-fernsehen_hd'	: 'SR Fernsehen HD',
	'swr_hd'			: 'SWR HD',
	'super-rtl_hq'		: 'Super RTL HQ',
	'wdr_hd'			: 'WDR HD',
	'zdf_hd'			: 'ZDF HD',
	'zdf-neo_hd'		: 'ZDF Neo HD',
	'zdf-info_hd'		: 'ZDF Info HD',
}

def print_usage_and_quit():
	print("usage: {} folder".format(sys.argv[0]))
	sys.exit(0)

def extract_digits(prefix, str):
	p = rf'^\S*{prefix}-(\d*)\S*'
	m = re.match(p, str)
	if m:
		return m.group(1)

def convert_file_name(file_name):
	print()
	file_ext = ''
	date = ''
	title = ''
	season = ''
	episode = ''
	season_episode = ''
	broadcaster = ''
	file_stem, file_ext = os.path.splitext(file_name)

	# Identify broadcaster
	for k,v in enumerate(broadcaster_list):
		if file_stem.endswith(v):
			broadcaster = v
			break
	if not broadcaster:
		print(f'No broadcaster found for: {file_name}')
		return
		
	# remove broadcaster from string
	title_raw = file_stem.replace(broadcaster,'')
	# Look-up and replace broadcaster
	broadcaster = broadcaster_list[broadcaster]
	# extract date
	m = re.match(r"^(\d\d\d\d-\d\d-\d\d)_\d\d-\d\d_(\S*)", title_raw)
	if m and len(m.groups()) == 2:
		date = m.group(1)
		title_raw = m.group(2)
		# Extract season and episode
		season = extract_digits('season', title_raw)
		episode = extract_digits('episode', title_raw)
		# Remove season and episode from title
		title_raw = title_raw.replace(f'season-{season}_', '')
		title_raw = title_raw.replace(f'episode-{episode}_', '')
		# Remove leading and trailing underscores
		title_raw = title_raw.strip('_')
		# Replace dashes with spaces
		title_raw = title_raw.replace('-', ' ')
		if season  and episode:
			season_episode = f'S{int(season):02}E{int(episode):02}'
		# Underscores are used to separate series and episode titles
		new_title = ''
		s = title_raw.split('_')
		if len(s) == 2:
			# Got series and episode title
			series = s[0]
			if series in series_translations:
				series = series_translations[series]
			if series in series_without_seasons:
				print(title_raw)
				print(episode)
				season_episode = f'E{int(episode):02}'
			new_title = f'{series} - {season_episode} - {s[1]}'
		else:
			new_title = title_raw
			
		# Append date and broadcaster
		new_title = f'{new_title} ({broadcaster}, {date})'

		print(f'----- {new_title}')


		# Replace underscores with dashes surrounded by spaces
#			title_raw = title_raw.replace('_', ' - ')
#			print(f'{title_raw}')
#			title = title_raw
		new_file_name = f'{new_title}{file_ext}'
		print(f'Old filename: {file_name}') 
		print(f'New filename: {new_file_name}') 
	return new_file_name

def run_tests():
	for v in tests:
		expected = tests[v]
		actual = convert_file_name(v)
		if actual != expected:
			print(f'Error converting file: {v}')
			print(f'Expected: {expected}')
			print(f'But got:  {actual}')
if __name__ == '__main__':
	argc = len(sys.argv)
	if argc == 1:
		run_tests()
	else:
		
		### last arg is supposed to be the start folder
		start_dir = sys.argv[-1]
		if not os.path.isdir(start_dir):
			print("{} is not a valid folder".format(start_dir))
			print_usage_and_quit()

	    # Search for all MP3s and extract their Artist/Album path parts
		filelist = []
		for filename in glob.glob(start_dir+'/*.mp4'):
			filelist.append(filename)

		for full_path in filelist:
			# Separate path and filename
			path, file_name = os.path.split(full_path)
			new_file_name = convert_file_name(file_name)
			if not new_file_name:
				print(f'No substitution found for {file_name}')
			else:
				new_full_path = os.path.join(path, new_file_name)
				os.rename(full_path, new_full_path)
