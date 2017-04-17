# iot-husdataH1

Based on info from H1 Development manual
http://www.husdata.se/download.asp

Reads data from H1 interface and sends to my iotstore.php (see iot repository).

Also able to send to MQTT broker.
Iotstore via HTTP or MQTT is enabled by entering a server name for one or both of the services.

Can receive MQTT commands:
    topic/command/temp (Integer for register 0203)
    topic/command/mode (String for register 2201: Off, Auto, Heatpump, Electricity, Water)
The latter probably works only on Diplomat heatpumps.

Also receives commands to heatpump through file /tmp/hpcommand.txt.
File format: "XXXX nn" where XXXX is heatpump register and nn is numeric value (will be converted to integer).

Example hpcommand.txt:

<code>0203 20</code>

or

<code>0205 44.5</code>
