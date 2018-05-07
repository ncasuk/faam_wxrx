'''
File size logger daemon for the weather radar data files on the ARA. The file
size of a user specified weather radar project is monitored during the flight.
This allows for time stamping any weather radar data post flight.

Weather Radar laptop procedure:
(1) Switch on laptop
(2) Run "About time ..." and set the laptop clock
(3) Start-up CoPilot, set up project, and start logging
(4) Start filesizeLogger


http://www.manning-sandbox.com/thread.jspa?threadID=2883

Created on 28 Oct 2011
'''

import datetime
import json
import os
import re
import sys
import subprocess
import threading
import urllib2

from Tkinter import *
import tkSimpleDialog
import tkMessageBox


LOGFILE_PATH = None
COPILOT_PATH = os.path.join('C:\\', 'CoPilot Projects')
TEMP_PATH = os.path.join('C:\\', 'Documents and Settings', 'WxRx CGPS', 'Local Settings', 'Temp')
DATAFILE = None
LOGFILE = None
HANDLE_EXE = 'C:\\bin\\handle.exe'          #http://technet.microsoft.com/en-us/sysinternals/bb896655


def set_logfile_path(fid):
    """Get the path where the CoPilot project is stored. Check both
lower and upper case."""
    global LOGFILE_PATH
    if os.path.exists(os.path.join(COPILOT_PATH, str.lower(fid))):
        LOGFILE_PATH = os.path.join(COPILOT_PATH, str.lower(fid))
    elif os.path.exists(os.path.join(COPILOT_PATH, str.upper(fid))):
        LOGFILE_PATH = os.path.join(COPILOT_PATH, str.upper(fid))
    else:
        LOGFILE_PATH = None
        return None


def guess_fid():
    """Try to get the actual flight number (Bnnn) from the
flight summary web site on HORACE. If not successful
return string 'Bnnn'."""

    result = ""
    try:
        response = urllib2.urlopen('http://192.168.101.110/live/tank_status.json')
        data = json.load(response)
        result = str(data['Tank']['Flight']).lower()
    except:
        pass
    return result


def check_fid(user_input):
    """Check if the user input flight number is valid.
Return result is either True (=valid) or False (not valid)."""
    try:
        if re.match('[b,c][0-9][0-9][0-9]', str.lower(user_input)):
            return True
        else:
            return False
    except:
        return False


def set_logfile(fid):
    """Define data file and log file."""
    global DATAFILE, LOGFILE
    try:
        os.path.exists(os.path.join(LOGFILE_PATH, LOGFILE))
        msg = 45*'#' + '\n' + '#  Logging restarted: ' + str(datetime.datetime.now()) + '\n' + 45*'#' + '\n'
        mode = 'a'
    except:
        LOGFILE = os.path.join(LOGFILE_PATH, str.upper(fid) + '.log')
        msg = 45*'#' + '\n' + '#  Logging started: ' + str(datetime.datetime.now()) + '\n' + 45*'#' + '\n'
        mode = 'w'
    out = open(LOGFILE, mode)
    out.write(msg)
    out.close()


def get_filelist():
    """
    """
    filelist = []
    args = '-p CoPilot'
    #http://stackoverflow.com/questions/2935704/running-shell-commands-without-a-shell-window
    #creationflags=0x08000000: disableds shell pop-up window
    p = subprocess.Popen(HANDLE_EXE+' '+ args, creationflags=0x08000000, stdout = subprocess.PIPE)
    out = p.stdout.read()
    for line in out.split('\r\n'):
        pattern = 'COP.*.tmp$'
        if re.search(pattern, line):
            filelist.append(os.path.join(TEMP_PATH, os.path.basename(line)))
    return filelist


def set_datafile( ):
    """The wxrx logging data file can change during a flight,
    when the CoPilot software has been restarted for example.
    """
    global DATAFILE
    filelist = get_filelist()
    if not filelist:
        DATAFILE = None
        return None
    mod_timestamp = []
    for file in filelist:
        mod_timestamp.append(os.stat(file).st_mtime)
    combi = zip(mod_timestamp, filelist)
    combi.sort()
    combi.reverse()
    DATAFILE = combi[0][1]


def log_filesize():
    global FILESIZE, LOGFILE, DATAFILE
    FILESIZE = os.stat(DATAFILE).st_size
    out = open(LOGFILE, 'a')
    out.write(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ',' + str(FILESIZE) + \
               ',' + os.path.basename(DATAFILE) + '\n')
    out.close()


def daemon():

    #try statement prevents crashing if CoPilot
    #is closed while this program is still running
    try:
        set_datafile()
        log_filesize()
    except:
        pass
    #Start the threading daemon
    threading.Timer(10.0, daemon).start()


if __name__ == '__main__':
    fid = None
    root = Tk()
    root.geometry('0x0+400+300')  # make root window "tiny"
    root.overrideredirect(1)      # get rid of the frame, border, etc.

    while not fid:
        fid = tkSimpleDialog.askstring('Flight Number', 'Input Flight Number', initialvalue=guess_fid())
        if not fid:
            sys.exit()
        #check the user inputed fid; exit on error
        if not check_fid(fid):
            tkMessageBox.showerror('Error', 'Flight Number format has to be bnnn')
            sys.exit()

    set_logfile_path(fid)
    if not LOGFILE_PATH:
        tkMessageBox.showerror('Error', 'No CoPilot folder found for\n' + fid + '\nLogging aborted!')
        sys.exit()
    set_logfile(fid)
    set_datafile()
    if not DATAFILE:
        tkMessageBox.showerror('Error', 'No data file found!\nHas CoPilot been fired up yet?\nLogging aborted!')
        sys.exit()
    tkMessageBox.showinfo('Info', 'Start logging!')
    daemon()
