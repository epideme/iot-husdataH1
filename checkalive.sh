SERVICE="daemonmqtt.py"
RESULT=`ps aux | grep $SERVICE | grep -v grep`

if [ "${RESULT:-null}" = null ]; then
    echo "not running"
    screen -dm python /home/pi/build/daemonmqtt.py
else
    echo "running"
fi
