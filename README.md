# iot-husdataH1

Based on info from H1 Development manual
http://www.husdata.se/download.asp

Reads data from H1 interface and sends to my iotstore.php (see iot repository).

Receives commands to heatpump through file /tmp/hpcommand.txt.
File format: "XXXX nn" where XXXX is heatpump register and nn is numeric value (will be converted to integer).

Example hpcommand.txt:

<code>0203 20</code>

or

<code>0205 44.5</code>
