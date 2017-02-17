#!/usr/bin/env python

import time
import serial
import re
import urllib2

# Server name of iot server
servername="homepi"

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
  # line="XP00001234 005 Brine in/Evaporator (11.7c)"
  if line:
    splitline=line.split(' (')
    label=splitline[0].split(' ')
    label='+'.join(label[2:])
    label=re.sub('/', '+', label)
    value = re.sub('[c\) ]', '', splitline[1])
    print "Label:", label
    print "Value:", value
    url="http://" + servername + "/iot/iotstore.php?id=HeatPump+" + label + "&set=" + value
    print url
    urllib2.urlopen(url).read()
  else:
    print "Waiting..."

