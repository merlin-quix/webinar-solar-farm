from quixstreams import Application
from datetime import timedelta, datetime
import os
from dotenv import load_dotenv

# Load environment variables for local development
load_dotenv()


def main():
    """
    This service aggregates solar panel data per location over 1-minute tumbling windows.
    
    For each location within each 1-minute window, it calculates:
    - Total power output from all panels
    - Count of unique panels
    - Average power per panel
    """

    # Setup necessary objects
    app = Application(
        consumer_group="solar_panel_aggregator",
        auto_create_topics=True,
        auto_offset_reset="earliest"
    )
    
    input_topic = app.topic(name=os.environ.get("input", "enriched_data"))
    output_topic = app.topic(name=os.environ.get("output", "downsampled_data"))
    
    # Create streaming dataframe
    sdf = app.dataframe(topic=input_topic)
    
    # Extract the nested data fields to the top level for easier processing
    sdf = sdf.apply(lambda row: {
        "timestamp": row["data"]["timestamp"],
        "location_id": row["data"]["location_id"],
        "location_name": row["data"]["location_name"],
        "panel_id": row["data"]["panel_id"],
        "power_output": row["data"]["power_output"]
    })
    
    # Group by location_id and apply 1-minute tumbling window
    windowed = (
        sdf.group_by("location_id")
        .tumbling_window(duration_ms=timedelta(minutes=1))
        .reduce(
            reducer=lambda agg, row: {
                "location_id": row["location_id"],
                "location_name": row["location_name"],
                "total_power": agg["total_power"] + row["power_output"],
                "panel_ids": agg["panel_ids"] + [row["panel_id"]] if row["panel_id"] not in agg["panel_ids"] else agg["panel_ids"]
            },
            initializer=lambda row: {
                "location_id": row["location_id"],
                "location_name": row["location_name"],
                "total_power": row["power_output"],
                "panel_ids": [row["panel_id"]]
            }
        )
        .final()
        .apply(lambda row: {
            "timestamp": datetime.fromtimestamp(row["end"] / 1000).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # Convert to ISO format
            "location_id": row["value"]["location_id"],  # Get from aggregated value
            "location_name": row["value"]["location_name"],
            "panel_count": len(set(row["value"]["panel_ids"])),  # Convert to set here for unique count
            "avg_power_per_panel": row["value"]["total_power"] / len(set(row["value"]["panel_ids"])),
            "window_start": datetime.fromtimestamp(row["start"] / 1000).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "window_end": datetime.fromtimestamp(row["end"] / 1000).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        })
    )
    
    # Print for debugging (optional)
    windowed = windowed.update(lambda row: print(f"Aggregated: {row}"))
    
    # Write to output topic
    windowed.to_topic(output_topic)
    
    # Run the application
    app.run()


# It is recommended to execute Applications under a conditional main
if __name__ == "__main__":
    main()
