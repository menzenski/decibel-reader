#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Display current decibel readings with a graphical gauge."""

import ftplib
import json
import math
import os
import random
import sys
import time
import Tkinter
import usb.core

try:
    from ftpconfig import FTP_HOST, FTP_USERNAME, FTP_PASSWORD, FTP_DIR
except ImportError:
    print "FTP configuration import failed. Saving output locally only."
    pass

def fibonacci_number(n):
    """Return the Nth Fibonacci number."""
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a

class FTPConnection(object):
    """FTP connection for uploading files."""

    def __init__(self, host, user, password, directory):
        """Initialize the FTP connection object.

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
        # called at the beginning of a 'with' block
        self.ftp = ftplib.FTP(self.host)
        self.ftp.login(self.user, self.password)
        # self.ftp.set_pasv(False)
        return self

    def __exit__(self, *args, **kwargs):
        # called at the end of a 'with' block
        try:
            self.ftp.quit()
        # if there's no connection to close, don't do anything
        except AttributeError:
            pass

    def send_file(self, filename, ext='.json', directory=None):
        """Upload a plain text file to the specified FTP directory.

           Parameters
           ----------
             filename (str) : file name, minus extension
             ext (str) : file extension
             directory (str) : destination subdirectory
        """
        if directory is None:
            directory = self.directory
        self.ftp.cwd(directory)
        fname = filename + ext
        return self.ftp.storlines('STOR {}'.format(fname), open(fname, 'r'))

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
        """Update the label with new content.

           Parameters
           ----------
             db (float, int) : decibel value
        """
        self.text.set('{} {}'.format(db, self.units))

class DecibelVisualizer(object):
    """Cool-looking way to visualize decibel levels."""

    def __init__(self, parent, width=320, height=150, min_db=30, max_db=130,
                 delay=500, subintervals=10, title="Live Decibel Reading",
                 units='dB', use_ftp=False, ftp_host='', ftp_username='',
                 ftp_password='', ftp_dir='', fname_send='kudbs',
                 fname_save='totalresults', seconds_between_uploads=15):
        """Initialize the DecibelVizualizer widget.

           Parameters
           ----------
             parent (Tkinter widget) : the parent widget
             width (int) : width of the visualization in pixels
             height (int) : height of the visualization in pixels
             min_db (int) : minimum decibel level of the USB sound meter
             max_db (int) : maximum decibel level of the USB sound meter
             delay (int) : refresh rate of the USB sound level meter in
               milliseconds (i.e, delay=500 means a refreshed rate of 2x
               per second)
             subintervals (int) : number of times per second that the
               visualization will be refreshed
             title (str) : title displayed at the top of the main window
             units (str) : units of measurement for the meter readings
             use_ftp (boolean) : should readings be sent to FTP server?
             ftp_host (str) : hostname for FTP server
             ftp_username (str) : username for FTP server
             ftp_password (str) : password for FTP server
             ftp_dir (str) : path to desired directory on FTP server
             fname_send (str) : filename for sending live readings via FTP
               while the script is running
             fname_save (str) : filename for saving all results locally
               when script is stopped
             seconds_between_uploads (int) : seconds between each attempt
               to send data to the FTP server
        """
        self.parent = parent
        self.parent.wm_title(title)
        self.Canvas = Tkinter.Canvas(parent, width=width, height=height)
        self.w = width
        self.h = height
        self.min_db = float(min_db)
        self.max_db = float(max_db)
        self.min_scale = 0
        self.max_scale = max_db + 10
        self.db_current = min_db
        self.db_maximum = min_db
        self.all_dbs = []
        self.temp_dbs = []
        # live decibel tracking won't happen while self.event is None
        self.event = None
        # delay between readings of the USB device, in milliseconds
        self.delay = delay
        # number of times per second that the visualization will refresh
        self.subintervals = subintervals
        self.seconds_between_uploads = seconds_between_uploads

        # filename for the JSON to be sent via FTP
        self.fname_send = fname_send
        # filename for the JSON to be saved locally with all results
        self.fname_save = fname_save

        # ftp login credentials
        self.use_ftp = use_ftp
        self.ftp_host = ftp_host
        self.ftp_username = ftp_username
        self.ftp_password = ftp_password
        self.ftp_dir = ftp_dir

        # if self.use_ftp == True:
        #    self.ftp_connection = FTPConnection(
        #             self.ftp_host, self.ftp_username, self.ftp_password,
        #             self.ftp_dir)

        self.colors = {
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

        # counters
        self.counter = 0
        self.subcounter = 0
        self.ftpcounter = 0
        self.fibcounter = 1

        # set up the labels and headings
        self.cur_heading = ReadoutHeading(parent,
                                          text="Current Decibel Reading:")
        self.cur_value = ReadoutValue(parent, value=min_db)

        self.avg_heading = ReadoutHeading(parent, text="Today's Average:")
        self.avg_value = ReadoutValue(parent, value=min_db, fontsize=44)

        self.max_heading = ReadoutHeading(parent, text="Today's Maximum:")
        self.max_value = ReadoutValue(parent, value=min_db, fontsize=44)

        # buttons
        self.close_button = Tkinter.Button(
                parent, text='Stop', font=('Helvetica', '30'),
                command=self.stop_reading)
        """Stop reading and displaying dB values and save all readings."""

        self.demo_button = Tkinter.Button(
                parent, text='Demo', font=('Helvetica', '30'),
                command=self.live_display)
        """Display one new data point."""

        self.start_button = Tkinter.Button(
                parent, text='Start', font=('Helvetica', '30'),
                command=self.start_live_db_reading)
        """Start reading and displaying dB values."""

        # configure the parent widget's grid
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        # add widgets to the parent widget's grid
        self.Canvas.grid(row=2, column=1, columnspan=3, rowspan=3)
        self.cur_heading.Label.grid(row=0, column=0, columnspan=2, padx=10,
                                    pady=10)
        self.cur_value.Label.grid(row=1, column=0, pady=5)

        self.avg_heading.Label.grid(row=0, column=2, padx=10, pady=5)
        self.avg_value.Label.grid(row=0, column=3, pady=5)

        self.max_heading.Label.grid(row=1, column=2, padx=10, pady=5)
        self.max_value.Label.grid(row=1, column=3, pady=5)
        self.close_button.grid(row=4, column=0, padx=10, pady=5)
        self.demo_button.grid(row=3, column=0, padx=10, pady=5)
        self.start_button.grid(row=2, column=0, padx=10, pady=5)

    def _send_file_via_ftp(self, fname, ext='.json'):
        """Try to send a file to the FTP server.

           Parameters
           ----------
             fname (str) : file name, minus extension
             ext (str) : file extension
        """
        ftp_conn = FTPConnection(self.ftp_host, self.ftp_username,
                                 self.ftp_password, self.ftp_dir)
        # ideally data is sent every 15 seconds
        standard_wait = self.seconds_between_uploads
        try:
            with ftp_conn as ftp:
                cmd = ftp.send_file(filename=fname)
            # confirm successful upload and delete temp file
            if cmd == '226 Transfer complete.':
                print 'Successful upload! {}'.format(cmd)
                self.temp_dbs = []
                self.fibcounter = 1
                self.ftpcounter = 0
        # if we get an error, keep trying
        except AttributeError as e:
            print "AttributeError: {}".format(e)
        except:
            print 'Unexpected error: {}'.format(sys.exc_info()[0])
            wait = (standard_wait + fibonacci_number(self.fibcounter)) * 1000
            self.Canvas.after(wait, self._send_file_via_ftp, fname)
            self.fibcounter += 1

    def save_json(self, obj, filename='results', overwrite=False):
        """Save an object to file in JSON format."""
        # convert a single reading to a list
        if isinstance(obj, tuple):
            obj = [obj]
        if overwrite == False:
            file_number_in_use = True
            idx = 1
            while file_number_in_use:
                str_idx = str(idx).rjust(2, '0')
                fname = '{}_{}'.format(filename, str_idx)
                if os.path.isfile(fname + '.json'):
                    idx += 1
                else:
                    filename = fname
                    break
        # the overwritten file should be as small as possible for FTP
        indent = 3 if overwrite == False else None
        json_output = json.dumps(obj, indent=indent, separators=(',', ':'))
        with open(filename + '.json', 'w+') as stream:
            stream.write(json_output)

    def live_dbs(self, lower_bound=None, upper_bound=None):
        """Return the live decibel reading from the USB device.

           Parameters
           ----------
             lower_bound (int) : minimum decibel reading
             upper_bound (int) : maximum decibel reading

           Returns
           -------
             (float) : current decibel reading, either the actual
               reading from the connected USB device, or a random
               reading which may approximate it for testing purposes.
               The returned reading is rounded to two decimal places.
        """
        if lower_bound is None:
            lower_bound = self.min_db
        if upper_bound is None:
            upper_bound = self.max_db
        try:
            # identify the usb device
            dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc)
            # decipher its signal
            ret = dev.ctrl_transfer(0xC0, 4, 0, 0, 200)
            db = (ret[0] + ((ret[1] & 3) * 256)) * 0.1 + 30
            db_as_string = '{0:.2f}'.format(float(db))
            return float(db_as_string)
        # allow a demo mode in case the demo mode isn't connected.
        except ValueError:
            return float('{0:.2f}'.format(
                    float(random.randrange(lower_bound, upper_bound))))
        except Exception as e:
            print "Unknown exception: {}".format(e)
            return float('{0:.2f}'.format(
                    float(random.randrange(lower_bound, upper_bound))))

    def draw_frame(self):
        """Draw the frame and labels."""
        x1, y1 = 10, 10
        x2, y2 = 10, self.max_scale
        x3, y3 = self.w, self.max_scale
        self.Canvas.create_line(x1, y1, x2, y2, x3, y3, fill='black')

    def draw_one_bar(self, bar_height=130, bar_width=20, left_edge=20):
        """Draw a single bar composed of colored bins.

           Parameters
           ----------
             bar_height (float, int) : height of the bar in pixels
             bar_width (int) : width of the bar in pixels
             left_edge (int) : horizontal position of the bar's left edge,
               in pixels
        """
        # incremental height -- a bar is built up bin by bin
        inc_height = 0
        for i in range(0, int(bar_height) / 10 + 1):
            # the topmost bin will often be shorter than the usual bin height
            dif = bar_height - (i * 10)
            bin_height = min([dif, 10])
            col = self.colors[i]
            # define the top-left and bottom right corners of the bin
            x1, y1 = left_edge, self.max_scale - ((i * 10) + bin_height)
            x2, y2 = left_edge + bar_width, self.max_scale - (i * 10)

            inc_height += bin_height
            if inc_height > bar_height:
                break

            # draw a single bin
            self.Canvas.create_rectangle(x1, y1, x2, y2, fill=col)

    def draw_multiple_bars(self, list_of_height_edge_tuples):
        """Draw multiple, potentially different, bars at once.

           Parameters
           ----------
             list_of_height_edge_tuples (list) : list of 2-tuples, e.g.:
                 [(105, 20), (115, 50), (125, 80)]
               Each tuple represents one bar. The first entry in the tuple
               (int) is the bar's height, while the second (int) is the
               horizontal position of the bar's left edge.
        """
        for h, e in list_of_height_edge_tuples:
                self.draw_one_bar(bar_height=h, left_edge=e)

    def draw_identical_bars(self, bar_height):
        """Draw ten bars with identical heights.

           Parameters
           ----------
             bar_height (float, int) : height of the bars
        """
        self.draw_multiple_bars(
            [(bar_height, e) for e in [20+i*30 for i in range(0,10)]])

    def draw_interpolated_individual_bars(self, subcounter=None):
        """Draw ten bars which show smooth transitions between values.

           Parameters
           ----------
             subcounter (int) : number of transitional points to be
               generated between pairs of measurements
        """
        if subcounter is None:
            subcounter = self.subcounter
        # create a list of tuples representing all measurement pairs
        # e.g. [0, 1, 2, 3] --> [(0, 1), (1, 2), (2, 3)]
        tup_list = [(self.all_dbs[i][1], self.all_dbs[i+1][1])
                    for i in range(len(self.all_dbs) - 1)]
        # create a new list with finer-grained intervals by interpolating
        # between each measurement pair in tup_list
        int_list = []
        for a, b in tup_list:
            vals = self.interpolate_two_values(a, b)
            int_list += vals
        # number of bars to be drawn (ten is default)
        num = 10
        # the zip here joins a list of ten heights to a list of ten edges
        self.draw_multiple_bars(
            [(v, e) for (v, e) in zip(
                int_list[-(num + subcounter):],
                [20+i*30 for i in range(0, 10)])])

    def interpolate_two_values(self, val_a, val_b, subintervals=None):
        """Return a list of values evenly spaced between two values.

           Parameters
           ----------
             val_a (float, int) : older measurement
             val_b (float, int) : more recent measurement
             subintervals (int) : number of transitional points to be
               generated between the pair of measurements
        """
        if subintervals is None:
            subintervals = self.subintervals
        interval = val_b - val_a
        increment = interval / float(subintervals)
        return [val_a + (increment * s) for s in range(0, subintervals)]

    def fetch_new_reading(self):
        """Get a new reading from the decibel meter."""
        new = (int(time.time()), self.live_dbs())
        self.all_dbs.append(new)
        self.temp_dbs.append(new)
        self.ftpcounter += 1
        self.save_json(self.temp_dbs, filename=self.fname_send,
                       overwrite=True)
        if self.use_ftp == True:
            if self.ftpcounter % self.seconds_between_uploads == 0:
                self._send_file_via_ftp(fname=self.fname_send)
        self.update_stats()

    def live_display(self, subintervals=None):
        """Monitor live decibel readings and plot with smoothness.

           Parameters
           ----------
             subintervals (int) : number of transitional points to be
               generated between each pair of measurements
        """
        if subintervals is None:
            subintervals = self.subintervals
        delay = self.delay / subintervals
        if len(self.all_dbs) >= 2:
            # the USB meter's refresh rate and the subcounter are in sync
            self.subcounter = self.counter % subintervals
            # clear the canvas before drawing any new bars
            self.clear()
            self.draw_interpolated_individual_bars()

            # if subcounter is zero, it's time to read the meter
            if self.subcounter == 0:
                self.fetch_new_reading()
                self.counter += 1
            else:
                self.counter += 1
        else:
            self.fetch_new_reading()
            self.counter += 1
        # call this function recursively, if desired
        if self.event:
            self.Canvas.after(delay, self.live_display)

    def update_stats(self):
        """Update labels with new information."""
        self.db_current = self.all_dbs[-1][1]
        temp_average = sum(
            [e[1] for e in self.all_dbs]) / float(len(self.all_dbs))
        self.db_average = float('{0:.2f}'.format(temp_average))
        self.db_maximum = max(self.db_current, self.db_maximum)
        self.cur_value.update(self.db_current)
        self.avg_value.update(self.db_average)
        self.max_value.update(self.db_maximum)

    def start_live_db_reading(self, ms_between_readings=None):
        """Start live tracking and outputting of decibel readings."""
        if ms_between_readings is None:
            ms_between_readings = self.delay
        self.event = 'something'
        self.live_display()

    def clear(self):
        """Remove existing bars from the visualizer and redraw the frame."""
        self.Canvas.delete('all')
        self.draw_frame()

    def stop_reading(self, filename=None):
        """Stop tracking decibel input and save all results."""
        if filename is None:
            filename = self.fname_save
        self.use_ftp = False
        self.event = None
        self.save_json(obj=self.all_dbs, filename=filename, overwrite=False)

def main():
    root = Tkinter.Tk()
    root.geometry('570x330+30+30')
    if len(sys.argv) == 2:
        if sys.argv[1] == '--ftp':
            g = DecibelVisualizer(
                    root, use_ftp=True, ftp_host=FTP_HOST,
                    ftp_username=FTP_USERNAME, ftp_password=FTP_PASSWORD,
                    ftp_dir=FTP_DIR)
    else:
        g = DecibelVisualizer(root, use_ftp=False)
    g.draw_frame()
    # have the app open with some nice-looking bars on the screen
    g.draw_multiple_bars(
        [(105, 20), (115, 50), (125, 80), (121, 110), (120, 140),
         (119, 170), (118, 200), (115, 230), (112, 260), (108, 290)]
        )

    root.mainloop()

if __name__ == '__main__':
    main()
