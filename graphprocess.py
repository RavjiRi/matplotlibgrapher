"""
The graphing subprocess helper.

This is called by the main script in a subprocess.
There are two threads in this process:
    - The main thread with the matplotlib graph
    - The xmlrpc server receiving data

This is not intended to run by itself.

Version: 4/3/25

Author: RavjiRi
"""
from xmlrpc.server import SimpleXMLRPCServer
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

def process_running(pid: int):
    # check if a process is running
    strpid = str(pid)
    p = run(['ps', '-e'], capture_output=True) # get all running processes
    # count how many processes are with the pid
    # uses a trick that encloses the first number in brackets so this grep command isn't counted
    p = run(['grep', '-c', "[{}]{}".format(strpid[0], strpid[1:])], capture_output=True, input=p.stdout)
    return not (int(p.stdout) == 0) # if there are no processes return false, else return true

_data_points = [] # store plot points that are sent
def _on_data_recieved(data_sent: list):
    # extend sent data to data points list
    _data_points.extend(data_sent)
    return True

# create XML RPC server at localhost:8000 (broadcast address)
_server = SimpleXMLRPCServer(("127.0.0.1", 8000), logRequests=False)
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

# This function is called periodically from FuncAnimation
def animate(i, xs, ys, plt, ax):
    if not process_running(_ppid):
        # check if the parent process is still running
        # this is because IDLE does not close this process and its plot window
        # on the mac terminal the process and window closes but this is just an extra check
        sys.exit()

    for point in _data_points:
        # add x and y to lists
        xs.append(point[0])
        ys.append(point[1])
    # clear the list so the data isn't replotted next time
    _data_points.clear()

    # Limit x and y lists to 20 items
    #xs = xs[-20:]
    #ys = ys[-20:]

    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)

# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []
# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys, plt, ax), interval=_plot_rate)
plt.show()
