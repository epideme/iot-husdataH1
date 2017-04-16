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
wantvalue={}

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
    mqttc.publish(mqtttopic + "/status/temp", int(float(command)))
    sendtoheatpump('0203', int(float(command)))

def on_message(client, userdata, msg):
    print("Received unknown command ")
    print(msg.topic + ": " + str(msg.payload))

def handle_mode(command):
    if 'Auto' == command:
        print("Set mode auto")
        mqttc.publish(mqtttopic + "/status/mode", "Auto")
        sendtoheatpump('2201', '1')
    elif 'Heatpump' == command:
        print("Set mode heatpump")
        mqttc.publish(mqtttopic + "/status/mode", "Heatpump")
        sendtoheatpump('2201', '2')
    elif 'Electricity' == command:
        print("Set mode electricity")
        mqttc.publish(mqtttopic + "/status/mode", "Electricity")
        sendtoheatpump('2201', '3')
    elif 'Water' == command:
        print("Set mode water")
        mqttc.publish(mqtttopic + "/status/mode", "Water")
        sendtoheatpump('2201', '4')
    elif 'Off' == command:
        print("Set mode off")
        mqttc.publish(mqtttopic + "/status/mode", "Off")
        sendtoheatpump('2201', '0')
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

def sendtoheatpump(dataregister, svalue):
    global wantvalue
    hexvalue=format(int(float(svalue))*10, '04X')
    sendcommand="XW" + dataregister + hexvalue + "\r"
    print "Writing command: " + sendcommand
    ser.flushOutput()
    ser.flushInput()
    ser.write(sendcommand)
    if dataregister == "2201" and float(svalue) < 10:
      wantvalue[dataregister] = int(float(svalue))*10
    else:
      wantvalue[dataregister] = int(float(svalue))      

def sendtoh1(h1command):
    h1response="init"
    while h1response[:2] <> h1command:
          print "Writing command: " + h1command
          ser.flushOutput()
          ser.flushInput()
          ser.write(h1command + "\r\n")
          h1response=ser.readline()
          h1response=re.sub('[\n\r]', '', h1response)
          print h1response
          time.sleep(0.5)
    print "Confirmed " + h1command

def reseth1():
  print "Sending reset"
  ser.write("!\r\n")
  

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
  timeout=5
)

time.sleep(1)
print "Start collection of data..."
ser.flushOutput()
ser.flushInput()

while 1:
  line=ser.readline()
  line=re.sub('[\n\r]', '', line)
  if line:
    if line[:2] == "XR":
      if len(line) <= 10:
        sendtoh1("XP")
        sendtoh1("XM")
      else:
        parseresult = parseandsend(line)
        if wantvalue.has_key(parseresult[0]):
          if wantvalue[parseresult[0]] == parseresult[1]:
            del wantvalue[parseresult[0]]
            print "Register " + parseresult[0] + " confirmed!"
          else:
            print "Register " + parseresult[0] + " different from requested, resending..."
            sendtoheatpump(parseresult[0], wantvalue[parseresult[0]])        
  else:
    if wantvalue:
      print wantvalue
    if os.path.exists("/tmp/hpcommand.txt"):
      file = open("/tmp/hpcommand.txt", "r")
      filedata=file.read().split(' ')
      sendtoheatpump(filedata[0], filedata[1])
      file.close()
      call(["rm", "/tmp/hpcommand.txt"])

