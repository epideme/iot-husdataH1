#!/usr/bin/env python

import time
import serial
import re
from subprocess import call
import os.path
import paho.mqtt.client as mqtt
import urllib2

# ---------------------------------
# Initialize variables and settings
# ---------------------------------

# First global variables. We might need them early.
wantvalue={}

# Server name of iot server and MQTT server.
# Leave one empty to ignore that protocol.
httpservername="homepi"
mqttservername="homepi"

# MQTT Settings, leave user empty for open MQTT servers.
mqttuser="pi"
mqttpassword="raspberry"
mqtttopic="heatpump"

# -------------------
# Command definitions
# -------------------

# Define command to handle when MQTT subthread connects. Tell us and subscribe to command topic.
def on_connect(client, userdata, rc):
    print("Connected MQTT with status " + str(rc))
    client.subscribe(mqtttopic + '/command/#')

# Define command to handle callback for when MQTT command "mode" arrives. Tell us and call handle_mode.
def on_message_mode(client, userdata, msg):
    print("Received mode ")
    print(msg.topic + ": " + str(msg.payload))
    command = msg.payload.decode("utf-8")
    handle_mode(command)

# Define command to handle callback for when MQTT command "temp" arrives.
# Tell us and confirm on MQTT, then call sendtoheatpump to set the new room value.
def on_message_temp(client, userdata, msg):
    print("Received temp ")
    print(msg.topic + ": " + str(msg.payload))
    command = msg.payload.decode("utf-8").lower()
    mqttc.publish(mqtttopic + "/status/temp", int(float(command)))
    sendtoheatpump('0203', int(float(command)))

# Define command to handle callback for when MQTT command "curve" arrives.
def on_message_curve(client, userdata, msg):
    print("Received curve ")
    print(msg.topic + ": " + str(msg.payload))
    command = msg.payload.decode("utf-8").lower()
    mqttc.publish(mqtttopic + "/status/curve", int(float(command)))
    sendtoheatpump('0205', int(float(command)))

# Define command to handle callback for when other commands arrive on MQTT. We ignore these.
def on_message(client, userdata, msg):
    print("Received unknown command ")
    print(msg.topic + ": " + str(msg.payload))

# Define command for handling heatpump mode commands.
# Respond on MQTT and then call sendtoheatpump.
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

# Define command to parse incoming status line (XRxxxxyyyy) from H1, and send using MQTT and/or HTTP
# Example: XR010701B8   107 Heating setpoint (44.0c)
def parseandsend(line):
    # We need the global dict to know about recent commands sent to heatpump.
    global wantvalue
    # Process the XR line to get register, value and a good readable label.
    print line
    splitline=line.split(' (')
    labels=splitline[0].split(' ')
    label=labels[4:]
    label.insert(0,labels[0][2:6])
    label='+'.join(label)
    register=labels[0][2:6]
    # Confirm there were actually a label parsed. A bit paranoid at this point.
    if label:
        # Clean up label and value from unnessecary characters
        label=re.sub('/', '+', label)
        label=re.sub(',', '', label)
        value = re.sub('[hpcd\) %]', '', splitline[1])
        # Make sure we actually got a value there
        if value:
            # Now start sending received values to MQTT and/or HTTP,
            # but dont send anything if we are waiting for a specific
            # register to be confirmed (if exists in dict wantvalue)
            if not wantvalue.has_key(register):
                if mqttservername:
                    mqttc.publish(mqtttopic + "/" + register, int(float(value)))
                    # That one there sent the raw register as an MQTT topic.
                    # Now if the line is temp, curve or mode, send those in a friendlier way.
                    if labels[0][2:6] == "0203":
                        mqttc.publish(mqtttopic + "/status/temp", int(float(value)))
                    if labels[0][2:6] == "0205":
                        mqttc.publish(mqtttopic + "/status/curve", int(float(value)))
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
            # Return a list of the register and data we saw.
            return register, int(float(value))
        else:
            # Corrupted line. No value. Make sure we return something anyway.
            return "error", "novalue"
    else:
        # Corrupted line. No label parsed. Make sure we return something.
        return "error", "nolabel"

