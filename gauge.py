#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Display current decibel readings with a graphical gauge."""

import math
import time
import random
import Tkinter

def read_decibels(lower_bound=30, upper_bound=130):
    return random.randrange(lower_bound, upper_bound)

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
        self.text.set('{}'.format(db))

class Gauge(object):

    n_long = 0.85 # long arm of needle (relative to radius of 1.0)
    n_short = 0.3 # short arm of needle (relative to radius of 1.0)
    coef = 0.1 # coefficient representing radius of circle at gauge center
    step_distance = 25 # interval between big ticks on gauge perimeter

    def __init__(self, parent, width=400, height=400, min_db=30, max_db=130):
        """Initialize the gauge widget.

           Parameters
           ----------
             parent (Tkinter widget) : the parent object for the gauge.
             width (int) : size of the canvas (in the horizontal dimension)
             height (int) : size of the canvas (in the vertical dimension)
             min_db (int) : minimum decibel rating to show on gauge
             max_db (int) : maximum decibel rating to show on gauge

           Notes
           ----
             Default values for min_db and max_db are 30 and 130,
               respectively, because the WENSN WS1361 Digital Sound Level
               Meter this script is written for has a range of 30-130dB.
        """
        # Tkinter.Canvas.__init__(parent, width, height)
        self.Canvas = Tkinter.Canvas(parent, width=width, height=height)
        self.w = width
        self.h = height
        self.x0 = width/2 # position gauge center horizontally
        self.y0 = height/2 # position gauge center vertically
        self.rad = int(0.7*width/2) # gauge circle radius
        self.min_db = float(min_db) # minimum decibel level
        self.max_db = float(max_db) # maximum decibel level
        self.step = 5
        # set some default values for the decibel measurement displays
        self.db_current = min_db
        self.db_average = min_db
        self.db_maximum = min_db
        self.all_dbs = []
        # affiliated labels
        self.label_current = []
        self.label_average = []
        self.label_maximum = []

    def draw_gauge(self, title="Live Decibel Reading", unit="dB"):
        """Draw the gauge itself."""
        #self.title = self.create_text(self.w/2, 20, fill='#000')
        # surround the gauge in a circle of a different color
        self.Canvas.create_oval(
            self.x0-self.rad*1.1,
            self.y0-self.rad*1.1,
            self.x0+self.rad*1.1,
            self.y0+self.rad*1.1,
            fill='#DDD'
            )
        # then draw the actual gauge circle on top
        self.Canvas.create_oval(
            self.x0-self.rad,
            self.y0-self.rad,
            self.x0+self.rad,
            self.y0+self.rad,
            fill='#000'
        )
        # draw the little circle at the center of the gauge
        self.Canvas.create_oval(
            self.x0-self.rad*self.coef,
            self.y0-self.rad*self.coef,
            self.x0+self.rad*self.coef,
            self.y0+self.rad*self.coef,
            fill='#FFF'
            )
        # draw and label the tick marks around the gauge's perimeter
        min_db, max_db = self.min_db, self.max_db
        for i in xrange(1+int((max_db-min_db)/self.step)):
            db = min_db + self.step * i
            angle = (5+6*((float(db)-min_db)/
                (float(max_db)-min_db)))*math.pi/4
            self.Canvas.create_line(
                self.x0+self.rad*math.sin(angle)*0.9,
                self.y0-self.rad*math.cos(angle)*0.9,
                self.x0+self.rad*math.sin(angle)*0.98,
                self.y0-self.rad*math.cos(angle)*0.98,
                fill='#FFF', width=2
                )
            if db % 10 == 0:
                self.Canvas.create_text(
                    self.x0+self.rad*math.sin(angle)*0.75,
                    self.y0-self.rad*math.cos(angle)*0.75,
                    text=db, fill='#FFF'
                    )
            if i == float(max_db-min_db)/self.step:
                continue
            for d_db in xrange(1, 4):
                angle = (5+6*((db+d_db*(self.step/4)-min_db)/(
                    max_db-min_db)))*math.pi/4
                self.Canvas.create_line(
                    self.x0+self.rad*math.sin(angle)*0.94,
                    self.y0-self.rad*math.cos(angle)*0.94,
                    self.x0+self.rad*math.sin(angle)*0.98,
                    self.y0-self.rad*math.cos(angle)*0.98,
                    fill='#FFF'
                    )
        # draw the needle in its starting position
        self.needle = self.Canvas.create_line(
                        self.x0-self.rad*math.sin(5*math.pi/4)*self.n_short,
                        self.y0+self.rad*math.cos(5*math.pi/4)*self.n_short,
                        self.x0+self.rad*math.sin(5*math.pi/4)*self.n_long,
                        self.y0-self.rad*math.cos(5*math.pi/4)*self.n_long,
                        fill='#FFF', width=2
                        )

    def draw_needle(self, db):
        """Draw the needle."""
        # make sure that the reading doesn't exceed the gauge's scale
        db = max(db, self.min_db)
        db = min(db, self.max_db)
        angle = (5+6*((float(db)-self.min_db)/
            (float(self.max_db)-self.min_db)))*math.pi/4
        self.Canvas.coords(self.needle,
            self.x0-self.rad*math.sin(angle)*self.n_short,
            self.y0+self.rad*math.cos(angle)*self.n_short,
            self.x0+self.rad*math.sin(angle)*self.n_long,
            self.y0-self.rad*math.cos(angle)*self.n_long)

    def db_values(self):
        """Parse a new decibel reading."""
        # first add a new entry to the list of all entries
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S %Z")
        self.db_current = read_decibels()
        # and move the needle
        self.draw_needle(self.db_current)
        self.all_dbs.append((timestamp, self.db_current))
        # then recalculate the average decibel rating
        self.db_average = sum([e[1] for e in self.all_dbs])/len(self.all_dbs)
        # and the maximum
        self.db_maximum = max(self.db_current, self.db_maximum)

        for label in self.label_current:
            label.update(self.db_current)
        for label in self.label_average:
            label.update(self.db_average)
        for label in self.label_maximum:
            label.update(self.db_maximum)

        # return self.db_current, self.db_average, self.db_maximum

    def stop_reading(self):
        """Stop tracking decibel input and quit the program."""
        pass

