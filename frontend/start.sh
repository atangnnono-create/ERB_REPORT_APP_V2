#!/bin/bash

echo "Starting on port: $PORT"

# Install dependencies
pip install -r requirements.txt

# Start with port from environment variable

streamlit run frontend/home.py --server.port="$PORT"