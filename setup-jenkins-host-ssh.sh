#!/bin/bash

echo "Setting up SSH access from Jenkins host to app servers..."

# Generate SSH key for ec2-user on Jenkins host
if [ ! -f /home/ec2-user/.ssh/id_rsa ]; then
    sudo -u ec2-user ssh-keygen -t rsa -b 4096 -N "" -f /home/ec2-user/.ssh/id_rsa
fi

echo "Public key generated:"
cat /home/ec2-user/.ssh/id_rsa.pub

# Save public key to temp file
cat /home/ec2-user/.ssh/id_rsa.pub > /tmp/jenkins_host_key.pub

echo ""
echo "SSH key ready for app servers"
