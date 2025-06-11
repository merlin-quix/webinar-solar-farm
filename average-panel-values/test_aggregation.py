#!/usr/bin/env python3
"""
Test script for the aggregation service with stop conditions
"""
from quixstreams import Application
from quixstreams.dataframe.windows import Sum, Collect
from datetime import timedelta, datetime
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    # Create temporary consumer group with timestamp
    consumer_group = f"test_aggregation_{int(time.time())}"
    
    # Setup necessary objects
    app = Application(
        consumer_group=consumer_group,
        auto_create_topics=True,
        auto_offset_reset="earliest"
    )
    
    # Define topics with explicit deserializer/serializer
    input_topic = app.topic(name=os.environ["input"], value_deserializer="json")
    output_topic = app.topic(name=os.environ["output"], value_serializer="json")
    
    # Create StreamingDataFrame
    sdf = app.dataframe(topic=input_topic)
    
    # Extract the nested data fields
    sdf = sdf.apply(lambda msg: {
        "timestamp": msg["data"]["timestamp"],  # nanoseconds
        "location_id": msg["data"]["location_id"],
        "location_name": msg["data"]["location_name"],
        "panel_id": msg["data"]["panel_id"],
        "power_output": msg["data"]["power_output"]
    })
    
    # Group by location_id and apply 1-minute tumbling window with aggregations
    sdf = (
        sdf.group_by("location_id")
        .tumbling_window(duration_ms=timedelta(seconds=10))  # 10 second window for testing
        .agg(
            total_power_output=Sum("power_output"),
            panel_ids=Collect("panel_id")
        )
        .final()  # Note: Using final() means windows only emit when closed
    )
    
    # Transform the aggregated results into the desired output format
    def format_output(result, key, timestamp, headers):
        # Count unique panel IDs
        unique_panels = set(result["panel_ids"])
        panel_count = len(unique_panels)
        
        # Calculate average power per panel
        avg_power_per_panel = result["total_power_output"] / panel_count if panel_count > 0 else 0
        
        # Convert window timestamps from milliseconds to ISO format
        window_start_dt = datetime.fromtimestamp(result["start"] / 1000.0)
        window_end_dt = datetime.fromtimestamp(result["end"] / 1000.0)
        
        # Get location_id from key
        location_id = key if key else "UNKNOWN"
        
        return {
            "timestamp": window_end_dt.isoformat() + "Z",
            "location_id": location_id,
            "location_name": location_id + " Farm",  # Will be improved with state store later
            "avg_power_per_panel": round(avg_power_per_panel, 2),
            "panel_count": panel_count,
            "window_start": window_start_dt.isoformat() + "Z",
            "window_end": window_end_dt.isoformat() + "Z"
        }
    
    sdf = sdf.apply(format_output, metadata=True)
    
    # Print results for debugging
    print("Aggregated window results:")
    print("-" * 80)
    sdf = sdf.print(metadata=False)
    
    # Write results to output topic
    sdf.to_topic(output_topic)

    # Run the Application with stop conditions
    print(f"Starting aggregation service...")
    print(f"Consumer group: {consumer_group}")
    print(f"Input topic: {os.environ['input']}")
    print(f"Output topic: {os.environ['output']}")
    print("Will stop after 1000 messages or 30 seconds...\n")
    
    try:
        app.run(timeout=30.0, count=1000)
    except Exception as e:
        print(f"\nError occurred: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()