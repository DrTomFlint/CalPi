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
row1 = [1,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]      # a single row of data
data1 = []      # append row onto a larger table
caldata = []

on_time = 0
timecount = 0
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
    global row1

    # local vars
    count = 0  
    time1 = 0.0
    time2 = 0.0
    temp = 0

    while True:
        row1[0] = 1
        timei = round((1/60)*(time.time()-time0),2)
        row1[1] = timei
        count = count + 1      

        # loop over boards (0 and 1) and channels (1 to 8)
        for board in range(2):
            for channel in range(1,9):
                if( (2+8*board+channel-1) !=13):
                    temp = librtd.get(board,channel)
                else:
                    # broken channel, read one prior instead
                    temp = librtd.get(board,channel-1)
                    
                # if sensor returns NaN don't update the row value
                if(np.isnan(temp)==False):
                    row1[2+8*board+channel-1]=temp
                else:
                    nan_count = nan_count+1

        frow1 = [f'{item:.2f}' for item in row1]
        print(', '.join(frow1))
        
        # delay 1 second minus the on_time
        time.sleep(1)
            
#start up threads
t1 = threading.Thread(target=controller,daemon=True)
t1.start()
t2 = threading.Thread(target=emit_data,daemon=True)
t2.start()

@socketio.on('update_calpoint')			
def update_cal(data):
    global caldata
    global calm
    global calb
    global row1
    
    temp = [data]+row1[2:]
    caldata.append(temp)
    print(temp)
    print(caldata)
    calm=[]
    calb=[]
    ydata = [col[0] for col in caldata]
    print(ydata)
    for i in range(16):
        xdata = [col[i+1] for col in caldata]
        print(xdata)
        m,b = np.polyfit(xdata,ydata,1)
        calm.append(m)
        calb.append(b)
    
    print(calm)
    print(calb)

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






