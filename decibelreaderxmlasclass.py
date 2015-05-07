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

class XMLSession(object):

    def __init__(self, title):
        self.title = title
        self.xml_filename = "{}.xml".format(self.title)
        self.empty_xml = ("""<?xml version="1.0" encoding="UTF-8"?>"""
                          """<data></data>""")

    def create_new_xml(self):
        """Create a new XML file."""
        with open(self.xml_filename, "w") as stream:
            stream.write(self.empty_xml)

    def check_xml(self):
        """Create an XML file if one doesn't already exist."""
        if not os.path.isfile(self.xml_filename):
            self.create_new_xml()
        else:
            pass

    def open_xml(self):
        """Open and read an XML file."""
        self.xml_data = ET.parse(self.xml_filename)
        self.xml_entries = self.xml_data.getroot() 

    def new_entry(self):
        """Append a new entry to an open XML file."""
        self.xml_entry = ET.Element("entry")
        self.xml_entry.attrib["date"] = "{}".format(time.strftime("%Y-%m-%d"))
        self.xml_entry.attrib["time"] = "{}".format(time.strftime("%H:%M:%S"))
        self.xml_entry.attrib["db"] = "0"
        #self.xml_entry.attrib["db"] = "{}".format(read_decibels())

        self.xml_entries.append(self.xml_entry)

    def write_xml_to_file(self):
        """Write an XML file to disk."""
        self.xml_data.write(self.xml_filename)

def main():
    my_title = "xmlclasstest"
    
    mysession = XMLSession(my_title)

    mysession.check_xml()
    mysession.open_xml()
    
    for i in range(1,10):
        mysession.new_entry()
        time.sleep(1)

    mysession.write_xml_to_file()

if __name__ == "__main__":
    main()
