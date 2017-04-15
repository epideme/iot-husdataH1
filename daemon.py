#!/usr/bin/env python

import time
import serial
import re
from subprocess import call
import os.path
import paho.mqtt.client as mqtt
import urllib2

# Server name of iot server and mqtt server
# Leave one empty to ignore
httpservername="homepi"
mqttservername="homepi"
mqttuser="pi"
mqttpassword="raspberry"
mqtttopic="heatpump"

def on_connect(client, userdata, rc):
    print("Connected MQTT with status " + str(rc))
    client.subscribe(mqtttopic + '/command/#')

def on_message_mode(client, userdata, msg):
    print("Received mode ")
    print(msg.topic + ": " + str(msg.payload))
    command = msg.payload.decode("utf-8")
    handle_mode(command)

def on_message_temp(client, userdata, msg):
    print("Received temp ")
    print(msg.topic + ": " + str(msg.payload))
    command = msg.payload.decode("utf-8").lower()
    write_commandfile('0203 ' + command)
    mqttc.publish(mqtttopic + "/status/temp", int(float(command)))

def on_message(client, userdata, msg):
    print("Received unknown command ")
    print(msg.topic + ": " + str(msg.payload))

def handle_mode(command):
    if 'Auto' == command:
        print("Set mode auto")
        write_commandfile('2201 1')
        mqttc.publish(mqtttopic + "/status/mode", "Auto")
    elif 'Heatpump' == command:
        print("Set mode heatpump")
        write_commandfile('2201 2')
        mqttc.publish(mqtttopic + "/status/mode", "Heatpump")
    elif 'Electricity' == command:
        print("Set mode electricity")
        write_commandfile('2201 3')
        mqttc.publish(mqtttopic + "/status/mode", "Electricity")
    elif 'Water' == command:
        print("Set mode water")
        write_commandfile('2201 4')
        mqttc.publish(mqtttopic + "/status/mode", "Water")
    elif 'Off' == command:
        print("Set mode off")
        write_commandfile('2201 0')
        mqttc.publish(mqtttopic + "/status/mode", "Off")
    else:
        print("Unknown command!")

def write_commandfile(commandline):
    f = open('/tmp/hpcommand.txt', 'w')
    f.write(commandline)
    f.close()

def parseandsend(line):
    global wantvalue
    print line
    splitline=line.split(' (')
    labels=splitline[0].split(' ')
    label=labels[4:]
    label.insert(0,labels[0][2:6])
    label='+'.join(label)
    register=labels[0][2:6]
    if label:
      label=re.sub('/', '+', label)
      label=re.sub(',', '', label)
      value = re.sub('[hpcd\) %]', '', splitline[1])
      if value:
       if not wantvalue.has_key(register):
        if mqttservername:
          mqttc.publish(mqtttopic + "/" + register, int(float(value)))
          if labels[0][2:6] == "0203":
            mqttc.publish(mqtttopic + "/status/temp", int(float(value)))
          if labels[0][2:6] == "2201":
            if int(float(value)) == 0:
              mqttc.publish(mqtttopic + "/status/mode", "Off")
            if int(float(value)) == 10:
              mqttc.publish(mqtttopic + "/status/mode", "Auto")
            if int(float(value)) == 20:
              mqttc.publish(mqtttopic + "/status/mode", "Heatpump")
            if int(float(value)) == 30:
              mqttc.publish(mqtttopic + "/status/mode", "Electricity")
            if int(float(value)) == 40:
              mqttc.publish(mqtttopic + "/status/mode", "Water")
	if httpservername:
          url="http://" + httpservername + "/iot/iotstore.php?id=HeatPump+" + label + "&set=" + value
          urllib2.urlopen(url).read()
       return register, int(float(value))
      else:
        return "0000", "0"
    else:
      return "0000", "0"

def sendtoheatpump(dataregister, value):
    global wantvalue
    hexvalue=format(int(float(value))*10, '04X')
    sendcommand="XW" + dataregister + hexvalue + "\r"
    line="something"
    while line<>"XW01":
      print "Writing command: " + sendcommand
      ser.flushOutput()
      ser.flushInput()
      ser.write(sendcommand)
      line=ser.readline()
      line=re.sub('[\n\r]', '', line)
      print line
      if line[:4]=="XW00":
        print "Command not accepted"
        line="XW01"
        return False
    if dataregister == "2201":
      wantvalue[dataregister] = int(float(value))*10
    else:
      wantvalue[dataregister] = int(float(value))      

if mqttservername:
  mqttc = mqtt.Client(mqtttopic)
  if mqttuser:
    mqttc.username_pw_set(mqttuser, mqttpassword)
  mqttc.message_callback_add(mqtttopic + '/command/mode', on_message_mode)
  mqttc.message_callback_add(mqtttopic + '/command/temp', on_message_temp)
  mqttc.on_connect = on_connect
  mqttc.on_message = on_message
  mqttc.connect(mqttservername)
  mqttc.loop_start()

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
ser.flushOutput()
ser.flushInput()
ser.write("XP\r\n")
#print  "Waiting for H1 to settle"
line=ser.readline()
print line
line=ser.readline()
while line:
  line=ser.readline()

print "Toggle heatpump specific output"
ser.flushOutput()
ser.flushInput()
ser.write("XS\r\n")
#print "Waiting for H1 to settle"
line=ser.readline()
print line
line=ser.readline()
while line:
  line=ser.readline()

print "Toggle scheduled full output"
ser.flushOutput()
ser.flushInput()
ser.write("XM\r\n")
#print "Waiting for H1 to settle"
line=ser.readline()
print line
line=ser.readline()
while line:
  line=ser.readline()

wantvalue={}

print "Start collection of data..."
ser.flushOutput()
ser.flushInput()
while 1:
  line=ser.readline()
  line=re.sub('[\n\r]', '', line)
  if line:
    parseresult = parseandsend(line)
    if wantvalue.has_key(parseresult[0]):
      if wantvalue[parseresult[0]] == parseresult[1]:
        del wantvalue[parseresult[0]]
        print "Register " + parseresult[0] + " confirmed!"
      else:
        print "Register " + parseresult[0] + " different from requested, resending..."
        sendtoheatpump(parseresult[0], wantvalue[parseresult[0]])
        
  else:
    print wantvalue
    if os.path.exists("/tmp/hpcommand.txt"):
      file = open("/tmp/hpcommand.txt", "r")
      filedata=file.read().split(' ')
      sendtoheatpump(filedata[0], filedata[1])
      file.close()
      call(["rm", "/tmp/hpcommand.txt"])

