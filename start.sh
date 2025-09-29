#!/bin/bash

# Use Railway's PORT or default to 8000
PORT=${PORT:-8000}

# Start the application
uvicorn main:app --host 0.0.0.0 --port $PORT
