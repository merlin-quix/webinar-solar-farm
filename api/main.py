from quixstreams import Application
import os
from flask import Flask, jsonify
from flask_cors import CORS
import json
import threading

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store the last 500 data points
data_store = []

# For local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

# Initialize Quix Streams application
quix_app = Application(consumer_group="data-collector")

# Create the streaming dataframe
input_topic = quix_app.topic(os.getenv("input", ""))

if input_topic is None:
    raise ValueError("input topic is required")

# Create the streaming dataframe
sdf = quix_app.dataframe(input_topic)

def process_data(data):
    """
    Process incoming data and store it in the data store.
    Only keeps the last 500 data points.
    """
    global data_store
    
    try:
        data_dict = json.loads(data)
        
        # Add to data store
        data_store.append(data_dict)
        
        # Keep only the last 500 data points
        if len(data_store) > 500:
            data_store.pop(0)
            
    except json.JSONDecodeError:
        print(f"Error parsing data: {data}")

# Apply the processing function to incoming data
sdf = sdf.apply(process_data)

@app.route('/api/data', methods=['GET'])
def get_data():
    """
    API endpoint to get the last 500 data points
    """
    return jsonify(data_store)

def run_flask():
    """
    Function to run Flask server in a separate thread
    """
    app.run(host='0.0.0.0', port=80)

if __name__ == "__main__":
    print("Starting application")
    
    # Run Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run Quix Streams application on the main thread
    quix_app.run(sdf)