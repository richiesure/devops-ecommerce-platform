#!/bin/bash

# Get Jenkins public key from SSM parameter or fetch from Jenkins
JENKINS_KEY=$(aws ssm get-command-invocation \
  --command-id "$1" \
  --instance-id "$2" \
  --region eu-west-2 \
  --query 'StandardOutputContent' \
  --output text | grep "^ssh-rsa")

if [ -z "$JENKINS_KEY" ]; then
    echo "Could not retrieve Jenkins public key"
    exit 1
fi

# Add key to authorized_keys
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Check if key already exists
if ! grep -q "$JENKINS_KEY" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "$JENKINS_KEY" >> ~/.ssh/authorized_keys
    echo "Jenkins key added successfully"
else
    echo "Jenkins key already exists"
fi
