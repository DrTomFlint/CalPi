#=========================================================================================
# sql.py
#
#
# DrTomFlint 22 Sept 2023
#=========================================================================================

import sqlite3
import json

#-----------------------------------------------------------------------------------------
def open(database_file):
    db = sqlite3.connect(database_file)
    cursor = db.cursor()
    q_create_run_data ='''
        CREATE TABLE IF NOT EXISTS run_data(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            run_number INTEGER,
            time REAL,
            top REAL,
            bottom REAL,
            front REAL,
            back REAL,
            probe1 REAL,
            probe2 REAL,
            pi REAL,
            ssr REAL,
            avg REAL,
            setpoint REAL,
            command REAL,
            integral REAL,
            on_time REAL,
            FOREIGN KEY (run_number) REFERENCES run_summary(run_number)
        )'''

    cursor.execute(q_create_run_data)

    q_create_run_summary ='''
        CREATE TABLE IF NOT EXISTS run_summary(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            run_number INTEGER,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            comment TEXT
        )'''

    cursor.execute(q_create_run_summary)

    db.commit()
    return db

#-----------------------------------------------------------------------------------------
def close(db):
    db.close()

#-----------------------------------------------------------------------------------------
def read_last_run_number(db):

    cursor = db.cursor()

    q_read_run_number = '''
        SELECT *
        FROM run_summary
        ORDER BY run_number DESC
    '''

    cursor.execute(q_read_run_number)
    row = cursor.fetchone()
    if row:
        return row[1]
    else:
        return 0

#-----------------------------------------------------------------------------------------
def read_last_run_start(db):

    cursor = db.cursor()

    q_read_run_number = '''
        SELECT *
        FROM run_summary
        ORDER BY run_number DESC
    '''

    cursor.execute(q_read_run_number)
    row = cursor.fetchone()
    if row:
        return row[2]
    else:
        return 'never'


#-----------------------------------------------------------------------------------------
def read_last_run_comment(db):

    cursor = db.cursor()

    q_read_run_number = '''
        SELECT *
        FROM run_summary
        ORDER BY run_number DESC
    '''

    cursor.execute(q_read_run_number)
    row = cursor.fetchone()
    if row:
        return row[3]
    else:
        return 'comment'

#-----------------------------------------------------------------------------------------
def insert_run_data(db,data):

    cursor = db.cursor()

    q_insert_run_data='''
        INSERT INTO run_data (run_number, time, top, bottom, front, back, probe1, probe2, pi, ssr, avg, setpoint, command, integral, on_time)
        VALUES (?,?,?,?,?, ?,?,?,?,?, ?,?,?,?,?)
    '''

    cursor.execute(q_insert_run_data,data)
    db.commit()

#-----------------------------------------------------------------------------------------
def insert_run_summary(db,data):

    cursor = db.cursor()

    q_insert_run_summary='''
        INSERT INTO run_summary (run_number, start_time, comment)
        VALUES (?,?,?)
    '''

    cursor.execute(q_insert_run_summary,data)
    db.commit()

#-----------------------------------------------------------------------------------------
def read_run_data(db,run_number):
    
    cursor = db.cursor()

    q_read_run_data='''
        SELECT * FROM run_data
         WHERE run_number = ?
    '''
    
    # Fetch data from the run_data table
    cursor.execute(q_read_run_data,str(run_number))
    data = cursor.fetchall()

    print('read db for test',run_number)
    if data:
        return data
    else:
        return []


#=========================================================================================
