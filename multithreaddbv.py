#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Display current decibel readings with a graphical gauge."""

# TODO: (interpolated) data points at 15 samples/second
# TODO: send most recent 300 samples at a time
# TODO: upload to FTP once per second

# Revised TODO items, for multithreaded version:
#
# don't write temp files: send as cStringIO.StringIO() instead
# (don't forget to close them, though!)

from __future__ import print_function, division

import ftplib
import itertools
import json
import math
import os
import Queue
import random
import sys
import threading
import time
import Tkinter
import usb.core

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
    print("Using non-C implementation of StringIO.")

try:
    from ftpconfig import FTP_HOST, FTP_USERNAME, FTP_PASSWORD, FTP_DIR
except ImportError:
    print("FTP configuration import failed.")

def interpolate_two_numbers(earlier, later, subintervals=10):
    """Return a list of values evenly spaced between two values.

       Parameters
       ----------
         earlier (float, int) : the older of the two values
         later (float, int) : the more recent of the two values
         subintervals (int) : number of transitional points to be
           generated between the pair of values
    """
    interval = later - earlier
    increment = interval / subintervals
    return (earlier + (increment * s) for s in xrange(0, subintervals))

def interpolate_two_tuples(older, newer, subintervals=10):
    """Interpolate between two tuples."""
    return itertools.izip(interpolate_two_numbers(older[0], newer[0]),
                          interpolate_two_numbers(older[1], newer[1]))

class DecibelDataObject(object):
    """File-like object containing decibel data for FTP uploading."""

    def __init__(self, list_of_tuples):
        """Initialize the DecibelDataObject object.

           Parameters
           ----------
             list_of_tuples (list) : list of 2-tuples, each of which contains
               a Unix timestamp in milliseconds in the first position and a
               decibel reading in the second position.
        """
        self.tups = list_of_tuples

    def __enter__(self):
        # open the context manager
        json_string = json.dumps(self.tups, indent=None
                                 separators=(',', ':'))
        self.file_like_obj = StringIO.StringIO(json_string)
        return self

    def __exit__(self):
        # close the context manager
        try:
            self.file_like_obj.close()
        except Exception:
            # if it's not open, don't do anything
            pass

class DBMeterReader(object):
    """Decibel Meter Reader."""

    MIN_DB = 30
    MAX_DB = 130

    def __init__(self, queue, **kwargs):
        """Initialize the DBMeterReader object.

           Parameters
           ----------
             queue (Queue.Queue) : queue to which new decibel readings
               will be added
        """
        self.queue = queue
        self.temp = []

    def _put(self, tup):
        """Put a 2-tuple into the queue."""
        self.queue.put(tup)

    def produce_data(self):
        self._put(self.new_reading())

    def new_reading(self):
        """Put a 2-tuple---a Unix timestamp and a dB value---in the queue."""
        reading = int(time.time() * 1000), self._db_value()
        return reading

    def _db_value(self):
        """Get the current decibel reading.

           Returns
           -------
             (float) : current decibel reading rounded to two decimal
                 places. If the meter's connected, this is the actual
                 decibel level. If the meter is not connected, or there's
                 an error, this number is a random value within the range
                 of the meter.
        """
        try:
            # identify the usb device
            dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc)
            # decipher its signal
            ret = dev.ctrl_transfer(0xc0, 4, 0, 0, 200)
            db = (ret[0] + ((ret[1] & 3) * 256)) * 0.1 + 30
            db_as_string = '{0:.2f}'.format(float(db))
            return float(db_as_string)
        # allow a demo mode in case the usb sound level meter isn't connected
        except Exception as e:
            # print('{}: {}'.format(e.__doc__, e.message))
            return float('{0:.2f}'.format(float(random.randrange(
                self.MIN_DB, self.MAX_DB))))

class FTPUploader(object):
    """FTP connection with associated methods."""

    def __init__(self, host, user, password, directory='/', **kwargs):
        """Initialize the FTPUploader object.

           Parameters
           ----------
             host (str) : FTP hostname
             user (str) : FTP username
             password (str) : FTP password
             directory (str) : desired FTP subdirectory
        """
        self.host = host
        self.user = user
        self.password = password
        self.directory = directory

    def __enter__(self):
        """dostring"""
        self.ftp = ftplib.FTP(self.host)
        self.ftp.login(self.user, self.password)
        return self

    def __exit__(self):
        """docstring"""
        try:
            self.ftp.quit()
        # if there's no connection to close, we don't need to do anything
        except AttributeError:
            pass

    def upload_filelike_obj(self, obj, filename, directory=None):
        """Upload a filelike object to an FTP directory."""
        if directory is None:
            directory = self.directory
        # TODO: Flesh out this function
        # TODO: Add a separate class for the json string, which has a
        # `.as_stringio()` method which returns a cStringIO.StringIO object.

class ReadoutHeading(object):
    """Display a description of some measurement."""

    def __init__(self, parent, text):
        """Initialize the ReadoutHeading object.

           Parameters
           ----------
             parent (Tkinter widget) : the parent widget
             text (str) : text for the label
        """
        self.Label = Tkinter.Label(parent, text=text)

