#!/usr/bin/env python3
import sqlite3

# connect to database and get a cursor
db = sqlite3.connect('./database/ovenpi8.db')

# fetch out the last run number
cursor = db.cursor()

q_read_run_number = '''
    SELECT *
    FROM run_summary
    ORDER BY run_number DESC
'''

cursor.execute(q_read_run_number)
row = cursor.fetchone()
print('last run number was: ',row[1])
last_run = row[1]

# print out test summaries
cursor = db.cursor()

q_read_summary = '''
    SELECT *
    FROM run_summary
'''

cursor.execute(q_read_summary)
row = cursor.fetchone()
print('---------------------------------------------------')
while row:
    print(f'run number {row[1]} started at {row[2]}, {row[3]}')
    row = cursor.fetchone()

# print out test data
q_read_data = '''
    SELECT *
    FROM run_data
    WHERE run_number = ?
'''

data_titles=['run','time','top','bottom','front','back','probe1','probe2','pi','ssr','avg','set','cmd','integral','on_time']
for run_number in range(1,last_run+1):
    print('---------------------------------------------------')
    print('{:>4}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}{:>9}'.format(*data_titles))
    cursor.execute(q_read_data,str(run_number))

    row = cursor.fetchone()
    while row:
        print('{:>4}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.1f}{:>9.3f}'.format(*row[1:]))
        row = cursor.fetchone()

# done so close database
db.close()
