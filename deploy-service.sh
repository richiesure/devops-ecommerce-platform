#!/bin/bash

SERVICE=$1
VERSION=${2:-latest}
APP1_IP="10.0.11.51"
APP2_IP="10.0.12.197"

echo "Deploying $SERVICE to app servers..."

# Function to deploy to a server
deploy_to_server() {
    local SERVER_IP=$1
    local SERVICE_NAME=$2
    
    echo "Deploying to $SERVER_IP..."
    
    # Copy service files
    scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        /var/jenkins_home/workspace/product-service-pipeline/${SERVICE_NAME}/${SERVICE_NAME}.tar.gz \
        ec2-user@${SERVER_IP}:/tmp/
    
    # Deploy on server
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@${SERVER_IP} << REMOTE_EOF
        cd ~/services/${SERVICE_NAME}
        tar -xzf /tmp/${SERVICE_NAME}.tar.gz
        npm install --production
        pm2 restart ${SERVICE_NAME} || pm2 start server.js --name ${SERVICE_NAME}
        rm /tmp/${SERVICE_NAME}.tar.gz
        echo "Deployment to ${SERVER_IP} complete"
REMOTE_EOF
    
    if [ $? -eq 0 ]; then
        echo "Deployment to $SERVER_IP: SUCCESS"
        return 0
    else
        echo "Deployment to $SERVER_IP: FAILED"
        return 1
    fi
}

# Deploy to both servers
deploy_to_server $APP1_IP $SERVICE &
PID1=$!

deploy_to_server $APP2_IP $SERVICE &
PID2=$!

# Wait for both deployments
wait $PID1
RESULT1=$?

wait $PID2
RESULT2=$?

# Check results
if [ $RESULT1 -eq 0 ] && [ $RESULT2 -eq 0 ]; then
    echo "Deployment successful on all servers"
    exit 0
else
    echo "Deployment failed on one or more servers"
    exit 1
fi
