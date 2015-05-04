#! /usr/bin/env python
# -*- coding: utf-8 -*-

#import usb.core
import time
import json
import os.path

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

def create_new_json(title):
    """Create a new json file."""
    empty_json = "[]"
    json_filename = "{}.json".format(title)
    with open(json_filename, "w") as stream:
        stream.write(empty_json)

def check_json(title):
    """Create a json file if one doesn't already exist."""
    if not os.path.isfile("{}.json".format(title)):
        create_new_json(title)
    else:
        pass

def new_entry():
    entry_date = time.strftime("%Y/%m/%d")
    entry_time = time.strftime("%H:%M:%S")
    entry_decibels = 0
    # entry_decibels = ## read something
    return {"date": entry_date, "time": entry_time, "db": entry_decibels}

def update_json(json_file):
    
    with open(json_file, "r") as j:
        data = json.load(j)

    data.append(new_entry())

    with open(json_file, "w") as j:
        j.write(json.dumps(data, indent=4))

            
if __name__ == "__main__":
    my_title = "fancyjson"
    check_json(my_title)
    update_json("{}.json".format(my_title))
    
