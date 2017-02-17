#!/usr/bin/env python

import time
import serial
import re
import urllib2
  
ser = serial.Serial(
  port='/dev/serial0',
  baudrate = 19200,
  timeout=10
)

print "Sending reset"
ser.write("!\r\n")
time.sleep(2)
print "Toggle readable output"
ser.write("XP\r\n")
time.sleep(2)
ser.flushInput()  
while 1:
  line=ser.readline()
  if line:
    splitline=line.split(' ')
    label=splitline[2]
    value = re.sub('(c)', '', splitline[3])
    print "Label:", label
    print "Value:", value
    urllib2.urlopen("http://localhost/iot/iotstore.php?id=" + label + "&set=" + value).read()
  else:
    print "Waiting..."

