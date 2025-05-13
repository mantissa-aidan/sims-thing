#!/bin/bash

# Script to build and run the sims-thing Docker container

IMAGE_NAME="sims-thing"
CONTAINER_NAME="sims-thing-container"

# Default environment variables
# These are suitable for running MongoDB and Ollama locally and accessing them from Docker Desktop (Mac/Windows)
DEFAULT_MONGO_URI="mongodb://host.docker.internal:27017/sims_mud_db"
DEFAULT_OLLAMA_URL="http://host.docker.internal:11434"

# Use provided arguments or defaults
MONGO_URI=${1:-$DEFAULT_MONGO_URI}
OLLAMA_URL=${2:-$DEFAULT_OLLAMA_URL}

# Build the Docker image
echo "Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "Docker build failed. Exiting."
    exit 1
fi

echo "Build successful."

# Stop and remove existing container with the same name, if it exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container: $CONTAINER_NAME..."
    docker stop $CONTAINER_NAME > /dev/null
    docker rm $CONTAINER_NAME > /dev/null
    echo "Existing container stopped and removed."
fi

# Run the Docker container
echo "Running Docker container: $CONTAINER_NAME..."
echo "Using MONGODB_URI: $MONGO_URI"
echo "Using OLLAMA_BASE_URL: $OLLAMA_URL"

# -v "$(pwd)":/app mounts the current directory on the host to /app in the container
# This enables hot-reloading for Flask development server
docker run -d -p 5001:5001 \
    -v "$(pwd)":/app \
    -e MONGODB_URI="$MONGO_URI" \
    -e OLLAMA_BASE_URL="$OLLAMA_URL" \
    --name $CONTAINER_NAME \
    $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo "Container $CONTAINER_NAME started successfully with hot-reloading enabled."
    echo "Application should be accessible on http://localhost:5001"
    echo "To see logs: docker logs -f $CONTAINER_NAME"
    echo "To stop: docker stop $CONTAINER_NAME"
else
    echo "Failed to start Docker container."
    exit 1
fi

exit 0 