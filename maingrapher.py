"""
An easy to use non-blocking matplotlib grapher.

This program was written so that graphs can be plotted in real time in Python.
The matplotlib library provides a plot function which is well made, but the show function is blocking.
Using threads does not work as matplotlib is not thread safe...
and multiprocessing requires the main script importing the library to have a main guard which is unhelpful.
So this library creates the plot using a subprocess and uses signals and xmlrpc to communicate data.

Run this by import, this was made to work for the apple mac.

Version: 10/3/25

Author: RavjiRi
"""
from threading import Event as _Event, Thread as _Thread, main_thread as _main_thread
from signal import signal as _signal, SIGUSR1 as _SIGUSR1
from subprocess import Popen as _Popen, PIPE as _PIPE
from xmlrpc.client import ServerProxy as _ServerProxy
from json import dumps as _dumps
from pathlib import Path as _Path
from time import sleep as _sleep
import sys as _sys

# configuration variables
_sync_frequency = 0.1 # how often to send the plot points to subprocess
_DEBUG = False
_isIDLE = True
_ADDRESS = 'http://127.0.0.1:' # local host broadcast address
class configuration():
    pass
configs = configuration()
configs.PORT = 8000 # python requests port, can use any UNPRIVLEDGED port

_data_points = []  # store plot points that are about to be sent
def _sync_send(proxy: _ServerProxy):
    '''Send data points to subprocess.

    The secondary thread calls this function and starts a loop
    This sends plot points from the XMLRPC client to the server on the subprocess

    Args:
        proxy (xmlrpc.client.ServerProxy): the XMLRPC client proxy to send data over
    Returns:
        None
    '''
    while _main_thread().is_alive():
        if _DEBUG:
            print('sending')
        # send the data in JSON format
        # XML RPC doesn't support large numbers due to overflow error
        # sending a large string works however
        proxy.send_data(_dumps(_data_points))
        # clear the list, do not set to an empty list
        # otherwise the list pointer is overwritten and a global variable is needed
        _data_points.clear()
        _sleep(_sync_frequency)

# exposed function to add data point to the plot
def plot(x: int | float, y: int | float):
    '''Add data point to the plot.

    This adds a data point to the data points variable
    The points will wait to be sent to the server subprocess

    Args:
        x (int | float): the x coordinate
        y (int | float): the y coordinate
    Returns:
        None
    '''
    _data_points.append((x, y))

def start():
    '''Start the module.

    This starts server subprocess which handles the matplotlib graph and the threads

    Args:
        None
    Returns:
        None
    '''
    # create client proxy object
    proxy = _ServerProxy(_ADDRESS + str(configs.PORT))

    subprocess_ready = _Event()

    # set the threading event when the user defined signal is sent from the child process
    # n, frame = signal number, current stack frame though these are unused
    _signal(_SIGUSR1, lambda n, frame: subprocess_ready.set())

    # this means graphprocess.py will have to be in the same directory as maingrapher.py
    process_dir = _Path(__file__).parent/'graphprocess.py'
    # using python3 doesn't work because it will open an older version than more recent version with pip
    p = _Popen(['/Library/Frameworks/Python.framework/Versions/3.13/bin/python3',
                process_dir, str(configs.PORT)],
                stdin=_PIPE, stdout=_sys.__stdout__, stderr=_sys.__stdout__)
    # wait for subprocess to startup the server
    # this will wait until the signal is sent from which the event is set
    subprocess_ready.wait()
    # cleanup event object
    del subprocess_ready

    # create a new thread and start
    sync_thread = _Thread(target=_sync_send, args=(proxy,))
    sync_thread.start()

# demo if not imported
if __name__ == "__main__":
    start()
    count = 0
    while True:
        count+=1

        _data_points.append((count, count+1))
        _sleep(0.00001)
