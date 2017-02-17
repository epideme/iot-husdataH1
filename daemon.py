#!/usr/bin/env python

import time
import serial
import re
      
  
ser = serial.Serial(
          
  port='/dev/serial0',
  baudrate = 19200,
  timeout=10
)
counter=0

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
  else:
    print "Waiting..."

