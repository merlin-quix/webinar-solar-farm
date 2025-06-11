#!/usr/bin/env python3
"""
Test consumer to analyze the enriched_data topic structure
"""
from quixstreams import Application
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables from .env file
load_dotenv()

def main():
    # Create temporary consumer group with timestamp
    consumer_group = f"test_consumer_{int(time.time())}"
    
    # Setup application
    app = Application(
        consumer_group=consumer_group,
        auto_offset_reset="earliest"  # Read from beginning
    )
    
    # Define input topic
    input_topic = app.topic(name=os.environ["input"], value_deserializer="json")
    
    # Create StreamingDataFrame
    sdf = app.dataframe(topic=input_topic)
    
    # Counter for messages
    message_count = 0
    analyzed_fields = set()
    sample_messages = []
    
    def analyze_message(msg):
        nonlocal message_count, analyzed_fields, sample_messages
        
        message_count += 1
        
        # Capture first few messages as samples
        if message_count <= 5:
            sample_messages.append(msg)
            print(f"\n{'='*60}")
            print(f"Message #{message_count}:")
            print(json.dumps(msg, indent=2))
            
        # Analyze fields
        if isinstance(msg, dict):
            analyzed_fields.update(msg.keys())
        
        return msg
    
    # Apply analysis function
    sdf = sdf.apply(analyze_message)
    
    # Run with stop conditions
    print("Starting to consume messages from enriched_data topic...")
    print("Will stop after 100 messages or 30 seconds...\n")
    
    try:
        app.run(sdf, timeout=30.0, count=100)
    except Exception as e:
        print(f"\nError occurred: {e}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("ANALYSIS SUMMARY:")
    print(f"Total messages consumed: {message_count}")
    print(f"\nFields found in messages:")
    for field in sorted(analyzed_fields):
        print(f"  - {field}")
    
    # Try to identify key fields for aggregation
    print("\nPotential key fields for aggregation:")
    timestamp_fields = [f for f in analyzed_fields if 'timestamp' in f.lower() or 'time' in f.lower()]
    location_fields = [f for f in analyzed_fields if 'location' in f.lower()]
    panel_fields = [f for f in analyzed_fields if 'panel' in f.lower()]
    power_fields = [f for f in analyzed_fields if 'power' in f.lower() or 'output' in f.lower()]
    
    if timestamp_fields:
        print(f"  Timestamp fields: {timestamp_fields}")
    if location_fields:
        print(f"  Location fields: {location_fields}")
    if panel_fields:
        print(f"  Panel fields: {panel_fields}")
    if power_fields:
        print(f"  Power fields: {power_fields}")

if __name__ == "__main__":
    main()