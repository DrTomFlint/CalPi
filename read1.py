#====================================================================
# read1.py
# read all the RTDs on the calorimeter
#
# DrTomFlint 2 Nov 2023
#====================================================================

import librtd
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
resist = [0.0]*16           # a single row of raw resistances
temperature = [0.0]*16      # a single row of calibrated temperatures
row1 = [1,0]+temperature

cal_data = []
cal_num = 0
cal_m = [1.0]*16
cal_b = [0.0]*16
cal_coeffs = []

time0 = time.time()
timei = 0.0

# NaN sometimes appears in the temperture readings from librtd?
nan_count = 0

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
#socketio = SocketIO(app, logger=True, engineio_logger=True)

# Make Control C exit properly after turning off the SSRs
def handler(signum,frame):
    print(" ")
    print("Control C detected, exiting calpi.py")
    print(" ")
    exit(1)

signal.signal(signal.SIGINT, handler)

# Create a mutex to prevent interruption of the controller thread
lock = threading.Lock()
	
def emit_data():
    while True:
        with lock:
            json_data = json.dumps(row1)
            
            # Send data to the 'update_chart' event
            socketio.emit('update_chart', json_data)
            #print("emit data {}",json_data)
        
        # Sleep long enough that browser client doesn't overload cpu
        time.sleep(5)

def controller():
    # call out globals that are modified within this function
    global timei
    global nan_count
    global resist
    global temperature
    global row1

    # local vars
    count = 0  
    time1 = 0.0
    time2 = 0.0
    temp = 0

    while True:
        timei = round((1/60)*(time.time()-time0),2)
        count = count + 1      

        # loop over boards (0 and 1) and channels (1 to 8)
        for board in range(2):
            for channel in range(1,9):
                if( (8*board+channel-1) !=11):
                    temp = librtd.get(board,channel)
                else:
                    # broken channel, read one prior instead
                    temp = librtd.get(board,channel-1)
                    
                # if sensor returns NaN don't update the row value
                if(np.isnan(temp)==False):
                    resist[8*board+channel-1] = temp
                    temperature[8*board+channel-1] = cal_m[8*board+channel-1]*temp + cal_b[8*board+channel-1]
                else:
                    nan_count = nan_count+1

                # make a row of data
                row1 = [1, timei]+temperature

        frow1 = [f'{item:.2f}' for item in row1]
        print(', '.join(frow1))
        
        # delay 1 second minus the on_time
        time.sleep(1)
            
#start up threads
t1 = threading.Thread(target=controller,daemon=True)
t1.start()
t2 = threading.Thread(target=emit_data,daemon=True)
t2.start()

def cal_print():
    global cal_data
    global cal_m
    global cal_b
    global cal_coeffs
    global row1

    print('----- cal_data ------')
    print(cal_data)
    print('----- cal_m ------')
    print(cal_m)
    print('----- cal_b ------')
    print(cal_b)
    print('----- cal_coeffs ------')
    print(cal_coeffs)

@socketio.on('cal_add')			
def cal_add(data):
    global cal_data
    global cal_m
    global cal_b
    global cal_coeffs
    global cal_num
    global row1

    print('cal_add')
    cal_num += 1
    temp = [data]+resist
    cal_data.append(temp)
    if cal_num>=2:
        cal_m=[]
        cal_b=[]
        ydata = [col[0] for col in cal_data]
        print(ydata)
        for i in range(16):
            xdata = [col[i+1] for col in cal_data]
            print(xdata)
            m,b = np.polyfit(xdata,ydata,1)
            cal_m.append(m)
            cal_b.append(b)
    
    cal_coeffs = list(zip(cal_m,cal_b))
    cal_print()

@socketio.on('cal_load')			
def cal_load():
    global cal_data
    global cal_m
    global cal_b
    global cal_coeffs
    global row1

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

@socketio.on('cal_save')			
def cal_save():
    global cal_data
    global cal_m
    global cal_b
    global cal_coeffs
    global row1

    print('cal_save')
    # Write the calibration data to a text file
    with open('calibration.txt', 'w') as file:
        for sensor, (m, b) in enumerate(cal_coeffs, start=1):
            file.write(f'Sensor {sensor}: m = {m:.8f}, b = {b:.8f}\n')

    cal_print()

@socketio.on('cal_reset')			
def cal_reset():
    global cal_data
    global cal_m
    global cal_b
    global cal_coeffs
    global row1

    print('cal_reset')
    cal_data=[]
    cal_m=[1.0]*16
    cal_b=[0.0]*16
    cal_coeffs = list(zip(cal_m,cal_b))
    cal_print()

# flask webpage main
@app.route("/")
def index():
    global run_start
    global run_comment
    global emit_refresh
    initial_values = {
    }
    return render_template('read1.html',initial_values=initial_values)

if __name__=="__main__":
#	app.run(host='0.0.0.0',debug=False)
    socketio.run(app,host='0.0.0.0',debug=False)






