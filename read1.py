#====================================================================
# read1.py
# read all the RTDs on the calorimeter
#
# DrTomFlint 2 Nov 2023
#====================================================================

import librtd
import libioplus
import RPi.GPIO as GPIO
import scurve
import time
import signal
import json
from datetime import datetime
from flask import Flask, Response, render_template, stream_with_context
from flask_socketio import SocketIO, emit
import threading
import random
import numpy as np
import sql

# globals to hold current readings and command
temperature = [0.0]*16      # a single row of calibrated temperatures
adc = [0.0]*8               # a single row of adc readings
row1 = [1,0]+temperature

cal_y0 = [0.0]*16
cal_y1 = [0.0]*16
cal0 = 0.0
cal1 = 0.0
cal_m = [1.0]*16
cal_b = [0.0]*16
cal_coeffs = []

time0 = time.time()
timei = 0.0
nan_count = 0       # NaN sometimes appears in the temperture readings from librtd
onoff = 0

database_file = './database/read1.db'
db = sql.open(database_file)
run_number = sql.read_last_run_number(db)
run_start = sql.read_last_run_start(db)
run_comment = sql.read_last_run_comment(db)
emit_refresh = False
if run_number>0:
    emit_refresh = True

print(f'STARTUP: last test {run_number} started at {run_start}, comment: {run_comment}')

# Create a mutex to prevent interruption of the controller thread
lock = threading.Lock()

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
#socketio = SocketIO(app, logger=True, engineio_logger=True)

#-----------------------------------------------------------------------	
# Make Control C exit properly after turning off the SSRs
def handler(signum,frame):
    print(" ")
    print("Control C detected, exiting calpi.py")
    print(" ")
    exit(1)

signal.signal(signal.SIGINT, handler)

#-----------------------------------------------------------------------	
def emit_data():
    while True:
        with lock:
            json_data = json.dumps(row1)
            
            # Send data to the 'update_chart' event
            socketio.emit('update_chart', json_data)
            #print("emit data {}",json_data)
        
        # Sleep long enough that browser client doesn't overload cpu
        time.sleep(5)

#-----------------------------------------------------------------------	
def controller():
    # call out globals that are modified within this function
    global timei
    global nan_count
    global temperature
    global row1
    global cal_m
    global cal_b

    # local vars
    count = 0  
    time1 = 0.0
    time2 = 0.0
    temp = 0

    while True:
        with lock:
            timei = round((1/60)*(time.time()-time0),2)
            count = count + 1      

            # loop over boards (0 and 1) and channels (1 to 8)
            for board in range(2):
                for channel in range(1,9):
                    temp = librtd.get(board,channel)                    
                    # if sensor returns NaN don't update the temperature value
                    if(np.isnan(temp)==False):
                        temperature[8*board+channel-1] = (temp - cal_b[8*board+channel-1]) / cal_m[8*board+channel-1]
                    else:
                        nan_count = nan_count+1

            for channel in range(1,9):
                adc[channel-1] = libioplus.getAdcV(2,channel)

            # make a row of data
            row1 = [run_number, timei]+temperature+adc

            frow1 = [f'{item:.2f}' for item in row1]
            print(', '.join(frow1))
            
        # delay 1 second minus the on_time
        time.sleep(1)

#-----------------------------------------------------------------------	
def record_data():
    global row1
    db2 = sql.open(database_file)    
    while True:
        if onoff:
            with lock:
                sql.insert_run_data(db2,row1)
        time.sleep(5)

#-----------------------------------------------------------------------	
#start up threads
t1 = threading.Thread(target=controller,daemon=True)
t1.start()
t2 = threading.Thread(target=emit_data,daemon=True)
t2.start()
t3 = threading.Thread(target=record_data,daemon=True)
t3.start()

#-----------------------------------------------------------------------	
@socketio.on('update_onoff')			
def update_onoff(data,run_comment):
    global onoff
    global time0
    global run_number
    global run_start
    print("Update on/off to ",data)
    if data==True:
        time0=time.time()
        run_number+=1
        db3=sql.open(database_file)
        run_start=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print('starting test %2d at %s, comment = %s' % (run_number,run_start,run_comment))
        sql.insert_run_summary(db3,(run_number,run_start,run_comment))
    onoff = data

