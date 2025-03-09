"""
The graphing subprocess helper.

This is called by the main script in a subprocess.
There are two threads in this process:
    - The main thread with the matplotlib graph
    - The xmlrpc server receiving data

This is not intended to run by itself.

Version: 10/3/25

Author: RavjiRi
"""
from xmlrpc.server import SimpleXMLRPCServer
from argparse import ArgumentParser
from json import loads
from threading import Thread
from signal import SIGUSR1
from subprocess import run
from random import randint
import sys
import os

sys.path.append('/Users/ritesh.ravji/Documents/libraries')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# configuration variables
_plot_rate = 1 # how often matplotlib animation function is called to plot points (ms)
_DEBUG = False
PLOT_COLOUR = (0, 0, 1) # the plot colour
parser = ArgumentParser()
parser.add_argument('PORT') # first argument is port arg
args = parser.parse_args()
PORT = int(args.PORT)

def process_running(pid: int):
    '''Check if a process is running.

    This calls the command line command ps to get all running processes
    The result is then filtered with the grep command to see if the process is running or not

    Args:
        pid (int): the process id to check
    Returns:
        None
    '''
    strpid = str(pid)
    p = run(['ps', '-e'], capture_output=True) # get all running processes
    # count how many processes are with the pid
    # uses a trick that encloses the first number in brackets so this grep command isn't counted
    p = run(['grep', '-c', "[{}]{}".format(strpid[0], strpid[1:])], capture_output=True, input=p.stdout)
    return not (int(p.stdout) == 0) # if there are no processes return false, else return true

_data_points = [] # store plot points that are sent
def _on_data_recieved(data_sent: list):
    '''Extend sent data to data points list.

    Args:
        data_sent (list): the data sent from the main process
    Returns:
        None
    '''
    # extend sent data to data points list
    # convert from JSON format
    _data_points.extend(loads(data_sent))
    return True

# create XML RPC server at localhost:8000 (broadcast address)
_server = SimpleXMLRPCServer(("127.0.0.1", PORT), logRequests=False)
_server.register_function(_on_data_recieved, "send_data")
if _DEBUG:
    print("Graph server is running")

# start server in another thread as it is blocking
_server_thread = Thread(target=_server.serve_forever)
_server_thread.daemon = True
_server_thread.start()

# get the parent process id
_ppid = os.getppid()
# send user defined signal to the parent process to say server is ready
os.kill(_ppid, SIGUSR1)

def animate(i, x_points, y_points, plt, ax):
    '''Plot and animate the on the graph.

    This is called every _plot_rate ms

    Args:
        i (int): ???
        x_points (list): the list of x points saved from the previous function call
        y_points (list): the list of y points saved from the previous function call
        plt (module): the matplotlib plot object
        axes (axes): the matplotlib axes
    Returns:
        None
    '''
    if not process_running(_ppid):
        # check if the parent process is still running
        # this is because IDLE does not close this process and its plot window
        # on the mac terminal the process and window closes but this is just an extra check
        sys.exit()

    # get the end point and add it to the start of the lists
    # this is so the points connect on the plot rather than an empty space
    if x_points:
        end_x = x_points[-1]
        x_points.clear()
        x_points.append(end_x)
    if y_points:
        end_y = y_points[-1]
        y_points.clear()
        y_points.append(end_y)

    for point in _data_points:
        # add x and y to lists
        x_points.append(point[0])
        y_points.append(point[1])
    # clear the list so the data isn't replotted next time
    _data_points.clear()

    # draw the lists
    plt.plot(x_points, y_points, color=PLOT_COLOUR)

    # apply plot formatting here

# plot figure and axes
fig, ax = plt.subplots()
x_points = []
y_points = []
# create a func animation to call animate every _plot_rate ms
ani = animation.FuncAnimation(fig, animate, fargs=(x_points, y_points, plt, ax), interval=_plot_rate)
plt.show()
