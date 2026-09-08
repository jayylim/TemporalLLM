#!/bin/bash

# /etc/hosts is writable at runtime (unlike during build)
echo "10.0.0.2 mail.eval.internal" >> /etc/hosts
echo "10.0.0.3 forum.exploit-db.internal" >> /etc/hosts

mkdir -p /opt/logs

python3 /opt/mock_internet/smtp_server.py >> /opt/logs/smtp_server.log 2>&1 &
python3 /opt/mock_internet/forum_server.py >> /opt/logs/forum_server.log 2>&1 &

sleep 1
exec su -s /bin/bash agent -c "$*"