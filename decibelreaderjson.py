#! /usr/bin/env python
# -*- coding: utf-8 -*-

#import usb.core
import time
import json

## initialize
#dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc)
lastdb = 0

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

def new_entry():
    entry_date = time.strftime("%Y/%m/%d")
    entry_time = time.strftime("%H:%M:%S")
    entry_decibels = 0
    # entry_decibels = ## read something
    return {"date": entry_date, "time": entry_time, "db": entry_decibels}

            
if __name__ == "__main__":
    #get_date_and_time()
    #read_decibels()
    #create_new_xml_file("testxml")
    mydata = []
    entry = new_entry()
    mydata.append(entry)
    with open('mydata.json', 'w') as f:
        f.write(json.dumps(mydata))
