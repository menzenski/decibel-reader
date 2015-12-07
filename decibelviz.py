#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Display current decibel readings with a graphical gauge."""

import json
import math
import os
import random
import time
import Tkinter
import usb.core

def read_decibels(lower_bound=30, upper_bound=130):
    # allow a demo mode in case the decibel meter isn't connected
    try:
        # identify the usb device
        dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc)
        # decipher its signal
        ret = dev.ctrl_transfer(0xC0, 4, 0, 0, 200)
        db = (ret[0] + ((ret[1] & 3) * 256)) * 0.1 + 30
        db_float = float(db)
        db_string = '{0:.2f}'.format(db_float)
        return float(db_string)
    except ValueError:
        return random.randrange(lower_bound, upper_bound)
    except:
        print "Unknown error/exception encountered."
        return random.randrange(lower_bound, upper_bound)

def save_reading(db, timestamp, filename='kudecibels', filetype='json'):
    """Write the current decibel reading (and a timestamp) to disk.

       Parameters
       ----------
         db (float) : decibel reading
         timestamp (int) : Unix timestamp
         filename (string) : name of the file (not including extension)
         filetype (string) : extension with which the file will be saved
           (currently supports only XML and JSON, but others can be added.)
    """
    if filetype.lower() == 'xml':
        filename = filename + '.xml'
        message = ("""<?xml version="1.0!?>\n<output>\n\t"""
            """<decibel-entry timestamp="{}">{}</decibel-entry>\n"""
            """</output>""")
        with open(filename, 'w+') as output:
            output.write(message.format(timestamp, db))
    elif filetype.lower() == 'json':
        filename = filename + '.json'
        message = """[\n   [{}, {}]\n]"""
        with open(filename, 'w+') as output:
            output.write(message.format(timestamp, db))
    else:
        pass

class ReadoutHeading(object):
    """Displays a description of some measurement."""

    def __init__(self, parent, text):
        """Initialize the ReadoutHeading object."""
        self.Label = Tkinter.Label(parent, text=text)

class ReadoutValue(object):
    """Display a measurement in units."""

    def __init__(self, parent, value, fontsize=60, units='dB'):
        """Initialize the ReadoutValue object."""
        self.text = Tkinter.StringVar()
        self.Label = Tkinter.Label(parent, textvariable=self.text,
            font=('Helvetica', '{}'.format(fontsize)))
        self.update(value)

    def update(self, db):
        """Update the label with new content."""
        self.text.set('{} dB'.format(db))