#-----------------------------------------------------------------------	
def cal_print():
    global cal_y0
    global cal_y1
    global cal_m
    global cal_b
    global cal_coeffs

    print('----- cal0 ------')
    print(cal0)
    print('----- cal1 ------')
    print(cal1)
    print('----- cal_y0 ------')
    print(cal_y0)
    print('----- cal_y1 ------')
    print(cal_y1)
    print('----- cal_m ------')
    print(cal_m)
    print('----- cal_b ------')
    print(cal_b)
    print('----- cal_coeffs ------')
    print(cal_coeffs)

#-----------------------------------------------------------------------	
@socketio.on('cal_zero')			
def cal_zero():
    global cal_y0
    global cal0
    global temperature

    print('cal_zero')
    cal_y0 = temperature.copy()
    cal0 = np.mean(cal_y0)
    cal_print()

#-----------------------------------------------------------------------	
@socketio.on('cal_one')			
def cal_one():
    global cal_y0
    global cal_y1
    global cal_coeffs
    global cal0
    global cal1
    global temperature

    print('cal_one')
    cal_y1 = temperature.copy()

    cal1 = np.mean(cal_y1)
    print(f'Calibration point means {cal0:.4f}, {cal1:.4f}')

    for i in range(16):
        cal_m[i] = (cal_y1[i]-cal_y0[i]) / (cal1-cal0)
        cal_b[i] = cal_y0[i] - cal_m[i] * cal0
    cal_coeffs = list(zip(cal_m,cal_b))
    cal_print()

#-----------------------------------------------------------------------	
@socketio.on('cal_load')			
def cal_load():
    global cal_m
    global cal_b
    global cal_coeffs

    cal_coeffs = []

    # Read the calibration data from the text file
    with open('calibration.txt', 'r') as file:
        for line in file:
            if line.startswith('Sensor'):
                # Extract m and b values from the line and append to the list
                parts = line.split()
                m = float(parts[4].strip(','))  # Extract and convert m
                b = float(parts[7])            # Extract and convert b
                cal_coeffs.append((m, b))

    # Split the combined_list into list1 and list2
    cal_m, cal_b = zip(*cal_coeffs)

    # Convert the results to lists
    cal_m = list(cal_m)
    cal_b = list(cal_b)
    cal_print()

#-----------------------------------------------------------------------	
@socketio.on('cal_save')			
def cal_save():
    global cal_m
    global cal_b
    global cal0
    global cal1
    global cal_coeffs

    print('cal_save')
    # Write the calibration data to a text file
    cal_coeffs = list(zip(cal_m,cal_b))
    with open('calibration.txt', 'w') as file:
        file.write(f'Calibration done {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        file.write(f'with cal0 = {cal0:.4f} and cal1 = {cal1:.4f}\n')
        for sensor, (m, b) in enumerate(cal_coeffs, start=1):
            file.write(f'Sensor {sensor}: m = {m:.8f}, b = {b:.8f}\n')

    cal_print()

#-----------------------------------------------------------------------	
@socketio.on('cal_reset')			
def cal_reset():
    global cal_m
    global cal_b
    global cal0
    global cal1
    global cal_coeffs

    print('cal_reset')
    cal_m=[1.0]*16
    cal_b=[0.0]*16
    cal0 = 0.0
    cal1 = 0.0
    cal_coeffs = list(zip(cal_m,cal_b))
    cal_print()

#-----------------------------------------------------------------------	
# flask webpage main
@app.route("/")
def index():
    global run_start
    global run_comment
    global emit_refresh
    initial_values = {
    }
    return render_template('read2.html',initial_values=initial_values)

if __name__=="__main__":
#	app.run(host='0.0.0.0',debug=False)
    socketio.run(app,host='0.0.0.0',debug=False)






