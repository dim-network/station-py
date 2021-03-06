#!/usr/bin/bash

ps -fe | grep "\/srv\/dims\/robots\/gbot_assistant.py" | grep -v grep
if [ $? -ne 0 ]
then
    time=`date +%Y%m%d-%H%M%S`
    stdbuf -oL /usr/local/bin/python3 /srv/dims/robots/gbot_assistant.py >> /tmp/assistant-${time}.log 2>&1 &
    echo "Group assistant is started."
else
    echo "Group assistant is running..."
fi
