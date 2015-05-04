#! /usr/bin/env python
# -*- coding: utf-8 -*-

#import usb.core
import time
import xml.etree.ElementTree
import os.path

## initialize
#dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc)
lastdb = 0

## set up XML 

def get_date_and_time():
    """ Grab current time and date; return values in 2-element list. """
    time_now = time.strftime("%H:%M:%S")
    date_today = time.strftime("%Y/%m/%d")
    return [date_today, time_now]

def get_date():
    now_date = time.strftime("%Y/%m/%d")
    return now_date

def get_time():
    now_time = time.strftime("%H:%M:%S")
    return now_time

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

def create_new_xml_file(title):
    xml_text = """<?xml version="1.0" encoding="UTF-8"?>\n<data>\n</data>"""
    xml_filename = "{}.xml".format(title)
    with open(xml_filename, "a") as stream:
        stream.write(xml_text)

def check_xml(title):
    if not os.path.isfile("{}.xml".format(title)):
        create_new_xml_file(title)
    else:
        pass

def append_to_xml(xml_file, xml_date=0, xml_time=0, xml_decibels=0):
    try:
        with open(xml_file, "a") as x:
            # get current date and time
            entry_date = time.strftime("%Y/%m/%d")
            entry_time = time.strftime("%H:%M:%S")

            # get xml structure
            tree = xml.etree.ElementTree.parse(xml_file)
            root = tree.getroot()

            
            print root
    except OSError:
        print "Failed to open XML file."

            
if __name__ == "__main__":
    #get_date_and_time()
    #read_decibels()
    #create_new_xml_file("testxml")
    my_xml_title = "output"
    check_xml(my_xml_title)
    append_to_xml(xml_file="{}.xml".format(my_xml_title))
