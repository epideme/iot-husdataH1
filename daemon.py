#!/usr/bin/env python

import time
import serial
      
  
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
  x=ser.readline()
  print x
  print "."

