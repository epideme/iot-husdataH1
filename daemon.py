#!/usr/bin/env python

import time
import serial
import re
import urllib2
from subprocess import call
import os.path

# Server name of iot server
servername="homepi"

ser = serial.Serial(
  port='/dev/serial0',
  baudrate = 19200,
  timeout=10
)

print "Sending reset"
ser.write("!\r\n")
print "Waiting for H1 to settle"
line=ser.readline()
while line:
  line=ser.readline()

print "Toggle readable output"
ser.write("XP\r\n")
print  "Waiting for H1 to settle"
line=ser.readline()
while line:
  line=ser.readline()

print "Toggle heatpump specific output"
ser.write("XS\r\n")
print "Waiting for H1 to settle"
line=ser.readline()
while line:
  line=ser.readline()

print "Toggle scheduled full output"
ser.write("XM\r\n")
print "Waiting for H1 to settle"
line=ser.readline()
while line:
  line=ser.readline()

print "Start collection of data..."

while 1:
  line=ser.readline()
  line=re.sub('[\n\r]', '', line)
  if line:
    print line
    splitline=line.split(' (')
    labels=splitline[0].split(' ')
    label=labels[4:]
    label.insert(0,labels[0][2:6])
    label='+'.join(label)
    if label:
      label=re.sub('/', '+', label)
      label=re.sub(',', '', label)
      value = re.sub('[hpcd\) %]', '', splitline[1])
      if value:
        url="http://" + servername + "/iot/iotstore.php?id=HeatPump+" + label + "&set=" + value
        urllib2.urlopen(url).read()
  else:
    if os.path.exists("/tmp/hpcommand.txt"):
      file = open("/tmp/hpcommand.txt", "r")
      filedata=file.read().split(' ')
      dataregister=filedata[0]
      datavalue=format(int(float(filedata[1]))*10, '04X')
      sendcommand="XW" + dataregister + datavalue + "\r"
      expectcommand="XR" + dataregister + datavalue
      waitingreply=1
      while waitingreply:
        while line<>"XW01":
          print "Writing command: " + sendcommand
          ser.flushOutput()
          ser.flushInput()
          ser.write(sendcommand)
          line=ser.readline()
          line=re.sub('[\n\r]', '', line)
          print line
	  if line[:4]=="XW00":
            waitingreply=0
            line="XW01"
        while (line and waitingreply):
          line=ser.readline()
          line=re.sub('[\n\r]', '', line)
          print "Received line " + line[:10] + " (Wanted " + expectcommand + ")"
          if line[:10] == expectcommand:
            waitingreply=0
            print "Received reply " + line[:10]

      file.close()
      call(["rm", "/tmp/hpcommand.txt"])