# Define command to send XW commands through H1 interface to set heatpump settings
# Uses register (4 char hex string) and data (normally integer as int or string)
def sendtoheatpump(dataregister, svalue):
    # We need the global dict to put the newly set registers and values in, for later verification.
    global wantvalue
    # Convert value string to int, multiply 10 for one decimal and format as 2 byte HEX, then form H1 XW command.
    hexvalue=format(int(float(svalue))*10, '04X')
    sendcommand="XW" + dataregister + hexvalue + "\r"
    # Flush buffers and send XW string.
    print "Writing command: " + sendcommand
    ser.flushOutput()
    ser.flushInput()
    ser.write(sendcommand)
    # Save register and value in dict wantvalue. This is later compared to incoming values
    # to make sure it was received by the heatpump.
    if dataregister == "2201" and float(svalue) < 10:
        # For 2201 register we multiply 10 for the compare value to match later, if we havent already multiplied (resending).
        # Mode number is reported by H1 as a direct decimal from the hex data (000A = 10).
        # All other values are returned with its base at one decimal (000A = 1.0).
        wantvalue[dataregister] = int(float(svalue))*10
    else:
        wantvalue[dataregister] = int(float(svalue))

# Define command to send 2 byte (XP, XS etc.) settings to H1 interface and verify it was accepted.
# Todo: only allow 2 byte strings.
def sendtoh1(h1command):
    h1response="init"
    # Resend command every 0.5s until answer is received
    while h1response[:2] != h1command:
        print "Writing command: " + h1command
        ser.flushOutput()
        ser.flushInput()
        ser.write(h1command + "\r\n")
        h1response=ser.readline()
        h1response=re.sub('[\n\r]', '', h1response)
        print h1response
        time.sleep(0.5)
    print "Confirmed " + h1command

# Define command to reset H1 interface. Unused for now, but saved for reference.
def reseth1():
    print "Sending reset"
    ser.write("!\r\n")

# ------------------
# Start main program
# ------------------

# Set MQTT and launch its subthread, but only if we want MQTT.
if mqttservername:
    mqttc = mqtt.Client(mqtttopic)
    if mqttuser:
        mqttc.username_pw_set(mqttuser, mqttpassword)
    mqttc.message_callback_add(mqtttopic + '/command/mode', on_message_mode)
    mqttc.message_callback_add(mqtttopic + '/command/temp', on_message_temp)
    mqttc.message_callback_add(mqtttopic + '/command/curve', on_message_curve)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(mqttservername)
    mqttc.loop_start()

# Define H1 interface serial port.
ser = serial.Serial(
    port='/dev/serial0',
    baudrate = 19200,
    timeout=10
)

# Give MQTT time to connect, then clear the serial buffers and start the business.
time.sleep(1)
print "Start collection of data..."
ser.flushOutput()
ser.flushInput()

# The business... (Main loop)
while 1:
    # Read line from H1. Strip CR/LF. Times out after 10 seconds (see above)
    line=ser.readline()
    line=re.sub('[\n\r]', '', line)
    if line:
        # If we got a line (no timeout) we do checking and parsing of it
        if line[:2] == "XR":
            # Only care about lines with heatpump data. (XRxxxxyyyy)
            if len(line) <= 10:
                # If the data line is only 10 characters, we assume the H1 reset and lost its settings.
                # Make H1 send readable labels and regular full updates
                sendtoh1("XP")
                sendtoh1("XM")
            else:
                # If the data line is full expected length, work with it.
                # Call parse and send MQTT/HTTP command. Returns what data was actually used.
                parseresult = parseandsend(line)
                # Check if the data we found is waiting to be confirmed in "wantvalue" dictionary.
                if wantvalue.has_key(parseresult[0]):
                    if wantvalue[parseresult[0]] == parseresult[1]:
                        # Data received matches. No more check needed. Delete from dictionary.
                        del wantvalue[parseresult[0]]
                        print "Register " + parseresult[0] + " confirmed!"
                    else:
                        # Data received does not match. Resend command to heatpump.
                        print "Register " + parseresult[0] + " different from requested, resending..."
                        sendtoheatpump(parseresult[0], wantvalue[parseresult[0]])
    else:
        # No line was received from H1 interface. Use this time to do other things.
        if wantvalue:
            # Print out dict of values waiting for confirmation, if any.
            print wantvalue
        if os.path.exists("/tmp/hpcommand.txt"):
            # Send commands to heatpump the alternative (original, non MQTT) way.
            # Read from a text file, then delete the file.
            file = open("/tmp/hpcommand.txt", "r")
            filedata=file.read().split(' ')
            sendtoheatpump(filedata[0], filedata[1])
            file.close()
            call(["rm", "/tmp/hpcommand.txt"])
