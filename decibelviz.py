#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Display current decibel readings with a graphical gauge."""

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

    def __init__(self, parent, width=300, height=150, min_db=30, max_db=130,
                 delay=1000):
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
        # delay between readings, in milliseconds
        self.delay = delay

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

    def draw_frame(self, title="Live Decibel Reading", unit='dB'):
        """Draw the frame and labels."""
        x1, y1 = 10, 10
        x2, y2 = 10, self.max_scale
        x3, y3 = 200, self.max_scale
        self.Canvas.create_line(x1, y1, x2, y2, x3, y3, fill='black')

    def draw_one_bar(self, bar_height=125, bar_width=10, left_edge=20):
        """Draw a single bar (for testing purposes)."""
        # more_height = True
        top_height = bar_height - ((bar_height / 10) * 10)
        # while more_height:
        bins = (bar_height / 10) + 1
        for _ in range(0, bins):
            b = bar_height / 10
            b_height = 10 if ((10 * b) + 10) < bar_height else top_height
            print 'b: {}\tb_height: {}'.format(b, b_height)
            if self.colors[b] >= 0:
                col = self.colors[b]
                x1, y1 = left_edge, b + b_height
                x2, y2 = left_edge + bar_width, b
                self.Canvas.create_rectangle(x1, y1, x2, y2, fill=col)
                bar_height = ((bar_height / 10) * 10) - 1
                if bar_height <= 0:
                    break
            else:
                break

def main():
    root = Tkinter.Tk()
    root.geometry('+30+30')
    # weight the left two columns more heavily
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    # app = DecibelReader(root)
    current = ReadoutHeading(root, text='Current Decibel Reading:')
    current.Label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
    g = DecibelVisualizer(root)
    g.draw_frame()
    g.Canvas.grid(row=2, column=1, columnspan=3, rowspan=3)

    g.draw_one_bar()

    root.mainloop()

if __name__ == '__main__':
    main()
