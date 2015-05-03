#! /usr/bin/env python
# -*- coding: utf-8 -*-

import usb.core

# init
dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc)
lastdb = 0

def getDateTime():
    """
    Function grabs current time and date; returns values in 2-element list. """
    timeNow = time.strftime("%H:%M:%S")
    dateToday = time.strftime("%y/%m/%d")
    return [dateToday, timeNow]

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
    read_decibels()