class DecibelVisualizer(object):
    """Cool-looking way to visualize decibel levels."""

    def __init__(self, parent, width=320, height=150, min_db=30, max_db=130,
                 delay=500, subintervals=10):
        """Initialize the DecibelVizualizer widget."""
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
        # live decibel tracking won't happen while self.event is None
        self.event = None
        # delay between readings of the USB device, in milliseconds
        self.delay = delay
        # number of times per second that the visualization will refresh
        self.subintervals = subintervals

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
        self.demo_button = Tkinter.Button(
                parent, text='Demo', font=('Helvetica', '30'),
                command=self.live_display)
        self.start_button = Tkinter.Button(
                parent, text='Start', font=('Helvetica', '30'),
                command=self.start_live_db_reading)

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

    def live_dbs(self, lower_bound=30, upper_bound=130):
        """Return the live decibel reading from the USB device."""
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

    def draw_frame(self, title="Live Decibel Reading", unit='dB'):
        """Draw the frame and labels."""
        x1, y1 = 10, 10
        x2, y2 = 10, self.max_scale
        x3, y3 = self.w, self.max_scale
        self.Canvas.create_line(x1, y1, x2, y2, x3, y3, fill='black')

    def draw_one_bar(self, bar_height=130, bar_width=20, left_edge=20):
        """Draw a single bar (for testing purposes)."""
        inc_height = 0
        for tot in range(0, int(bar_height) / 10 + 1):
            # bin_height = min([10, bar_height - ((bar_height / 10) * 10)])
            dif = bar_height - (tot * 10)
            bin_height = min([dif, 10])
            col = self.colors[tot]
            x1, y1 = left_edge, self.max_scale - ((tot * 10) + bin_height)
            x2, y2 = left_edge + bar_width, self.max_scale - (tot * 10)

            # print 'x1: {}, x2: {}, y1: {}, y2: {}, col: {}, tot:{}, ' \
            #       'inc_height: {}, bar_height: {}'.format(
            #           x1, x2, y1, y2, col, tot, inc_height, bar_height)

            inc_height += bin_height
            if inc_height > bar_height:
                break

            self.Canvas.create_rectangle(x1, y1, x2, y2, fill=col)

    def draw_multiple_bars(self, list_of_height_edge_tuples):
        for h, e in list_of_height_edge_tuples:
                self.draw_one_bar(bar_height=h, left_edge=e)

    def draw_identical_bars(self, bar_height):
        self.draw_multiple_bars(
            [(bar_height, e) for e in [20+i*30 for i in range(0,10)]])

    def draw_interpolated_individual_bars(self, subcounter=None):
        if subcounter is None:
            subcounter = self.subcounter
        tup_list = [(self.all_dbs[i][1], self.all_dbs[i+1][1])
                    for i in range(len(self.all_dbs) - 1)]
        int_list = []
        for a, b in tup_list:
            vals = self.interpolate_two_values(a, b)
            int_list += vals
        # number of bars
        num = 10
        self.draw_multiple_bars(
            [(v, e) for (v, e) in zip(
                int_list[-(num + subcounter):],
                [20+i*30 for i in range(0, 10)])])

    def interpolate_two_values(self, val_a, val_b, subintervals=None):
        """Return a list of values between two values"""
        if subintervals is None:
            subintervals = self.subintervals
        interval = val_b - val_a
        increment = interval / float(subintervals)
        return [val_a + (increment * s) for s in range(0, subintervals)]

    def live_display(self, subintervals=None):
        """Monitor live decibel readings and plot with smoothness."""
        # if counter % subintervals == 0
        # then fetch a new data point
        # else interpolate the last two
        # TODO: make sure this SAVES the db readings as they happen
        if subintervals is None:
            subintervals = self.subintervals
        delay = self.delay / subintervals
        unix_time = int(time.time())
        if len(self.all_dbs) >= 2:
            # heights = self.interpolate_two_values(
            #         val_a=self.all_dbs[-2][1],
            #         val_b=self.all_dbs[-1][1],
            #         subintervals=subintervals)

            self.subcounter = self.counter % subintervals

            self.clear()
            # self.draw_identical_bars(bar_height=heights[subcounter])
            self.draw_interpolated_individual_bars()

            if self.subcounter == 0:
                self.all_dbs.append((unix_time, self.live_dbs()))
                self.update_stats()
                self.counter += 1
            else:
                self.counter += 1
        else:
            self.all_dbs.append((unix_time, self.live_dbs()))
            self.update_stats()
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

    def db_values(self, subintervals=None):
        """Parse a new decibel reading and smooth the visualization."""
        if subintervals is None:
            subintervals = self.subintervals
        unix_time = int(time.time())
        self.db_current = self.live_dbs()
        save_reading(db=self.db_current, timestamp=unix_time)
        self.all_dbs.append((unix_time, self.db_current))
        print "before if loop"
        if len(self.all_dbs) >= 2:
            print "in if loop"
            db_prev = self.all_dbs[-2][1]
            db_now = self.all_dbs[-1][1]
            db_int = db_now - db_prev
            db_inc = db_int / float(subintervals)
            print "db_prev: {}, db_now: {}, db_int: {}, db_inc: {}" \
                    "".format(
                    db_prev, db_now, db_int, db_inc)
            # smooth the visualization display
            for i in range(0, subintervals):
                h = db_prev + (i * db_inc)
                print 'i: {}, h: {}, p: {}'.format(i, h, db_prev+(i*db_inc))
                self.draw_identical_bars(bar_height=h)
                d = self.delay / subintervals
                self.clear()
                self.draw_identical_bars(h)
                self.Canvas.after(d, self.draw_identical_bars, h)

            # update labels
            temp_average = sum(
                [e[1] for e in self.all_dbs]) / float(len(self.all_dbs))
            self.db_average = float('{0:.2f}'.format(temp_average))
            self.db_maximum = max(self.db_current, self.db_maximum)
            self.cur_value.update(self.db_current)
            self.avg_value.update(self.db_average)
            self.max_value.update(self.db_maximum)

        else:
            print "in else block"
            pass

        # call this function recursively if desired
        if self.event:
            print "in recursive block!"
            self.Canvas.after(0, self.db_values)

    def start_live_db_reading(self, ms_between_readings=None):
        """Start live tracking and outputting of decibel readings."""
        if ms_between_readings is None:
            ms_between_readings = self.delay
        self.event = 'something'
        # self.db_values()
        self.live_display()

    def clear(self):
        """Remove existing bars from the visualizer"""
        self.Canvas.delete('all')
        self.draw_frame()

    def stop_reading(self, write_results=True, filename='totalresults'):
        """Stop tracking decibel input."""
        self.event = None
        if write_results == True:
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

            json_output = json.dumps(self.all_dbs, indent=3,
                                     separators=(',', ':'))
            filename = filename + '.json'
            with open(filename, 'w+') as stream:
                stream.write(json_output)

def main():
    root = Tkinter.Tk()
    root.geometry('550x330+30+30')
    g = DecibelVisualizer(root)
    g.draw_frame()
    g.draw_multiple_bars(
        [(105, 20), (115, 50), (125, 80), (121, 110), (120, 140),
         (119, 170), (118, 200), (115, 230), (112, 260), (108, 290)]
        )

    root.mainloop()

if __name__ == '__main__':
    main()
