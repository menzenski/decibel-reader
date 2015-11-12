#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Display current decibel readings with a graphical gauge."""

import os
import time
import math
import Tkinter

class Gauge(object):

    N_LONG = 0.85 # long arm of needle (relative to radius of 1.0)
    N_SHORT = 0.3 # short arm of needle (relative to radius of 1.0)

    def __init__(self, parent, width=300, height=300, min_db=30, max_db=130):
        """Initialize the gauge widget.

           Parameters
           ----------
             parent (Tkinter widget) : the parent object for the gauge.
             width (int) : size of the canvas (in the horizontal dimension)
             height (int) : size of the canvas (in the vertical dimension)
             min_db (int) : minimum decibel rating to show on gauge
             max_db (int) : maximum decibel rating to show on gauge

           Notes
           -----
             Default values for min_db and max_db are 30 and 130,
               respectively, because the WENSN WS1361 Digital Sound Level
               Meter this script is written for has a range of 30-130dB.
        """
        # Tkinter.Canvas.__init__(parent, width, height)
        self.Canvas = Tkinter.Canvas(parent, width=width, height=height)
        self.w = width
        self.h = height
        self.x0 = width/2 # position gauge center horizontall
        self.y0 = height/2 # position gauge center vertically
        self.rad = int(0.7*width/2) # gauge circle radius
        self.min_db = min_db # minimum decibel level
        self.max_db = max_db # maximum decibel level
        self.step = int((max_db - min_db)/16) # distance between tick marks

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
        self.Canvas.pack()

    def draw_needle(self, dB):
        """Draw the needle."""
        pass

def main():
    root = Tkinter.Tk()
    g = Gauge(root)
    g.draw_gauge()
    root.mainloop()

if __name__ == '__main__':
    main()
