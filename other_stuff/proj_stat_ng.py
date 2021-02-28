#! /usr/bin/python3

import sys, datetime
from html_table_parser import HTMLTableParser
from io import StringIO
import re, os
import pandas as pd

header = ['Date', 'Employee_ID', 'Phase_ID', 'Project_ID', 'Note', 'Time']
hours_per_day = 8.0

example_time_table = """INSERT INTO `time` VALUES 
(1,1,1,1,'2010-11-19',2,15,'Besprechung mit Patrick über Motorregler (Test), Pattern','2010-11-19 14:47:32','2010-12-06 13:52:57',1),
(2,1,1,1,'2010-11-12',0,15,'Telefongespräch mit Herrn Knecht über chin. Zeichen.','2010-11-19 14:48:45','2010-12-06 13:52:32',1),
(3,1,1,1,'2010-11-28',3,0,'bla','2010-11-19 14:54:38','2010-12-06 13:53:35',1),
(4,1,1,2,'2010-12-06',1,30,'','2010-12-06 14:47:30','2010-12-06 13:47:30',0),
(1776,731,'Vorbereitung, Durchführung, Nachlese','2020-12-01 09:59:25','2020-12-01 08:59:25',0),
(1857,745,'TCA5 (Intel Atom) Rechner Inbetriebnahme','2021-02-08 13:12:07','2021-02-08 12:12:07',0);
"""

example_time_table2 = """INSERT INTO `time` VALUES (1,1,1,1,'2010-11-19',2,15,'Besprechung mit Patrick über Motorregler','2010-11-19 14:47:32','2010-12-06 13:52:57',1),(2,1,1,1,'2010-11-12',0,15,'Telefongespräch mit Herrn Knecht über chin. Zeichen.','2010-11-19 14:48:45','2010-12-06 13:52:32',1);"""


example_time_table3 = """INSERT INTO `time` VALUES (AAA),(BBB),(CCC);"""

example_time_table4 = """INSERT INTO `time` VALUES (1,1,1,1,'2010-11-19',2,15,'Besprechung mit Patrick über Motorregler','2010-11-19 14:47:32','2010-12-06 13:52:57',1);"""

time_pattern = r'''
(?P<t_id>{number}),
(?P<t_proj>{number}),
(?P<t_phase>{number}),
(?P<t_employee>{number}),
'(?P<t_date>{date})',
(?P<t_hours>{number}),
(?P<t_mins>{number}),
'(?P<t_note>.*?)',
'(?P<t_created>{datetime})',
'(?P<t_modified>{datetime})',
(?P<t_del>{number})'''.format(
number = '[0-9]+',
date = '[0-9]{4}-[0-9]{2}-[0-9]{2}',
datetime = '[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}')

time_table = []

def dump_monthly_table(monthly_table, user_list, use_days = False):

	time_scale = hours_per_day if use_days else 1.0

	# Determine field width based on longest user name, but maintain min. width
	width = 8
	for user in user_list:
		if len(user) > width:
			width = len(user)

	str = '_______'
	totals_table = {}
	for user in user_list:
		totals_table[user] = 0.0
		str += ' | {:{width}}'.format(user, width=width)
	str += ' | {:{width}}'.format('Total', width=width)
	str += ' | {:{width}}'.format('Cumul.', width=width)
	print(str)

	cum_monthly_total = 0.0

	for month in monthly_table:
		monthly_total = 0.0
		str = month
		for user in user_list:
			if user in monthly_table[month]:
				time = monthly_table[month][user]
			else:
				time = 0.0

			monthly_total += time
			totals_table[user] += time

			str += ' | {:{width}.2f}'.format(time / time_scale, width=width)
		cum_monthly_total += monthly_total
		str += ' | {:{width}.2f}'.format(monthly_total / time_scale, width=width)
		str += ' | {:{width}.2f}'.format(cum_monthly_total / time_scale, width=width)
		print(str)
	print()

	str = 'Total: '
	total = 0.0
	for user in user_list:
		time = totals_table[user]
		total += time
		str += ' | {:{width}.2f}'.format(time / time_scale, width=width)
	str += ' | {:{width}.2f}'.format(total / time_scale, width=width)
	str += ' | {:{width}.2f}'.format(cum_monthly_total / time_scale, width=width)
	print(str)	

