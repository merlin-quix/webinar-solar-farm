from quixstreams import Application, State
from quixstreams.models.serializers.quix import JSONDeserializer, JSONSerializer, QuixTimeseriesSerializer
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Quix Application
app = Application(
    consumer_group="average-panel-values",
    auto_create_topics=True,
    auto_offset_reset="latest"
)

# Define input and output topics
input_topic = app.topic(
    name=os.environ["input"],
    value_deserializer=JSONDeserializer()
)

output_topic = app.topic(
    name=os.environ["output"],
    value_serializer=QuixTimeseriesSerializer()
)

def calculate_average(window_data):
    """Calculate average values for all metrics in the window."""
    values = [msg.value for msg in window_data]
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
        metrics['power_output'] += value.get('power_output', 0)
        metrics['temperature'] += value.get('temperature', 0)
        metrics['irradiance'] += value.get('irradiance', 0)
        metrics['voltage'] += value.get('voltage', 0)
        metrics['current'] += value.get('current', 0)
        metrics['panel_count'] += 1
    
    # Calculate averages
    count = metrics.pop('panel_count')
    if count == 0:
        return None
        
    result = {
        'location_id': values[0].get('location_id'),
        'location_name': values[0].get('location_name'),
        'latitude': values[0].get('latitude'),
        'longitude': values[0].get('longitude'),
        'timezone': values[0].get('timezone'),
        'timestamp': values[-1].get('timestamp', 0),  # Use the latest timestamp in the window
        'panel_count': count,
        'avg_power_output': metrics['power_output'] / count,
        'avg_temperature': metrics['temperature'] / count,
        'avg_irradiance': metrics['irradiance'] / count,
        'avg_voltage': metrics['voltage'] / count,
        'avg_current': metrics['current'] / count,
        'window_start': values[0].get('timestamp', 0),
        'window_end': values[-1].get('timestamp', 0)
    }
    
    return result

# Create a streaming dataframe from the input topic
sdf = app.dataframe(input_topic)

# Apply windowing and aggregation
sdf = sdf.apply(
    func=calculate_average,
    stateful=False,
    expand=False,
    metadata=False
).update(
    lambda value: logger.info(f"Processed window: {value}") or value
)

# Send the result to the output topic
sdf = sdf.to_topic(output_topic)

if __name__ == "__main__":
    logger.info("Starting Average Panel Values service...")
    app.run(sdf)
