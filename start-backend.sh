#!/bin/bash
# Script to start the backend service

SUDO_PREFIX=""
# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
  # Try with sudo if direct command fails
  if ! sudo docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running or not accessible. Please start Docker and ensure you have permissions, or run this script with sudo."
    exit 1
  else
    echo "INFO: Docker is accessible with sudo. Subsequent docker/compose commands will use sudo."
    SUDO_PREFIX="sudo"
  fi
else
  echo "INFO: Docker is running and accessible."
fi

# Check for .env file and create from .env.example if it doesn't exist
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "INFO: .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "INFO: .env file created. Please review and adjust settings if necessary, especially NEO4J_PASSWORD."
  else
    echo "Error: .env file not found and .env.example is also missing. Cannot proceed."
    exit 1
  fi
fi

# Determine Docker Compose command
BASE_COMPOSE_CMD="docker compose"
if ! command -v docker compose &> /dev/null; then
    if command -v docker-compose &> /dev/null; then
        BASE_COMPOSE_CMD="docker-compose"
    else
        echo "Error: Neither 'docker compose' nor 'docker-compose' command found. Please install Docker Compose."
        exit 1
    fi
fi
COMPOSE_CMD="$SUDO_PREFIX $BASE_COMPOSE_CMD"

echo "INFO: Using '$BASE_COMPOSE_CMD' (with sudo if needed) to manage services."

# Start the backend service using Docker Compose
echo "INFO: Starting the backend service..."

# Stop backend if it's already running to ensure a clean start and apply potential .env changes
# Check if backend service is defined and running
# Need to ensure $COMPOSE_CMD is used here
SERVICE_STATUS=$($COMPOSE_CMD ps -q backend 2>/dev/null)
if [ -n "$SERVICE_STATUS" ]; then
    echo "INFO: Backend service is already running. Stopping it first..."
    $COMPOSE_CMD stop backend
fi

$COMPOSE_CMD up -d --no-deps --build backend # --no-deps to avoid starting neo4j if not needed, --build to pick up code changes

# Check if the backend container started successfully
# Give it a moment to start
echo "INFO: Waiting for backend service to start (approx 15 seconds)..."
sleep 15

BACKEND_CONTAINER_ID=$($COMPOSE_CMD ps -q backend)
if [ -z "$BACKEND_CONTAINER_ID" ]; then
  echo "Error: Backend container failed to start. Check Docker Compose logs for details:"
  echo "$COMPOSE_CMD logs backend"
  exit 1
fi

# Use SUDO_PREFIX for direct docker commands too
BACKEND_CONTAINER_STATUS=$($SUDO_PREFIX docker inspect -f '{{.State.Status}}' $BACKEND_CONTAINER_ID 2>/dev/null)
if [ "$BACKEND_CONTAINER_STATUS" != "running" ]; then
    echo "Error: Backend container is not running (status: $BACKEND_CONTAINER_STATUS). Check Docker Compose logs for details:"
    echo "$COMPOSE_CMD logs backend"
    exit 1
fi

echo "INFO: Backend container started (ID: $BACKEND_CONTAINER_ID, Status: $BACKEND_CONTAINER_STATUS)."

# Health check
BACKEND_PORT=$(grep -E '^ *ports:' docker-compose.yml -A 1 | grep -E 'backend' -A 1 | sed -n 's/.*-\s*"\([0-9]*\):.*/\1/p' | head -n 1)
if [ -z "$BACKEND_PORT" ]; then
    # Fallback to default from docker-compose if grep fails
    BACKEND_PORT="8000"
    echo "WARN: Could not dynamically determine backend port from docker-compose.yml, defaulting to $BACKEND_PORT."
fi
HEALTH_CHECK_URL="http://localhost:${BACKEND_PORT}/api/health"
echo "INFO: Performing health check at $HEALTH_CHECK_URL..."

# Retry mechanism for health check
MAX_RETRIES=5
RETRY_COUNT=0
HEALTHY=false
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_CHECK_URL)
  if [ "$RESPONSE_CODE" = "200" ]; then
    echo "INFO: Backend health check successful (HTTP $RESPONSE_CODE)."
    HEALTHY=true
    break
  else
    echo "INFO: Backend health check attempt $(($RETRY_COUNT + 1)) failed (HTTP $RESPONSE_CODE). Retrying in 5 seconds..."
    RETRY_COUNT=$(($RETRY_COUNT + 1))
    sleep 5
  fi
done

if [ "$HEALTHY" = true ]; then
  echo "INFO: Backend service started successfully and is healthy."
  echo "INFO: Backend API should be available at http://localhost:${BACKEND_PORT}"
  echo "INFO: API docs (Swagger UI) at http://localhost:${BACKEND_PORT}/docs"
else
  echo "Error: Backend service failed to become healthy after $MAX_RETRIES retries."
  echo "Error: Please check the service logs: $NEEDS_SUDO $COMPOSE_CMD logs backend"
  exit 1
fi

exit 0