class DecibelReader(Tkinter.Frame):
    """Main widget window."""

    def __init__(self, parent, title="Decibel Reader"):
        Tkinter.Frame.__init__(self, parent, background='white')
        self.parent = parent
        self.parent.title(title)

def main():
    root = Tkinter.Tk()
    root.geometry('500x700+100+100')
    # weight the center column more heavily so that it expands to fill grid
    root.grid_columnconfigure(1, weight=1)
    # app = DecibelReader(root)
    current = ReadoutHeading(root, text='Current Decibel Reading:')
    current.Label.grid(row=0, column=1, padx=20, pady=20)
    g = Gauge(root)
    g.draw_gauge()
    g.Canvas.grid(row=2, column=0, columnspan=3)

    db = read_decibels()

    g.draw_needle(db)
    average = ReadoutHeading(root, text="Today's Average:")
    average.Label.grid(row=3, column=0, padx=10, pady=10)
    maximum = ReadoutHeading(root, text="Today's Maximum:")
    maximum.Label.grid(row=3, column=2, padx=10, pady=10)

    current_value = ReadoutValue(root, value=db)
    average_value = ReadoutValue(root, value=db, fontsize=44)
    maximum_value = ReadoutValue(root, value=db, fontsize=44)

    current_value.Label.grid(row=1, column=1, pady=10)
    average_value.Label.grid(row=4, column=0, pady=10)
    maximum_value.Label.grid(row=4, column=2, pady=10)

    g.label_current.append(current_value)
    g.label_average.append(average_value)
    g.label_maximum.append(maximum_value)

    # buttons
    close_button = Tkinter.Button(root, text="Stop")
    close_button.grid(row=5, column=2, padx=10, pady=10)
    demo_button = Tkinter.Button(root, text="Demo",
        command=g.db_values)
    demo_button.grid(row=5, column=1, padx=10, pady=10)
    start_button = Tkinter.Button(root, text="Start")
    start_button.grid(row=5, column=0, padx=10, pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()
