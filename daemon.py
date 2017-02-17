#!/usr/bin/env python

import time
import serial
import re
      
  
ser = serial.Serial(
          
  port='/dev/ttyAMA0',
  baudrate = 19200,
  timeout=10
)
counter=0

ser.write('!\r\n')
time.sleep(2)
ser.write('XP\r\n')
time.sleep(2)
  
while 1:
  line=ser.readline()
  splitline=line.split(' ')
  label=splitline[2]
  value = re.sub('(c)', '', splitline[3])
  print "Label:", label
  print "Value:", value
  print "."

