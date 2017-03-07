#!/usr/bin/env python

import urllib2

wanttemp=20

roomtempdevice="HTTP_Device_sensorMultilevel_122"
settempdevice="HeatPump+0203+Room+temp+setpoint"
wanttempdevice="Wanted+Indoor+Temperature"
servername="apps01"

url="http://" + servername + "/iot/iotread.php?id=" + roomtempdevice
roomtemp=float(urllib2.urlopen(url).read())
url="http://" + servername + "/iot/iotread.php?id=" + settempdevice
settemp=float(urllib2.urlopen(url).read())
url="http://" + servername + "/iot/iotread.php?id=" + wanttempdevice
wanttemp=float(urllib2.urlopen(url).read())

print "Set temp : " + str(int(settemp))
print "Want temp: " + str(wanttemp) 
print "Current  : " + str(roomtemp)

if (roomtemp >= wanttemp+1):
  newtemp = round(wanttemp,0)-2
  print "Set low  : " + str(newtemp)
elif (roomtemp >= wanttemp+0.5):
  newtemp = round(wanttemp,0)-1
  print "Set low  : " + str(newtemp)
elif (roomtemp >= wanttemp+0.2):
  newtemp = round(wanttemp,0)
  print "Set norm : " + str(newtemp)
elif (roomtemp <= wanttemp-0.5):
  newtemp = round(wanttemp,0)+2
  print "Set high : " + str(newtemp)
elif (roomtemp <= wanttemp):
  newtemp = round(wanttemp,0)+1
  print "Set high : " + str(newtemp)
else:
  newtemp = int(settemp)
  print "Keep at  : " + str(int(newtemp))

if settemp <> newtemp:
  text_file = open("/tmp/hpcommand.txt", "w")
  text_file.write("0203 %s" % str(int(newtemp)))
  text_file.close()
  print "Command queued"
else:
  print "Settemp unchanged"
