#!/bin/bash

echo "Starting Python Backend for Electron..."

# Activate the virtual environment
source venv/bin/activate

# Use honcho to start the processes defined in the Procfile
honcho start
