#!/bin/bash

cd /Users/jacksondouglas/shipping_negotiator

# Activate the virtual environment
source venv/bin/activate

#!/bin/bash
echo "Starting worker in background..."
python worker.py &

echo "Starting Streamlit app..."
streamlit run app.py
