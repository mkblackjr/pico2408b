"""
Device Parent Class.

he Device class acts as a framework for the child devices, whose classes can
be simplified to contain only the executions specifically pertinent to the 
individual device.

Device parent class contains the following class variables:
    _name:              String  - name of device in ALL_CAPS (DEVICE)
    _opening:           Boolean - whether an attempt to open device was made
    _open:              Boolean - whether device was successfully opened
    _running:               Boolean - whether device was successfully started
    _allow_save:        Boolean - whether data to be collected will be saved
    _has_error:         Boolean - whether error has occurred in open, start,
                                  save, or update method
    _has_save_thread:   Boolean - whether device uses separate save thread
    _has_update_thread: Boolean - whether device uses separate update thread
    _lock:              multiprocessing.Lock - lock used start/stop methods 

Device parent class contains the following class properties:
    ready(): Boolean - maps to self._open

Device parent class contains the following public class methods:
    open():             Opens the device
    close():            Closes out the device
    start():            Starts updating and saving methods
    stop():             Stops updating and saving methods
    update():           Runs _update_device method on a background thread
    save():             Runs _save_device method on a background thread
    create_directory(): Creates new directories for saving device data
"""

__author__     = "Mitchell Black"
__copyright__  = "Copyright 2018, Michigan Aerospace Corporation"
__credits__    = ["Mitchell Black", "Chad Lewis", "James Borck"]
__version__    = "3.6.3"
__maintainer__ = "Mitchell Black"
__email__      = "mblack@michiganaerospace.com"
__status__     = "Development"

from multiprocessing import Lock
from queue import Queue
from threading import Thread
from time import sleep,time
from os import mkdir
import traceback
import sys
import datetime

###############################################################################
############################### Class Definition ##############################
###############################################################################

class Device(object):
    """ Parent class for generic devices requiring serial, COM port, or 
    ethernet communication. """

    def __init__(self):
        """ Device Constructor: Does not accept any arguments. """

        self._name       = "DEVICE_PARENT_CLASS"
        self._opening    = False
        self._open       = False
        self._running    = False
        self._allow_save = False
        self._has_error  = False

        self._data_queue        = None # Queue for data
        self._has_save_thread   = None # Saves data placed into queue
        self._has_update_thread = None # Gets data and places it into queue
        self._lock = Lock()

        self._error_check_thread = Thread(target=self.check_error)

    @property
    def ready(self):
        """ Property for whether device is open and ready to be started. """
        return self._open

    def __del__(self):
        print("{} CLOSED".format(self._name))

    def open(self):
        """ Public method called to open device, i.e. device.open().
        Does not accept any arguments. 
        Does not return any values.
        """
        self._opening = True
        
        try:
            print("OPENING {}".format(self._name))
            self._open = self._open_device()
        except:
            self._has_error = True
            traceback.print_exc(file=sys.stdout)

        if self._open:
            if self._has_save_thread or self._has_update_thread:
                self._data_queue = Queue()

            if self._has_save_thread:
                self._save_thread = Thread(target=self.save,args=(self._data_queue,))
                self._save_thread.daemon = True
                self._save_thread.start()
            if self._has_update_thread:
                self._update_thread = Thread(target=self.update,args=(self._data_queue,))
                self._update_thread.daemon = True
                self._update_thread.start()

            print("{} is ready".format(self._name))
        else:
            print("Error opening {}".format(self._name))

    def _open_device(self):
        """ Overwritten by child device. """
        print("OPENING {}".format(self._name))
        return True

    def close(self):
        """ Public method called to close device, i.e. device.close().
        Does not accept any arguments. 
        Does not return any values.
        """
        if self._open:
            if self._running:
                self.stop()
            self._open = False
            self._opening = False
            print("CLOSING {}".format(self._name))
            self._close_device()

    def _close_device(self):
        """ Overwritten by child device."""
        print("CLOSING {}".format(self._name))

    def start(self,data_dir=None):
        """ Public method called to start device, i.e. device.start().
        data_dir: optional argument, string directory where data is stored.
        Does not return any values.
        """
        if self._open:
            with self._lock:
                if data_dir is not None:
                    self._data_dir = data_dir

                # Child device start routine
                if not self._running:
                    if self._allow_save:
                        self._create_log()
                    try:
                        print("STARTING {}".format(self._name))
                        self._running = self._start_device()
                    except:
                        self._has_error = True
                        traceback.print_exc(file=sys.stdout)

                    if self._running:
                        print("{} STARTED".format(self._name))
                    else:
                        print("{} DID NOT START".format(self._name))
                else:
                    print("{} is already running.".format(self._name))
        else:
            print("{} is not Open and did not start.".format(self._name))

    def _start_device(self):
        """ Overwritten by child device."""
        print("STARTING {}".format(self._name))
        return True

    def stop(self):
        """ Public method called to stop device. For example, device.stop().
        Does not accept any arguments. 
        Does not return any values.
        """
        with self._lock:
            self._running = False
            self._allow_save = False
            print("STOPPING {}".format(self._name))
            self._stop_device()

    def _stop_device(self):
        """ Overwritten by child device."""
        print("STOPPING {}".format(self._name))

    def restart(self):
        """ Public method called to restart device, i.e. device.restart().
        Does not accept any arguments. 
        Does not return any values.
        """
        self.close()
        sleep(1)
        self.open()

    def toggle_save(self):
        """ Public method called to toggle whether the collected data is saved.
        Does not accept any arguments. 
        Does not return any values.
        """
        # Create new directory if _allow_save changing to True
        if not self._allow_save:
            self._create_log()
        self._allow_save = not self._allow_save
        print("{} Allow Save: {}".format(self._name,self._allow_save))

    def check_error(self):
        while True:
            if self._has_error:
                print("{} has Error".format(self._name))
                self._open = False
                self._running = False
                self._allow_save = False

    def save(self,queue):
        """ Public method run on background self._save_thread. Does not need to
        be invoked. Will be started automatically if self._has_save_thread is
        set to True. Responsible for formatting and saving data and keeping 
        track of errors.

        queue: the data queue to be populated during _get_update method. 
        Does not return any values.
        """
        self._init_save()
        while True: 
            if self._running and self._allow_save:
                try:
                    self._save_data(queue)
                except:
                    self._has_error = True
                    traceback.print_exc(file=sys.stdout)            

    def _init_save(self):
        """ Overwritten by child device."""
        print("_init_save")

    def _save_data(params):
        """ Overwritten by child device."""
        print("Saved Parameters {}".format(params))
        sleep(1)

    def update(self,queue):
        """ Public method run on background self._update_thread. Does not need 
        to be invoked. Will be started automatically if self._has_update_thread 
        is set to True. Responsible for collecting data and keeping track of
        errors.

        queue: the data queue populated during device._get_update() 
        Does not return any values.
        """
        while True:
            if self._running:
                try:
                    self._get_update(queue)
                except:
                    self._has_error = True
                    traceback.print_exc(sys.stdout)

    def _get_update(self,queue):
        """ Overwritten by child device."""
        print("Getting Update")
        sleep(1)

    def _create_log(self):
        """ Overwritten by child device."""
        pass

###############################################################################
##################################### Main ####################################
###############################################################################

if __name__ == "__main__":
    dev = Device()
    dev.open()
    dev.toggle_save()
    dev.start()

    sleep(3)
    
    dev.stop()
    dev.close()