def analyse_project(table, project_id):

	total_hours = 0.0
	start_date = None
	end_date = None

	monthly_table = {}
	user_list = []

	for i,item in enumerate(table):

		print(item)
		if item[header.index('Project_ID')] != project_id:
			continue


		# times from table are in format e.g. '7.00\xa0h'
		time_str = item[header.index('Time')]
		date_str = item[header.index('Date')]

		user_str = item[header.index('Employee')]
		user = item['user']
		if user not in user_list:
			user_list.append(user)

		date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
		month = date.strftime('%Y-%m')

		if not start_date:
			start_date = date
		else:
			if date < start_date:
				start_date = date

		if not end_date:
			end_date = date
		else:
			if date > end_date:
				end_date = date

		time = float(time_str.split('\xa0', 1)[0])

		# use month as hash for
		if not month in monthly_table:
			monthly_table[month] = {user : time}
		else:
			if not user in monthly_table[month]:
				monthly_table[month][user] = time
			else:
				monthly_table[month][user] += time

		total_hours += time

	print('Total: {} h, {} d'.format(total_hours, total_hours / hours_per_day))
	print('Start: {}'.format(start_date))
	print('End:   {}'.format(end_date))

	print()
	print('Overview (hours)')
	dump_monthly_table(monthly_table, user_list, False)

	print()
	print('Overview (days)')
	dump_monthly_table(monthly_table, user_list, True)




def find_tables(dump_filename):
	line_num = 0
	tables = []
	with open(dump_filename, 'rb') as f:
		print('Tables:')
		for line in f:
			line_num += 1
			line = line.decode('latin-1')
			line = line.strip()


			m = re.match('INSERT INTO `(.*)` VALUES (.*)', line)
			if m:
				table_title = m.group(1)
				print('Line {}: {}'.format(line_num, table_title))
				tables.append(table_title)

	return tables


# Generate a pattern to separate elements
def generate_pattern(num_items):

	p = "\("
	for i in range(num_items):
		p += ".*?"
		if i < num_items-1:
			p += ","
	p += "\)"
	return p

def sql_table_to_list(vals, table_type, table):

	num_items = 0

	print('sql')
#	m = re.findall("(\(.*?\))[,;]", vals)
	pattern = None

	if table_type == 'time':
		pat = generate_pattern(11)
		pattern = time_pattern5


	else:
		print('Unable to handle table {}'.format(table_type))
		return 0

	print('Search pattern: {}'.format(pat))

	# Split table into elements
	m = re.findall(pat, vals)
	print('{} entries'.format(len(m)))
	for e in m:
		print(e)

		# Split elements into values
		if pattern:
			m = re.findall(pattern, e, re.VERBOSE)
			for v in m:
				print(v)	
				table.append(v)

# Check whether string is an SQL table. If yes, return a tuple of table title and value string. Otherwise return none.
def check_for_sql_table(str):

	m = re.match('INSERT INTO `(.*)` VALUES (.*);', str)
	if m and len(m.groups()) == 2:
		return m.group(1), m.group(2)
	else:
		return None, None

def get_entries(str, table_type):

	table = []
	str = str.replace('\n','')

	m = re.match('INSERT INTO `(.*)` VALUES (.*);', str)
	print("-----------------------X---------------------------")

	if m and len(m.groups()) > 1:
		print('found')
		print('len: {}'.format(len(m.groups())))

		table_title = m.group(1)
		table_values = m.group(2)
		print(table_values)
		sql_table_to_list(table_values, table_type, table)

# Search dump for target_table, note that target_table might be split into several pieces
def read_dump(dump_filename, target_table):
	table = []
	line_num = 0
	fast_forward = True
	print('reading dump')
	with open(dump_filename, 'rb') as f:
		for line in f:
			line_num += 1
			line = line.decode('utf-8')
			line = line.strip()

			t,v = check_for_sql_table(line)
			if t and v:
				print('found')
				if t == target_table:
					num = split_elements(v, table)
#					num = sql_table_to_list(v, target_table, table)
					print('Found table {} at line {} with {} items'.format(target_table, line_num, num))
	return table

def transform_time_table(table):

	out_table = []
	num_del_items = 0
	num_items = 0

	pattern = time_pattern

	for item in table:
		m = re.match(pattern, item, re.VERBOSE)
		if m:
			entry = []
			num_items += 1

			if m.group('t_del') == '1':
				print('Found deleted entry')
				num_del_items += 1
				continue

			for h_item in header:
				if h_item == 'Project_ID':
					entry.append(int(m.group('t_proj')))
				elif h_item == 'Phase_ID':
					entry.append(int(m.group('t_phase')))
				elif h_item == 'Employee_ID':
					entry.append(int(m.group('t_employee')))
				elif h_item == 'Time':
					h = int(m.group('t_hours'))
					m = int(m.group('t_mins'))
					t = h + m/60
					entry.append(t)
				elif h_item == 'Date':
					entry.append(m.group('t_date'))
		else:
			print('Failed to match entry')
			print('|{}|'.format(item))
			print('Pattern:')
			print(pattern)
			sys.exit(0)

			print(entry)
			out_table.append(entry)

	print('{}/{} deleted entries'.format(num_del_items, num_items))
	return out_table





