# decibel-reader

This repository contains Python code which reads decibel levels from
a connected USB sound level meter, displays them graphically, and saves
each reading and its timestamp to disk as a JSON file. The goal is to use
this code to measure decibels in an indoor athletic arena and send
measurements to an FTP server where they can be located and displayed as
a live stat in the team's official app and on the team's official web site.

The current iteration of the decibel reader widget looks like this:

![dB reader screenshot](img/decibelviz.png "Screenshot of the decibel reader")


