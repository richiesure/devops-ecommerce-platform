#!/bin/bash

echo "Testing SSH connectivity from Jenkins host..."

APP1_IP="10.0.11.51"
APP2_IP="10.0.12.197"

# Add hosts to known_hosts
ssh-keyscan -H $APP1_IP >> ~/.ssh/known_hosts 2>/dev/null
ssh-keyscan -H $APP2_IP >> ~/.ssh/known_hosts 2>/dev/null

# Test connections
echo "Testing App Server 1 ($APP1_IP)..."
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$APP1_IP 'hostname'; then
    echo "Connection to App Server 1: SUCCESS"
else
    echo "Connection to App Server 1: FAILED"
fi

echo ""
echo "Testing App Server 2 ($APP2_IP)..."
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$APP2_IP 'hostname'; then
    echo "Connection to App Server 2: SUCCESS"
else
    echo "Connection to App Server 2: FAILED"
fi
