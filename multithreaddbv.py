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

import ftplib
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
    print "Using non-C implementation of StringIO."

try:
    from ftpconfig import FTP_HOST, FTP_USERNAME, FTP_PASSWORD, FTP_DIR
except ImportError:
    print "FTP configuration import failed."

class DBMeterReader(object):
    """Decibel Meter Reader."""

    MIN_DB = 30
    MAX_DB = 130

    def __init__(self, *args, **kwargs):
        """Initialize the DBMeterReader object.

           Parameters
           ----------
             arg (type) :
        """
        pass

    def new_reading(self):
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
            print '{}: {}'.format(e.__doc__, e.message)
            return float('{0:.2f}'.format(float(random.randrange(
                self.MIN_DB, self.MAX_DB))))

class FTPUploader(object):
    """FTP connection with associated methods."""

    def __init__(self, *args, **kwargs):
        """Initialize the FTPUploader object.

           Parameters
           ----------
             arg (type) :
        """
        pass

class GuiDisplay(object):
    """Visualize live sound level data."""

    DEFAULTS = {
        'width': 320,
        'height': 150,
        'title': 'Live Decibel Reading',
        'units': 'dB',
        }

    def __init__(self, **kwargs):
        """Initialize the DecibelVisualizer object.

           Parameters
           ----------
             **kwargs
        """
        self._parse_kwargs(kwargs)

    def _parse_kwargs(self, **kwargs):
        """Unpack keyword arguments passed to __init__()."""
        fon k, v in kwargs.iteritems():
            setattr(self, k, v)
        for k, v in self.DEFAULTS:
            if not self.__dict__[k]:
                setattr(self, k, v)

class DecibelReaderMainApp(object):
    """docstring for DecibelReaderMainApp"""

    def __init__(self, *args, **kwargs):
        """Initialize the DecibelReaderMainApp object.

           Parameters
           ----------
             arg (type) :
        """
        self.gui = GuiDisplay()

    def read_input(self):
        """Handle the thread for incoming decibel data."""
        pass

    def send_output(self):
        """Handle the thread for sending decibel data via FTP."""
        pass

def main():
    pass

if __name__ == '__main__':
    main()
