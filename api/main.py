from quixstreams import Application
import os
from flask import Flask, jsonify
from flask_cors import CORS
import json

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
    
    # Parse the data into a dictionary
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

if __name__ == "__main__":
    print("Starting application")
    
    # Run Flask app on port 80 and all interfaces
    from threading import Thread
    
    # Run Quix Streams application in a separate thread
    quix_thread = Thread(target=quix_app.run, args=(sdf,))
    quix_thread.daemon = True
    quix_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=80)