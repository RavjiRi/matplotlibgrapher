"""
An easy to use non-blocking matplotlib grapher.

This program was written so that graphs can be plotted in real time in Python.
The matplotlib library provides a plot function which is well made, but the show function is blocking.
Using threads does not work as matplotlib is not thread safe...
and multiprocessing requires the main script importing the library to have a main guard which is unhelpful.
So this library creates the plot using a subprocess and uses signals and xmlrpc to communicate data.

HOW TO USE THIS

Version: 4/3/25

Author: RavjiRi
"""
from threading import Event as _Event, Thread as _Thread, main_thread as _main_thread
from signal import signal as _signal, SIGUSR1 as _SIGUSR1
from subprocess import Popen as _Popen, PIPE as _PIPE
from xmlrpc.client import ServerProxy as _ServerProxy
from pathlib import Path as _Path
from time import sleep as _sleep
import sys as _sys

# configuration variables
_sync_frequency = 0.1 # how often to send the plot points to subprocess
_DEBUG = False
_isIDLE = True

# create client proxy object
_proxy = _ServerProxy("http://127.0.0.1:8000/")

_stdout = _sys.stdout
# using sys.stdout does not work on IDLE as it is replaced with another object
if _isIDLE:
    _stdout = _PIPE

subprocess_ready = _Event()

# set the threading event when the user defined signal is sent from the child process
# n, frame = signal number, current stack frame though these are unused
_signal(_SIGUSR1, lambda n, frame: subprocess_ready.set())

process_dir = _Path(__file__).parent/'graphprocess.py'
# using python3 doesn't work because it will open an older version than more recent version with pip
p = _Popen(['/Library/Frameworks/Python.framework/Versions/3.13/bin/python3', process_dir], stdin=_PIPE, stdout=_sys.__stdout__, stderr=_sys.__stdout__)
# wait for subprocess to startup the server
# this will wait until the signal is sent from which the event is set
subprocess_ready.wait()
# cleanup event object
del subprocess_ready

_data_points = []  # store plot points that are about to be sent
# send plot points with this function
def _sync_send():
    # send data points to subprocess
    while _main_thread().is_alive():
        if _DEBUG:
            print('sending')
        _proxy.send_data(_data_points)
        # clear the list, do not set to an empty list
        # otherwise the list pointer is overwritten and a global variable is needed
        _data_points.clear()
        _sleep(_sync_frequency)

# exposed function to add data point to the plot
def plot(x: int | float, y: int | float):
    _data_points.append((x, y))

# create a new thread and start
_sync_thread = _Thread(target=_sync_send)
_sync_thread.start()

# demo if not imported
if __name__ == "__main__":
    count = 0
    while True:
        count+=1

        _data_points.append((count, count+1))
        _sleep(0.00001)
