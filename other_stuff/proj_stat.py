#! /usr/bin/python3

import sys, datetime
from html_table_parser import HTMLTableParser

header = ['Date', 'Employee', 'Phase', 'Note', 'Time']
hours_per_day = 8.0


def dump_monthly_table(monthly_table, user_list, use_days = False):

	time_scale = hours_per_day if use_days else 1.0

	longest_username = 0
	for user in user_list:
		if len(user) > longest_username:
			longest_username = len(user)

	str = '_______'
	totals_table = {}
	for user in user_list:
		totals_table[user] = 0.0
		str += ' | {:{width}}'.format(user, width=longest_username)
	str += ' | {:{width}}'.format('Total', width=longest_username)
	print(str)

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

			str += ' | {:{width}.2f}'.format(time / time_scale, width=longest_username)
		str += ' | {:{width}.2f}'.format(monthly_total / time_scale, width=longest_username)
		print(str)
	print()

	str = 'Total: '
	total = 0.0
	for user in user_list:
		time = totals_table[user]
		total += time
		str += ' | {:{width}.2f}'.format(time / time_scale, width=longest_username)
	str += ' | {:{width}.2f}'.format(total / time_scale, width=longest_username)
	print(str)	

def check_table(table):

	total_hours = 0.0
	start_date = None
	end_date = None

	monthly_table = {}
	user_list = []

	for i,line in enumerate(table):

		# skip header
		if i == 0:
			continue

		# detect last line
		if line[0] == 'Total':
			break

		# times from table are in format e.g. '7.00\xa0h'
		time_str = line[table[0].index('Time')]
		date_str = line[table[0].index('Date')]

		user_str = line[table[0].index('Employee')]
		user = user_str.split(',', 1)[0]
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

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Error: Invalid number of arguments.')
		sys.exit()

	infile = sys.argv[1]

	with open(infile, 'r') as file:
	    data = file.read().replace('\n', '')

	p = HTMLTableParser()
	p.feed(data)

	# Search relevant table, normally, it's the second one
	for i,t in enumerate(p.tables):

		ok = True
		for j,s in enumerate(p.tables[i][0]):
			if s != header[j]:
				ok = False

		if ok:
			check_table(p.tables[i])