class ReadoutValue(object):
    """Display a measurement in units."""

    def __init__(self, parent, value, fontsize=60, units='dB'):
        """Initialize the ReadoutValue object.

           Parameters
           ----------
             parent (Tkinter widget) : the parent widget
             value (str) : starting text for the label
             fontsize (int) : font size for the label
             units (str) : units of measurement for the value displayed
        """
        self.text = Tkinter.StringVar()
        self.Label = Tkinter.Label(parent, textvariable=self.text,
                                   font=('Helvetica', '{}'.format(fontsize)))
        self.units = units
        self.update(value)

    def update(self, db):
        """Update the readout with a new value.

           Parameters
           ----------
             db (float, int) : decibel value to be displayed
        """
        self.text.set('{} {}'.format(db, self.units))

class GuiDisplay(object):
    """Visualize live sound level data."""

    width = 320
    height = 150
    title = 'Live Decibel Reading'
    units = 'dB'
    min_db = 30
    max_db = 130
    db_average = 30
    db_maximum = 30
    seen = 0
    total = 0
    window_width = 650
    window_height = 330
    x_pos = 30
    y_pos = 30
    colors = {
        13: '#E50000',
        12: '#E14400',
        11: '#DD8700',
        10: '#D9C701',
        9:  '#A7D501',
        8:  '#65D201',
        7:  '#25CE02',
        6:  '#02CA1C',
        5:  '#02C658',
        4:  '#03C391',
        3:  '#03B6BF',
        2:  '#037ABB',
        1:  '#0341B7',
        0:  '#040AB4',
        }

    def __init__(self, parent, queue, start_command, stop_command, **kwargs):
        """Initialize the DecibelVisualizer object and parse any keyword
           arguments..

           Parameters
           ----------
             parent (Tkinter widget) : the parent widget
             queue (Queue.Queue) : queue from which incoming data is read
             start_command (function) : function which begins data reading
             stop_command (function) : function which stops data reading
             **kwargs
        """
        self.parent = parent
        self.queue = queue
        self.temp = []
        if kwargs:
            for k, v in kwargs.iteritems():
                setattr(self, k, v)
        # construct the GUI window and its parts
        self._configure_window()
        self._configure_labels()
        self._configure_buttons(start=start_command, stop=stop_command)
        self._configure_grid()
        self._draw_opening_bars()

    def _configure_window(self):
        """Configure window geometry."""
        self.parent.geometry('{}x{}+{}+{}'.format(
            self.window_width, self.window_height, self.x_pos, self.y_pos))
        self.parent.wm_title(self.title)
        self.Canvas = Tkinter.Canvas(self.parent, width=self.width,
                                     height=self.height)

    def _configure_labels(self):
        """Configure labels and text."""
        self.cur_heading = ReadoutHeading(
                self.parent, text="Current Decibel Reading:")
        self.cur_value = ReadoutValue(self.parent, value=self.min_db)

        self.avg_heading = ReadoutHeading(
                self.parent, text="Today's Average:")
        self.avg_value = ReadoutValue(
                self.parent, value=self.min_db, fontsize=44)

        self.max_heading = ReadoutHeading(
                self.parent, text="Today's Maximum:")
        self.max_value = ReadoutValue(
                self.parent, value=self.min_db, fontsize=44)

    def _configure_buttons(self, start, stop):
        """Configure buttons.

           Parameters
           ----------
             start (function) : function which starts data reading
             stop (function) : function which stops data reading
        """
        self.close_button = Tkinter.Button(
                self.parent, text='Stop', font=('Helvetica', '30'),
                command=stop
                )
        self.demo_button = Tkinter.Button(
                self.parent, text='Demo', font=('Helvetica', '30'))
        self.start_button = Tkinter.Button(
                self.parent, text='Start', font=('Helvetica', '30'),
                command=start
                )

    def _configure_grid(self):
        """Arrange subwidgets on the parent's grid."""
        # weight columns
        self.parent.grid_columnconfigure(0, weight=1, minsize=300)
        self.parent.grid_columnconfigure(1, weight=1)

        # add the canvas to the parent widget's grid
        self.Canvas.grid(row=2, column=1, columnspan=3, rowspan=3)

        # add labels and headings
        self.cur_heading.Label.grid(
                row=0, column=0, columnspan=2, padx=10, pady=10)
        self.cur_value.Label.grid(row=1, column=0, pady=5)

        self.avg_heading.Label.grid(row=0, column=2, padx=10, pady=5)
        self.avg_value.Label.grid(row=0, column=3, pady=5)

        self.max_heading.Label.grid(row=1, column=2, padx=10, pady=5)
        self.max_value.Label.grid(row=1, column=3, pady=5)

        # add buttons
        self.close_button.grid(row=4, column=0, padx=10, pady=5)
        self.demo_button.grid(row=3, column=0, padx=10, pady=5)
        self.start_button.grid(row=2, column=0, padx=10, pady=5)

    def _draw_opening_bars(self):
        """Draw some meaningless bars when the GuiDisplay is started."""
        self.draw_frame()
        list_of_bars = [
            (105, 20), (115, 50), (125, 80), (121, 110), (120, 140),
            (119, 170), (118, 200), (115, 230), (112, 260), (108, 290)]
        for h, e in list_of_bars:
            self.draw_one_bar(bar_height=h, left_edge=e)

    def draw_frame(self):
        """Draw the frame for the decibel visualization."""
        x1, y1 = 10, 10
        x2, y2 = 10, self.max_db + 10
        x3, y3 = self.width, self.max_db + 10
        self.Canvas.create_line(x1, y1, x2, y2, x3, y3, fill='black')

    def clear_bars(self):
        """Remove existing bars from the visualizer and redraw the frame."""
        self.Canvas.delete('all')
        self.draw_frame()

    def draw_one_bar(self, bar_height=130, bar_width=20, left_edge=20):
        """Draw a single bar composed of colored bins.

           Parameters
           ----------
             bar_height (float, int) : height of the bar, in pixels
             bar_width (int) : width of the bar, in pixels
             left_edge (int) : horizontal position of the bar's leftmost
               edge, in pixels
        """
        # incremental height -- a bar is built up bin by bin
        inc_height = 0
        for i in range(0, int(bar_height) // 10 + 1):
            # the topmost bin will often be shorter than the usual bar height
            dif = bar_height - (i * 10)
            bin_height = min([dif, 10])
            col = self.colors[i]
            # a bin is a rectangle defined by top-left and bottom-right pts
            x1, y1 = left_edge, (self.max_db + 10) - ((i * 10) + bin_height)
            x2, y2 = left_edge + bar_width, (self.max_db + 10) - (i * 10)

            inc_height += bin_height
            if inc_height > bar_height:
                break

            # draw one bin
            self.Canvas.create_rectangle(x1, y1, x2, y2, fill=col)

    def draw_multiple_bars(self, list_of_heights):
        """Draw multiple bars at once, from right to left.

           Parameters
           ----------
             list_of_heights (list) :
        """
        bars = zip(list_of_heights[::-1], [20+i*30 for i in range(9, -1, -1)])
        for (height, edge) in bars:
            self.draw_one_bar(bar_height=height, left_edge=edge)

    def process_incoming(self):
        """Handle data in the incoming queue."""
        while self.queue.qsize():
            try:
                # get most recent time and db reading (a 2-tuple)
                t, db = self.queue.get(0)
                print(t, db)
                self.add_to_temp(db)
                self.update_stats(db)
                self.clear_bars()
                self.draw_multiple_bars(self.temp)
                #self.draw_one_bar(bar_height=db)
            except Queue.Empty:
                pass

    def update_stats(self, db):
        """Update labels with new information."""
        # recalculate average and maximum
        self.seen += 1
        self.total += db
        self.db_average = float('{0:.2f}'.format(self.total / self.seen))
        self.db_maximum = max(self.db_maximum, db)
        # update labels
        self.cur_value.update(db)
        self.avg_value.update(self.db_average)
        self.max_value.update(self.db_maximum)

    def add_to_temp(self, db):
        """Return self.temp with a new value, limited to length 10."""
        self.temp.append(db)
        if len(self.temp) >= 10:
            self.temp = self.temp[-10:]
        return self.temp

class DecibelReaderMainApp(object):
    """docstring for DecibelReaderMainApp"""

    def __init__(self, **kwargs):
        """Initialize the DecibelReaderMainApp object.

           Parameters
           ----------
             arg (type) :
        """
        self.root = Tkinter.Tk()
        self._configure_queues()
        #self.running = True

        self.gui = GuiDisplay(parent=self.root, queue=self.raw_db_queue,
                              start_command=self._start,
                              stop_command=self._shutdown)

        # set up threads and start them
        #self._configure_threads()
        # start checking the queue for new data
        #self._periodic_call()

    def _configure_queues(self):
        """Configure the Queues for data input and data output."""
        self.raw_db_queue = Queue.Queue()
        #self.smoothed_db_queue = Queue.Queue()
        #self.ftp_queue = Queue.Queue()

    def _configure_threads(self):
        """Configure the threads used for input and output."""
        self.db_thread = threading.Thread(target=self.get_dbs)
        self.db_thread.start()

    def _periodic_call(self):
        """Check every 100ms if there is something new in the queue."""
        self.gui.process_incoming()
        if not self.running:
            sys.exit(1)
        self.root.after(125, self._periodic_call)

    def _start(self):
        """Start running the app."""
        self.running = 1
        self._configure_threads()
        self._periodic_call()

    def _shutdown(self):
        """Safely stop all running processes."""
        self.running = 0

    def get_dbs(self):
        """Fetch time/decibel readings and add to Queue."""
        while self.running:
            self.DBReader = DBMeterReader(queue=self.raw_db_queue)
            self.DBReader.produce_data()
            time.sleep(1)

    def send_output(self):
        """Handle the thread for sending decibel data via FTP."""
        pass

def main():
    app = DecibelReaderMainApp()
    app.root.mainloop()

if __name__ == '__main__':
    main()
