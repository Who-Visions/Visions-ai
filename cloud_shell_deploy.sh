#!/bin/bash

# Cloud Shell Deployment Script for Visions AI Reasoning Engine

echo "🚀 Starting Visions AI Reasoning Engine Deployment..."

# 1. Ensure we have the latest code
git pull origin main

# 2. Set up Python Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

# 3. Deploy
echo "Running deploy.py..."
python deploy.py

echo "✅ Script Finished. Copy the new Resource ID above and update agent.py!"
