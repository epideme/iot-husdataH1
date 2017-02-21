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
line=ser.readline()
line=re.sub('[\n\r]', '', line)
print line
while line:
  line=ser.readline()
  line=re.sub('[\n\r]', '', line)
  print line

print "Toggle readable output"
ser.write("XP\r\n")
line=ser.readline()
line=re.sub('[\n\r]', '', line)
print line
while line:
  line=ser.readline()
  line=re.sub('[\n\r]', '', line)
  print line
print "Toggle heatpump specific output"
ser.write("XS\r\n")
line=ser.readline()
line=re.sub('[\n\r]', '', line)
print line
while line:
  line=ser.readline()
  line=re.sub('[\n\r]', '', line)
  print line
print "Toggle scheduled full output"
ser.write("XM\r\n")
line=ser.readline()
line=re.sub('[\n\r]', '', line)
print line
while line:
  line=ser.readline()
  line=re.sub('[\n\r]', '', line)
  print line
while 1:
  line=ser.readline()
  line=re.sub('[\n\r]', '', line)
  print line
  # line="XP00001234 005 Brine in/Evaporator (11.7c)"
  if line:
    splitline=line.split(' (')
    labels=splitline[0].split(' ')
    label=labels[4:]
    label.insert(0,labels[0][:6])
    label='+'.join(label)
    if label:
      label=re.sub('/', '+', label)
      value = re.sub('[hpcd\) %,]', '', splitline[1])
      if value:
        print "Label:", label
        print "Value:", value
        url="http://" + servername + "/iot/iotstore.php?id=HeatPump+" + label + "&set=" + value
        print url
        urllib2.urlopen(url).read()
  else:
    print "Waiting..."

