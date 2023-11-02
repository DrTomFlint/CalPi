#!/usr/bin/env python3
import sqlite3

database_file = './database/ovenpi8.db'

# create tables
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
        integral REAL
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
db.close()

# create 2 runs with run_data and run_summary
run_number = 1
#         run time     top bottom front back    probe1 probe2 pi ssr     avg setpoint integral command on_time
data1 = [
    (run_number, 1,    50.0,40.0,45.0,45.2,     52.0,53.0,33.0,38.1,     50.5,55.0,54.4,1,0.123),
    (run_number, 2,    51.0,41.0,46.0,46.2,     53.0,54.0,33.1,39.1,     50.6,55.1,54.5,1,0.124),
    (run_number, 3,    52.0,42.0,47.0,47.2,     54.0,55.0,33.2,40.1,     50.7,55.2,54.6,1,0.125),
    (run_number, 4,    53.0,43.0,48.0,48.2,     55.0,56.0,33.3,41.1,     50.8,55.3,54.7,1,0.126),
]
summary1 = (1, '2023-09-12 10:00:00', 'bake a stealie')

run_number = 2
data2 = [
    (run_number, 1,    150.0,140.0,145.0,145.2,     152.0,153.0,43.0,48.1,     150.5,155.0,154.4,1,0.223),
    (run_number, 2,    151.0,141.0,146.0,146.2,     153.0,154.0,43.1,49.1,     150.6,155.1,154.5,1,0.224),
    (run_number, 3,    152.0,142.0,147.0,147.2,     154.0,155.0,43.2,50.1,     150.7,155.2,154.6,1,0.225),
    (run_number, 4,    153.0,143.0,148.0,148.2,     155.0,156.0,43.3,51.1,     150.8,155.3,154.7,1,0.226),
    (run_number, 4,    154.0,144.0,149.0,149.2,     156.0,156.0,43.5,51.2,     150.9,155.4,154.8,1,0.227),
    (run_number, 4,    155.0,145.0,150.0,150.2,     157.0,157.0,43.6,51.3,     151.0,155.5,154.9,1,0.228),
]
summary2 = (run_number, '2023-09-12 11:45:05', 'bake some lovecoins')

# insert data into tables
db = sqlite3.connect(database_file)
cursor = db.cursor()

q_insert_run_data='''
    INSERT INTO run_data (run_number, time, top, bottom, front, back, probe1, probe2, pi, ssr, avg, setpoint, command, integral, on_time)
    VALUES (?,?,?,?,?, ?,?,?,?,?, ?,?,?,?,?)
'''
q_insert_run_summary='''
    INSERT INTO run_summary (run_number, start_time, comment)
    VALUES (?,?,?)
'''

cursor.executemany(q_insert_run_data,data1)
cursor.execute(q_insert_run_summary,summary1)
cursor.executemany(q_insert_run_data,data2)
cursor.execute(q_insert_run_summary,summary2)

db.commit()
db.close()

