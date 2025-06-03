from quixstreams import Application, State
from quixstreams.models.serializers.quix import QuixDeserializer, QuixSerializer
import os
from datetime import datetime, timedelta
import json

# Initialize the Quix Application
app = Application(
    consumer_group="average-panel-values",
    auto_create_topics=True,
    auto_offset_reset="latest"
)

# Define input and output topics
input_topic = app.topic(os.environ["input"], value_deserializer="json")
output_topic = app.topic(os.environ["output"], value_serializer="json")

# Create a StreamingDataFrame and define the processing pipeline
sdf = app.dataframe(input_topic)

# Define the aggregation function
def calculate_averages(values: list, state: State):
    """Calculate average values for all metrics in the window."""
    if not values:
        return None
    
    # Initialize sums and counts
    metrics = {
        'power_output': 0.0,
        'temperature': 0.0,
        'irradiance': 0.0,
        'voltage': 0.0,
        'current': 0.0,
        'panel_count': 0
    }
    
    # Sum up all metrics
    for value in values:
        metrics['power_output'] += value['power_output']
        metrics['temperature'] += value['temperature']
        metrics['irradiance'] += value['irradiance']
        metrics['voltage'] += value['voltage']
        metrics['current'] += value['current']
        metrics['panel_count'] += 1
    
    # Calculate averages
    count = metrics.pop('panel_count')
    result = {
        'location_id': values[0]['location_id'],
        'location_name': values[0]['location_name'],
        'latitude': values[0]['latitude'],
        'longitude': values[0]['longitude'],
        'timezone': values[0]['timezone'],
        'timestamp': values[-1]['timestamp'],  # Use the latest timestamp in the window
        'panel_count': count,
        'avg_power_output': metrics['power_output'] / count,
        'avg_temperature': metrics['temperature'] / count,
        'avg_irradiance': metrics['irradiance'] / count,
        'avg_voltage': metrics['voltage'] / count,
        'avg_current': metrics['current'] / count,
        'window_start': values[0]['timestamp'],
        'window_end': values[-1]['timestamp']
    }
    
    return result

# Apply windowing
window = sdf.tumbling_window(
    duration_ms=60000,  # 1 minute window
    grace_ms=10000      # 10 seconds grace period for late-arriving data
)

# Apply the aggregation
aggregated = window.apply(calculate_averages, stateful=False)

# Convert the result to a dictionary
aggregated = aggregated.apply(lambda x: x)

# Publish the result to the output topic
aggregated = aggregated.to_topic(output_topic)

if __name__ == "__main__":
    print("Starting Average Panel Values service...")
    app.run(aggregated)
