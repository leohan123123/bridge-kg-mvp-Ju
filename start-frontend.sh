#!/bin/bash
# Script to start the frontend service

SUDO_PREFIX=""
# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
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

# Check for .env file (less critical for frontend but good for consistency)
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "INFO: .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "INFO: .env file created."
  else
    # Not exiting as .env might be less critical for frontend directly
    echo "Warning: .env file not found and .env.example is also missing."
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

# Optional: Run npm install in frontend directory if node_modules is missing
# This ensures that if the Dockerfile.dev relies on host node_modules, they are present.
# The frontend/Dockerfile.dev likely runs `npm install` itself, so this might be redundant
# but can be helpful for local consistency or specific Dockerfile.dev setups.
if [ -d "frontend" ] && [ ! -d "frontend/node_modules" ]; then
  echo "INFO: frontend/node_modules not found. Running npm install in ./frontend..."
  (cd frontend && npm install)
  if [ $? -ne 0 ]; then
    echo "Error: npm install in ./frontend failed. Please check for errors."
    # exit 1 # Decide if this should be a fatal error
  fi
elif [ ! -d "frontend" ]; then
    echo "Warning: ./frontend directory not found, skipping npm install check."
fi


# Start the frontend service using Docker Compose
echo "INFO: Starting the frontend service..."

SERVICE_STATUS=$($COMPOSE_CMD ps -q frontend 2>/dev/null)
if [ -n "$SERVICE_STATUS" ]; then
    echo "INFO: Frontend service is already running. Stopping it first..."
    $COMPOSE_CMD stop frontend
fi

$COMPOSE_CMD up -d --no-deps --build frontend

# Check if the frontend container started successfully
echo "INFO: Waiting for frontend service to start (approx 10-15 seconds)..."
sleep 15 # Vite can be quick for dev server

FRONTEND_CONTAINER_ID=$($COMPOSE_CMD ps -q frontend)
if [ -z "$FRONTEND_CONTAINER_ID" ]; then
  echo "Error: Frontend container failed to start. Check Docker Compose logs for details:"
  echo "$COMPOSE_CMD logs frontend"
  exit 1
fi

FRONTEND_CONTAINER_STATUS=$($SUDO_PREFIX docker inspect -f '{{.State.Status}}' $FRONTEND_CONTAINER_ID 2>/dev/null)
if [ "$FRONTEND_CONTAINER_STATUS" != "running" ]; then
    echo "Error: Frontend container is not running (status: $FRONTEND_CONTAINER_STATUS). Check Docker Compose logs for details:"
    echo "$COMPOSE_CMD logs frontend"
    exit 1
fi
echo "INFO: Frontend container started (ID: $FRONTEND_CONTAINER_ID, Status: $FRONTEND_CONTAINER_STATUS)."

# Health check for frontend (simple HTTP check)
# Extract frontend port from docker-compose.yml
# This regex is a bit fragile; assumes "XXXX:YYYY" format and takes the host port (XXXX)
FRONTEND_PORT=$(grep -E '^ *ports:' docker-compose.yml -A 2 | grep -A 1 'frontend:' | sed -n 's/.*-\s*"\([0-9]*\):.*/\1/p' | head -n 1)

if [ -z "$FRONTEND_PORT" ]; then
    FRONTEND_PORT="3000" # Default from docker-compose.yml
    echo "WARN: Could not dynamically determine frontend port from docker-compose.yml, defaulting to $FRONTEND_PORT."
fi
HEALTH_CHECK_URL="http://localhost:${FRONTEND_PORT}"
echo "INFO: Performing health check by trying to reach $HEALTH_CHECK_URL..."

MAX_RETRIES=3
RETRY_COUNT=0
HEALTHY=false
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  # Using curl -I to get headers, or -L to follow redirects if any, -s for silent, -o /dev/null to discard body
  # Checking for any 2xx or 3xx HTTP code as success for a basic frontend check
  RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L --max-time 5 $HEALTH_CHECK_URL)
  if [[ "$RESPONSE_CODE" =~ ^[23]..$ ]]; then # Check for 2xx or 3xx response codes
    echo "INFO: Frontend health check successful (HTTP $RESPONSE_CODE)."
    HEALTHY=true
    break
  else
    echo "INFO: Frontend health check attempt $(($RETRY_COUNT + 1)) failed (HTTP $RESPONSE_CODE). Retrying in 5 seconds..."
    RETRY_COUNT=$(($RETRY_COUNT + 1))
    sleep 5
  fi
done

if [ "$HEALTHY" = true ]; then
  echo "INFO: Frontend service started successfully and is reachable."
  echo "INFO: Frontend should be available at $HEALTH_CHECK_URL"
else
  echo "Error: Frontend service failed to become healthy after $MAX_RETRIES retries (last HTTP code: $RESPONSE_CODE)."
  echo "Error: Please check the service logs: $COMPOSE_CMD logs frontend"
  echo "Error: Also ensure the backend service is running if the frontend depends on it for its main page content."
  exit 1 # Making this a fatal error for the script
fi

exit 0
