#!/usr/bin/env python

import time
import urllib2
from subprocess import call

basecurve=44

roomtempdevice="HTTP_Device_sensorMultilevel_122"
outtempdevice="HeatPump+0007+Outdoor"
wanttempdevice="HeatPump+0203+Room+temp+setpoint"
setcurvedevice="HeatPump+0205+Heat+set+1+CurveL"

servername="homepi"

url="http://" + servername + "/iot/iotread.php?id=" + roomtempdevice
roomtemp=float(urllib2.urlopen(url).read())
#roomtemp=19.4
url="http://" + servername + "/iot/iotread.php?id=" + outtempdevice
outtemp=float(urllib2.urlopen(url).read())
url="http://" + servername + "/iot/iotread.php?id=" + wanttempdevice
wanttemp=float(urllib2.urlopen(url).read())
url="http://" + servername + "/iot/iotread.php?id=" + setcurvedevice
setcurve=float(urllib2.urlopen(url).read())

print "Room temp: " + str(roomtemp)
print "Out temp : " + str(outtemp)
print "Want temp: " + str(wanttemp) 
print "Current curve: " + str(setcurve)

if (roomtemp >= wanttemp+1):
  newcurve = basecurve-3
  print "Set curve: " + str(newcurve)
elif (roomtemp >= wanttemp+0.6):
  newcurve = basecurve-2
  print "Set curve: " + str(newcurve)
elif (roomtemp >= wanttemp+0.3):
  newcurve = basecurve-1
  print "Set curve: " + str(newcurve)
elif (roomtemp <= wanttemp-1):
  newcurve = basecurve+3
  print "Set curve: " + str(newcurve)
elif (roomtemp <= wanttemp-0.6):
  newcurve = basecurve+2
  print "Set curve: " + str(newcurve)
elif (roomtemp <= wanttemp-0.3):
  newcurve = basecurve+1
  print "Set curve: " + str(newcurve)
else:
  newcurve = basecurve
  print "Using base curve: " + str(int(newcurve))

text_file = open("/tmp/hpcommand.txt", "w")
text_file.write("0205 %s" % str(int(newcurve)))
text_file.close()
