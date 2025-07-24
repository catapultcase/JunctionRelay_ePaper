#!/bin/bash

# Build and Push Script for E-Paper Junction Relay Docker Image

set -e

# Configuration
IMAGE_NAME="YOUR_USERNAME/junctionrelay-epaper"
VERSION="1.0.0"
PLATFORMS="linux/arm64,linux/amd64"  # Support both Pi and x86

echo "🐳 Building E-Paper Junction Relay Docker Image"
echo "Image: ${IMAGE_NAME}:${VERSION}"
echo "Platforms: ${PLATFORMS}"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Are you in the project directory?"
    exit 1
fi

# Check if Docker buildx is available
if ! docker buildx version > /dev/null 2>&1; then
    echo "❌ Error: Docker buildx not available. Please install Docker Desktop or enable buildx."
    exit 1
fi

# Create buildx builder if it doesn't exist
if ! docker buildx ls | grep -q "epaper-builder"; then
    echo "📦 Creating multi-platform builder..."
    docker buildx create --name epaper-builder --use
fi

# Build multi-platform image
echo "🔨 Building multi-platform Docker image..."
docker buildx build \
    --platform ${PLATFORMS} \
    --tag ${IMAGE_NAME}:${VERSION} \
    --tag ${IMAGE_NAME}:latest \
    --push \
    .

echo "✅ Build complete!"
echo ""
echo "🚀 Image pushed to Docker Hub:"
echo "   ${IMAGE_NAME}:${VERSION}"
echo "   ${IMAGE_NAME}:latest"
echo ""
echo "📋 To deploy on Raspberry Pi using Portainer:"
echo "   1. Copy portainer-stack.yml content"
echo "   2. Go to Portainer -> Stacks -> Add Stack"
echo "   3. Paste the YAML content"
echo "   4. Set environment variables as needed"
echo "   5. Deploy!"
echo ""
echo "🎯 Or use docker-compose directly:"
echo "   docker-compose up -d"