def split_elements_old(str, table):

	start_pos = 0
	sep = ','
	depth = 0
	num_elems_found = 0
	for i,v in enumerate(str):

		if v == '(':
			if depth == 0:
				start_pos = i
			depth += 1
		elif v == ')':
			depth -= 1
			if depth == 0:
				# Found end of element
				s = str[start_pos+1:i]
				table.append(s)
				num_elems_found += 1
		else:
			if depth == 0:
				# Outside of bracket, only separator is expected
				if v != sep:
	#				print('Warning: separator not found')
					pass

	return num_elems_found

def split_elements(str, table):



	start_pos = 0
	sep = ','
	num_elems_found = 0
	is_comment = False
	for i,v in enumerate(str):

		if v == '(':
			if (i == 0) or (str[i-1] == sep):
				start_pos = i
		elif v == ')':
			if (i == len(str)-1) or (str[i+1] == sep):
				if not is_comment:
					# Found end of element
					s = str[start_pos+1:i]
					table.append(s)
					num_elems_found += 1
					print('end at {}'.format(i))
					print('strlen: {}'.format(len(str)))

					print(s)
					m = re.match(time_pattern, s, re.VERBOSE)
					if not m:
						print('mismatch:')
						print('is_comment: {}'.format(is_comment))
						sys.exit(0)

		elif v == "'":
			if (i > 0) and (str[i-1] == '\\'):
				if (i > 1) and (str[i-2] == '\\'):
					print('found double backslash, i: {}, offset: {}, str: {}'.format(i, i-start_pos, str[start_pos:i+20]))
					is_comment = not is_comment
					pass # backslash escaped with another backslash
				else:
					print('found single tick, i: {}, offset: {}, str: {}'.format(i, i-start_pos, str[start_pos:i+20]))
					# Skip ticks escaped with single backslash
					pass
			else:
				is_comment = not is_comment

	return num_elems_found


def extract_proj_table():
#'''
#	Extract project table from HTML file generated by Time. Make sure, that no filters are set.
#	I.e. do not select any employees or phases and leave start/end date on defaults.
#'''
	print()

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Error: Invalid number of arguments.')
		sys.exit()

	infile = sys.argv[1]

	print('\n===========================================\n')

#	get_entries(example_time_table2, 'time')

	print('\n===========================================\n')



	table = []
	s = "(930,53,90,6,'2011-11-01',8,0,'Einarbeiten in Maschinencode - wieder einmal gar nicht so einfach wie gedacht...','2011-11-01 19:26:49','2011-11-01 18:26:49',0),(931,52,91,5,'2011-11-01',3,0,'Testaufbau (mit I-Base Simulator), HW-Testschuss Debugging','2011-11-02 12:08:33','2011-11-02 11:08:33',0)"
	print(s)
	split_elements(s, table)
	print(table)

	table = []
	s = "(1232,54,118,5,'2011-11-21',4,0,'Aufwandschätzung Update auf V1.2','2011-12-21 17:37:25','2011-12-21 16:37:25',0),(1233,59,106,5,'2011-11-21',4,30,'Erstellen einer ersten Test Applikation auf dem Eval Board (STM3220G-EVAL), d. h. Makefile, Liker Script, BDI, ...','2011-12-21 17:41:33','2011-12-21 16:41:33',0),(1234,59,106,5,'2011-11-22',9,15,'dito','2011-12-21 17:42:02','2011-12-21 16:42:02',0),(1235,59,106,5,'2011-11-23',8,45,'Test USB Test Applikation (HID Device)','2011-12-21 17:42:54','2011-12-21 16:42:54',0)"

	print(s)
	split_elements(s, table)
	for t in table:
		print(t)
		m = re.match(time_pattern, t, re.VERBOSE)
		print(m)

#	sys.exit(0)


	tables = find_tables(infile)
	print(tables)

#	act_table = read_dump(infile, "activity")
#	print(len(act_table))
#	print(act_table)

	time_table_raw = read_dump(infile, "time")
	print(len(time_table))

	time_table = transform_time_table(time_table_raw)

	print('\n--- XXX ----------------------------------------\n')


	analyse_project(time_table, 722)

