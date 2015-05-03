#! /usr/bin/env python
# -*- coding: utf-8 -*-

import usb.core
import time
import json

# initialize
dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc)
lastdb = 0

def get_date_and_time():
    """ Grab current time and date; return values in 2-element list. """
    time_now = time.strftime("%H:%M:%S")
    date_today = time.strftime("%Y/%m/%d")
    return [date_today, time_now]

def read_decibels():
    while True:
        try:
            ret = dev.ctrl_transfer(0xC0, 4, 0, 0, 200)
            db = (ret[0] + ((ret[1] & 3) * 256)) * 0.1 + 30
            print str(db)
            lastdb = db
            return lastdb
        except:
            # failed to read decibels, don't let it stop the whole program
            print str(lastdb)
            return lastdb


            
if __name__ == "__main__":
    get_date_and_time()
    read_decibels()
