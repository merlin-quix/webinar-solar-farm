# import the Quix Streams modules for interacting with Kafka.
# For general info, see https://quix.io/docs/quix-streams/introduction.html
from quixstreams import Application
from quixstreams.dataframe.windows import Sum, Count
from datetime import datetime, timezone, timedelta
import os

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()


def main():
    """
    Solar Panel Data Aggregation Service
    
    Consumes enriched solar panel data and aggregates it per location 
    over 1-minute tumbling windows to calculate:
    - Average power per panel per location
    - Panel count per location 
    - Total power output per location
    """

    # Create unique consumer group for local testing
    consumer_group = f"panel_aggregation_{int(datetime.now().timestamp())}"
    
    # Setup application
    app = Application(
        consumer_group=consumer_group,
        auto_create_topics=True,
        auto_offset_reset="earliest"
    )
    
    # Setup topics with default output topic name
    input_topic = app.topic(name=os.environ.get("input", "enriched_data"))
    output_topic = app.topic(name=os.environ.get("output", "downsampled_data"))
    
    # Create streaming dataframe
    sdf = app.dataframe(topic=input_topic)

    # Extract data fields for processing
    sdf = sdf.apply(lambda row: {
        "timestamp": row["data"]["timestamp"],  # nanoseconds
        "location_id": row["data"]["location_id"],
        "location_name": row["data"]["location_name"],
        "panel_id": row["data"]["panel_id"],
        "power_output": row["data"]["power_output"]
    })

    # Set timestamp for windowing (convert nanoseconds to milliseconds)
    sdf = sdf.set_timestamp(lambda value, key, timestamp, headers: value["timestamp"] // 1_000_000)

    # For counting unique panels, we need to collect them first
    # This is a workaround since we need to count unique panel_ids per window
    # We'll create a custom aggregation for this
    
    # First, let's create a more complex state to track unique panels
    def panel_initializer(value):
        """Initialize the state for panel aggregation"""
        return {"total_power": value["power_output"], "panel_ids": [value["panel_id"]], "location_name": value["location_name"]}
    
    def panel_reducer(state, value):
        """Custom reducer to track total power and unique panel IDs"""
        state["total_power"] += value["power_output"]
        if value["panel_id"] not in state["panel_ids"]:
            state["panel_ids"].append(value["panel_id"])
        if not state["location_name"]:  # Set location_name if not already set
            state["location_name"] = value["location_name"]
        
        return state

    # Group by location_id and apply 1-minute tumbling window
    sdf = (sdf
           .group_by("location_id")
           .tumbling_window(duration_ms=timedelta(minutes=1))
           .reduce(panel_reducer, panel_initializer)
           .current()
           .apply(lambda value: {
               "timestamp": datetime.fromtimestamp(value["end"] / 1000, tz=timezone.utc).isoformat(),
               "location_id": "unknown",  # Will be set below
               "location_name": value["value"]["location_name"],
               "avg_power_per_panel": round(
                   value["value"]["total_power"] / len(value["value"]["panel_ids"]) 
                   if len(value["value"]["panel_ids"]) > 0 else 0.0, 2
               ),
               "panel_count": len(value["value"]["panel_ids"]),
               "total_power_output": round(value["value"]["total_power"], 2),
               "window_start": datetime.fromtimestamp(value["start"] / 1000, tz=timezone.utc).isoformat(),
               "window_end": datetime.fromtimestamp(value["end"] / 1000, tz=timezone.utc).isoformat()
           }))
    
    # Set the location_id from the message key
    def set_location_id(value, key, timestamp, headers):
        value["location_id"] = key
        return value
    
    sdf = sdf.apply(set_location_id, metadata=True)

    # Print results for debugging
    sdf = sdf.print()

    # Send to output topic
    sdf.to_topic(output_topic)

    # Run with stop conditions for local testing
    print(f"Starting aggregation service...")
    print(f"Input topic: {input_topic.name}")
    print(f"Output topic: {output_topic.name}")
    print(f"Consumer group: {consumer_group}")
    
    app.run(timeout=30.0, count=100)


# It is recommended to execute Applications under a conditional main
if __name__ == "__main__":
    main()