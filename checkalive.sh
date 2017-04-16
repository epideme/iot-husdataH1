SERVICE="daemon.py"
RESULT=`ps aux | grep $SERVICE | grep -v grep`

if [ "${RESULT:-null}" = null ]; then
    echo "not running"
    python -u /home/pi/build/daemon.py >> /var/log/heatpumplog 2>&1
else
    echo "running"
fi
