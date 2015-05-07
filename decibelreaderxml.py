#! /usr/bin/env python
# -*- coding: utf-8 -*-

#import usb.core
import time
import os.path
from xml.etree import ElementTree as ET

## initialize usb sound meter
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

def create_new_xml(title):
    """Create a new XML file."""
    empty_xml = ("""<?xml version="1.0" encoding="UTF-8"?>"""
                 """<data></data>""")
    xml_filename = "{}.xml".format(title)
    with open(xml_filename, "w") as stream:
        stream.write(empty_xml)

def check_xml(title):
    """Create an XML file if one doesn't already exist."""
    if not os.path.isfile("{}.xml".format(title)):
        create_new_xml(title)
    else:
        pass

def new_entry():
    entry_date = time.strftime("%Y-%m-%d")
    entry_time = time.strftime("%H:%M:%S")
    entry_decibels = 0
    #entry_decibels = read_decibels()
    return '<entry date="{}" time="{}" db="{}"></entry>'.format(
        entry_date, entry_time, entry_decibels)

def update_xml_old(xml_file):
    """Append a new entry to the named XML file."""
    with open(xml_file, "a") as j:
        j.write(new_entry())

def update_xml(xml_file):
    my_xml = ET.parse("{}.xml".format(xml_file))
    my_entries = my_xml.getroot()
    
    new_entry = ET.Element("entry")
    new_entry.attrib["date"] = "{}".format(time.strftime("%Y-%m-%d"))
    new_entry.attrib["time"] = "{}".format(time.strftime("%H:%M:%S"))
    new_entry.attrib["db"] = "0"
    #new_entry.attrib["db"] = "{}".format(read_decibels())

    my_entries.append(new_entry)

if __name__ == "__main__":
    my_title = "fancyxml"
    check_xml(my_title)
    for i in range(1,10):
        update_xml(my_title)
        time.sleep(1)

    
