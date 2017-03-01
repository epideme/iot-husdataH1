SERVICE="daemon.py"
RESULT=`ps aux | grep $SERVICE | grep -v grep`

if [ "${RESULT:-null}" = null ]; then
    echo "not running"
    screen -dm python /home/pi/build/daemon.py
else
    echo "running"
fi
