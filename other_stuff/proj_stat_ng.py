#! /usr/bin/python3

import sys, datetime
from html_table_parser import HTMLTableParser
from io import StringIO
import re, os
import pandas as pd

debug = False

hours_per_day = 8.0

date_pattern = '[0-9]{4}-[0-9]{2}-[0-9]{2}'
datetime_pattern = '[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}'
datetime_or_null_pattern = '\'[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}\'|NULL'
string_pattern = '.*?'
number_pattern = '[0-9]+'

time_db = {
	'pattern' : r'''
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
		number = number_pattern,
		date = date_pattern,
		datetime = datetime_pattern),
	'header' : ['Date', 'Employee_ID', 'Phase_ID', 'Project_ID', 'Time']
}

employee_db = {
	'pattern' : r'''
		(?P<t_id>{number}),
		'(?P<t_name>{string})',
		'(?P<t_surname>{string})',
		'(?P<t_login>{string})',
		'(?P<t_passwd>{string})',
		(?P<t_unknown>{number}),
		'(?P<t_created>{datetime})',
		'(?P<t_modified>{datetime})',
		(?P<t_del>{number})'''.format(
		number = number_pattern,
		string = string_pattern,
		date = date_pattern,
		datetime = datetime_pattern),
	'header' : ['Employee_ID', 'Username'],
	'table' : []
}

project_db = {
	'pattern' : r'''
		(?P<t_id>{number}),
		'(?P<t_name>{string})',
		(?P<t_customer>{number}),
		(?P<t_employee>{number}),
		'(?P<t_order>{string})',
		'(?P<t_description>{string})',
		(?P<t_start_date>{datetime_or_null}),
		(?P<t_end_date>{datetime_or_null}),
		(?P<t_hours>{number}),
		'(?P<t_status>{string})',
		'(?P<t_created>{datetime})',
		'(?P<t_modified>{datetime})',
		(?P<t_del>{number})'''.format(
		number = number_pattern,
		string = string_pattern,
		date = date_pattern,
		datetime = datetime_pattern,
		datetime_or_null = datetime_or_null_pattern),
	'header' : ['Project_ID', 'Name', 'Description', 'Employee_ID'],
	'table' : []
}

def debug_print(str):
	if debug:
		print(str)

def get_employee_short_by_id(id):
	for i in employee_db['table']:
		if id == i[employee_db['header'].index('Employee_ID')]:
			return i[employee_db['header'].index('Username')]

def get_project_by_id(id):
	for i in project_db['table']:
		if id == i[project_db['header'].index('Project_ID')]:
			return i[project_db['header'].index('Name')]


def dump_monthly_table(monthly_table, user_list, use_days = False):

	time_scale = hours_per_day if use_days else 1.0

	print(user_list)

	# Determine field width based on longest user name, but maintain min. width
	width = 8
	for user in user_list:
		user_str = get_employee_short_by_id(user)
		width = max(len(user_str), width)

	str = '_______'
	totals_table = {}
	for user in user_list:
		totals_table[user] = 0.0
		str += ' | {:{width}}'.format(get_employee_short_by_id(user), width=width)
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

def analyse_project(project_id):

	total_hours = 0.0
	start_date = None
	end_date = None

	monthly_table = {}
	user_list = []

	for i,item in enumerate(time_db['table']):

		debug_print(item)
		if item[time_db['header'].index('Project_ID')] != project_id:
			continue

		# times from table are in format e.g. '7.00\xa0h'
		date_str = item[time_db['header'].index('Date')]
		time = item[time_db['header'].index('Time')]

		user = item[time_db['header'].index('Employee_ID')]
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

		# use month as hash for
		if not month in monthly_table:
			monthly_table[month] = {user : time}
		else:
			if not user in monthly_table[month]:
				monthly_table[month][user] = time
			else:
				monthly_table[month][user] += time

		total_hours += time

	print()
	print('Report for #{} {}'.format(project_id, get_project_by_id(project_id)))
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

# Check whether string is an SQL table. If yes, return a tuple of table title and value string. Otherwise return none.
def check_for_sql_table(str):

	m = re.match('INSERT INTO `(.*)` VALUES (.*);', str)
	if m and len(m.groups()) == 2:
		return m.group(1), m.group(2)
	else:
		return None, None

# Search dump for target_table, note that target_table might be split into several pieces
def read_dump(dump_filename, target_table, transformation_cb):
	table = []
	line_num = 0
	fast_forward = True
	with open(dump_filename, 'rb') as f:
		for line in f:
			line_num += 1
			line = line.decode('utf-8')
			line = line.strip()

			t,v = check_for_sql_table(line)
			if t and v:
				if t == target_table:
					num = split_elements(v, table)
					print('Found table {} at line {} with {} items'.format(target_table, line_num, num))
	if transformation_cb:
		return transformation_cb(table)
	else:
		return table

def transform_project_table(table):
	out_table = []
	num_items = 0
	pattern = project_db['pattern']
	header = project_db['header']
	for item in table:
		print(item)
		m = re.match(pattern, item, re.VERBOSE)
		if m:
			entry = []
			num_items += 1

			for h_item in header:
				if h_item == 'Project_ID':
					entry.append(int(m.group('t_id')))
				elif h_item == 'Employee_ID':
					entry.append(int(m.group('t_employee')))
				elif h_item == 'Name':
					entry.append(m.group('t_name'))
		else:
			print('Failed to match entry')
			print('|{}|'.format(item))
			print('Pattern:')
			print(pattern)
			sys.exit(0)
		out_table.append(entry)
	return out_table

def transform_employee_table(table):
	out_table = []
	num_items = 0
	pattern = employee_db['pattern']
	header = employee_db['header']
	for item in table:
		m = re.match(pattern, item, re.VERBOSE)
		if m:
			entry = []
			num_items += 1

			for h_item in header:
				if h_item == 'Employee_ID':
					entry.append(int(m.group('t_id')))
				elif h_item == 'Username':
					entry.append(m.group('t_login'))
		else:
			print('Failed to match entry')
			print('|{}|'.format(item))
			print('Pattern:')
			print(pattern)
			sys.exit(0)
		out_table.append(entry)
	return out_table

def transform_time_table(table):

	out_table = []
	num_del_items = 0
	num_items = 0
	max_id = 0
	pattern = time_db['pattern']
	header = time_db['header']

	for item in table:
		m = re.match(pattern, item, re.VERBOSE)
		if m:
			entry = []
			num_items += 1

			max_id = max(max_id, int(m.group('t_id')))

			if m.group('t_del') == '1':
				# Found deleted entry
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

		debug_print(entry)
		out_table.append(entry)

	print('{}/{} deleted entries'.format(num_del_items, num_items))
	if num_del_items + len(out_table) != max_id:
		print('Warning: there might be items missing in the table')
	return out_table

def split_elements(str, table):
	start_pos = 0
	sep = ','
	num_elems_found = 0
	is_comment = False
	for i,v in enumerate(str):

		if v == '(':
			if (i == 0) or (str[i-1] == sep):
				# Found start of element
				start_pos = i
		elif v == ')':
			if (i == len(str)-1) or (str[i+1] == sep):
				if not is_comment:
					# Found end of element
					s = str[start_pos+1:i]
					table.append(s)
					num_elems_found += 1
		elif v == "'":
			if (i > 0) and (str[i-1] == '\\'):
				if (i > 1) and (str[i-2] == '\\'):
					# Found double backslash (escaped backslash)
					is_comment = not is_comment
				else:
					# Skip ticks escaped with single backslash
					pass
			else:
				is_comment = not is_comment

	return num_elems_found

def read_activity_table(infile):
	table = read_dump(infile, "activity", None)
	return table

def read_time_table(infile):
	time_db['table'] = read_dump(infile, "time", transform_time_table)

def read_employee_table(infile):
	employee_db['table'] = read_dump(infile, "employee", transform_employee_table)

def read_project_table(infile):
	project_db['table'] = read_dump(infile, "project", transform_project_table)

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print('Error: Invalid number of arguments.')
		print('Usage: {} <sql_file> -p <proj_id>'.format(sys.argv[0]))
		sys.exit()

	infile = sys.argv[1]

	print('\n===========================================\n')

	tables = find_tables(infile)

	read_activity_table(infile)
	read_time_table(infile)
	read_employee_table(infile)
	read_project_table(infile)

	if sys.argv[2] == '-p' and len(sys.argv) > 2:
		proj_id = int(sys.argv[3])
		analyse_project(proj_id)

