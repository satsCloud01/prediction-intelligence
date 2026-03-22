#!/bin/bash
set -euo pipefail

# ================================================================
# PredictionIntelligence — Docker ECR Deployment Script
# Usage: ./deploy.sh <EC2_IP> <SSH_KEY_PATH> [AWS_ACCOUNT_ID]
# ================================================================

EC2_IP="${1:?Usage: ./deploy.sh <EC2_IP> <SSH_KEY_PATH> [AWS_ACCOUNT_ID]}"
SSH_KEY="${2:?Usage: ./deploy.sh <EC2_IP> <SSH_KEY_PATH> [AWS_ACCOUNT_ID]}"
AWS_ACCOUNT_ID="${3:-$(aws sts get-caller-identity --query Account --output text)}"
AWS_REGION="us-east-1"

APP_NAME="prediction-intelligence"
APP_PORT="8031"
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/satszone/${APP_NAME}"
IMAGE_TAG="latest"

echo "=== Deploying PredictionIntelligence to ${EC2_IP} ==="

# 1. Build Docker image
echo "[1/5] Building Docker image..."
cd "$(dirname "$0")"
docker build -t "${APP_NAME}:${IMAGE_TAG}" .

# 2. Tag for ECR
echo "[2/5] Tagging for ECR..."
docker tag "${APP_NAME}:${IMAGE_TAG}" "${ECR_REPO}:${IMAGE_TAG}"

# 3. Login and push to ECR
echo "[3/5] Pushing to ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
    docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Create repo if it doesn't exist
aws ecr describe-repositories --repository-names "satszone/${APP_NAME}" --region "${AWS_REGION}" 2>/dev/null || \
    aws ecr create-repository --repository-name "satszone/${APP_NAME}" --region "${AWS_REGION}"

docker push "${ECR_REPO}:${IMAGE_TAG}"

# 4. Deploy on EC2
echo "[4/5] Deploying on EC2..."
ssh -i "${SSH_KEY}" "ubuntu@${EC2_IP}" << REMOTE_SCRIPT
set -euo pipefail

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Pull latest image
docker pull ${ECR_REPO}:${IMAGE_TAG}

# Stop and remove existing container
docker stop ${APP_NAME} 2>/dev/null || true
docker rm ${APP_NAME} 2>/dev/null || true

# Run new container
docker run -d \
    --name ${APP_NAME} \
    --restart unless-stopped \
    -p ${APP_PORT}:${APP_PORT} \
    ${ECR_REPO}:${IMAGE_TAG}

# Verify
sleep 3
docker ps | grep ${APP_NAME}
echo "Container running on port ${APP_PORT}"
REMOTE_SCRIPT

# 5. Health check
echo "[5/5] Health check..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${EC2_IP}:${APP_PORT}/api/health" || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "Health check passed!"
else
    echo "Warning: Health check returned ${HTTP_CODE}"
fi

echo ""
echo "Deployment complete!"
echo "  Backend:  http://${EC2_IP}:${APP_PORT}/api/health"
echo ""
