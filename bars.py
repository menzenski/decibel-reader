#!/usr/bin/env python
# -*- coding: utf-8 -*-

##########
## bars.py Version 0.1 (2015-12-05)
##
## Original author: Matthew Menzenski (menzenski@ku.edu)
##
## License: MIT ( http://opensource.org/licenses/MIT )
##
##
### The MIT License (MIT)
###
### Copyright (c) 2015 Matthew Menzenski
### Permission is hereby granted, free of charge, to any person obtaining a
### copy of this software and associated documentation files (the "Software"),
### to deal in the Software without restriction, including without limitation
### the rights to use, copy, modify, merge, publish, distribute, sublicense,
### and/or sell copies of the Software, and to permit persons to whom the
### Software is furnished to do so, subject to the following conditions:
###
### The above copyright notice and this permission notice shall be included in
### all copies or substantial portions of the Software.
###
### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
### OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
### FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
### THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
### LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
### FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
### DEALINGS IN THE SOFTWARE.
##
#########

from .ftpconfig import FTP_URL, FTP_USERNAME, FTP_PASSWORD

import ftplib
import os

def fibonacci_number(n):
    """Return the nth Fibonacci number."""
    a, b = 1, 1
    for _ in range(n-1):
        a, b = b, a+b
    return a

class FTPConnection(object):
    """Connection to the FTP server with associated methods."""

    def __init__(address, username, password, input_filename,
                 path_to_local_dir):
        """Initialize the connection object.

           Parameters
           ----------
             address (str) :
             username (str) :
             password (str) :
             input_filename (str) :
             path_to_local_dir (str) :
        """
        self.address = address
        self.username = username
        self.password = password
        self.input_filename = input_filename
        self.path_to_dir = path_to_local_dir

    def open(self):
        pass

    def close(self):
        pass

    def upload_file(self):
        pass

def main():
    pass

if __name__ == '__main__':
    main()
