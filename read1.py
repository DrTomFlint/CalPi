#====================================================================
# read1.py
#
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
top = 0.0
bottom = 0.0
front = 0.0
back = 0.0
left = 0.0
right = 0.0
spare1 = 0.0
spare2 = 0.0

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
            json_data = json.dumps(
            {'time':round(timei,0),
            'top':top,'bottom':bottom,
            'front':front,'back':back,
            'left':left,'right':right,
            'spare1':spare1,'spare2':spare2
            })
            
            # Send data to the 'update_chart' event
            socketio.emit('update_chart', json_data)
            #print("emit data {}",json_data)
        
        # Sleep long enough that browser client doesn't overload cpu
        time.sleep(5)

def controller():
    # call out globals that are modified within this function
    global timei
    global top
    global bottom
    global front
    global back
    global left
    global right
    global spare1
    global spare2
    global nan_count

    # local vars
    count = 0  
    time1 = 0.0
    time2 = 0.0
    temp = 0

    while True:
        count = count + 1       # cycle counter for debug

        # read sensors and protect from NaN
        timei = (1/60)*(time.time()-time0)
        temp = librtd.get(0,6)
        if(np.isnan(temp)==False):
            top = temp
        else:
            nan_count = nan_count+1

        temp = librtd.get(0,3)
        if(np.isnan(temp)==False):
            bottom = temp
        else:
            nan_count = nan_count+1

        temp = librtd.get(0,7)
        if(np.isnan(temp)==False):
            front = temp
        else:
            nan_count = nan_count+1

        temp = librtd.get(0,4)
        if(np.isnan(temp)==False):
            back = temp
        else:
            nan_count = nan_count+1        

        temp = librtd.get(0,8)
        if(np.isnan(temp)==False):
            left = temp
        else:
            nan_count = nan_count+1
        temp = librtd.get(0,5)
        if(np.isnan(temp)==False):
            right = temp
        else:
            nan_count = nan_count+1

        temp = librtd.get(0,1)
        if(np.isnan(temp)==False):
            spare1 = temp
        else:
            nan_count = nan_count+1
            
        temp = librtd.get(0,2)
        if(np.isnan(temp)==False):
            spare2 = temp
        else:
            nan_count = nan_count+1

        print("%5d: time=%5.2f top=%5.2f  bottom=%5.2f  front=%5.2f  back=%5.2f    left=%5.2f  right=%5.2f  spare1=%5.2f  spare2=%5.2f nan_count=%3d" % 
              (count, timei, top,  bottom,   front,  back,  left, right, spare1, spare2, nan_count), flush=True)
        
        # delay 1 second minus the on_time
        time.sleep(1-on_time)
            
#start up threads
t1 = threading.Thread(target=controller,daemon=True)
t1.start()
t2 = threading.Thread(target=emit_data,daemon=True)
t2.start()

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






