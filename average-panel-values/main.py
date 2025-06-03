from quixstreams import Application, State
from quixstreams.models.serializers.quix import JSONDeserializer, QuixTimeseriesSerializer
import os
import json
import logging
from datetime import datetime, timedelta

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

def process_message(value):
    """Extract and process the data from the message."""
    try:
        # The actual data is in the 'data' field
        data = value.get('data', {})
        if not data:
            return None
            
        # Parse timestamp if it's a string
        timestamp = value.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = int(datetime.fromisoformat(timestamp).timestamp() * 1000000000)  # Convert to ns
            except (ValueError, TypeError):
                timestamp = int(datetime.now().timestamp() * 1000000000)
        
        return {
            'panel_id': data.get('panel_id'),
            'location_id': data.get('location_id'),
            'location_name': data.get('location_name'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'timezone': data.get('timezone'),
            'power_output': float(data.get('power_output', 0)),
            'temperature': float(data.get('temperature', 0)),
            'irradiance': float(data.get('irradiance', 0)),
            'voltage': float(data.get('voltage', 0)),
            'current': float(data.get('current', 0)),
            'timestamp': timestamp
        }
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return None

def calculate_average(panel_data: list):
    """Calculate average values for all metrics in the window."""
    if not window_data:
        return None
    
    # Filter out None values
    panel_data = [data for data in window_data if data is not None]
    if not panel_data:
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
    
    # Use the first record for location info
    first_record = panel_data[0]
    
    # Sum up all metrics
    for data in panel_data:
        metrics['power_output'] += data.get('power_output', 0)
        metrics['temperature'] += data.get('temperature', 0)
        metrics['irradiance'] += data.get('irradiance', 0)
        metrics['voltage'] += data.get('voltage', 0)
        metrics['current'] += data.get('current', 0)
        metrics['panel_count'] += 1
    
    # Calculate averages
    count = metrics.pop('panel_count')
    if count == 0:
        return None
    
    # Get the latest timestamp in the window
    latest_timestamp = max(data.get('timestamp', 0) for data in panel_data)
    
    result = {
        'location_id': first_record.get('location_id'),
        'location_name': first_record.get('location_name'),
        'latitude': first_record.get('latitude'),
        'longitude': first_record.get('longitude'),
        'timezone': first_record.get('timezone'),
        'timestamp': latest_timestamp,
        'panel_count': count,
        'avg_power_output': metrics['power_output'] / count,
        'avg_temperature': metrics['temperature'] / count,
        'avg_irradiance': metrics['irradiance'] / count,
        'avg_voltage': metrics['voltage'] / count,
        'avg_current': metrics['current'] / count,
        'window_end': latest_timestamp,
        'window_start': latest_timestamp - 60_000_000_000  # 1 minute in nanoseconds
    }
    
    return result

# Create a streaming dataframe from the input topic
sdf = app.dataframe(input_topic)

# Process each message to extract the data
sdf = sdf.apply(process_message)

# Group by location
sdf = sdf.group_by(
    key=lambda x: x.get('location_id') if x else None,
    name="group_by_location"
)

# Define a 1-minute window
window_size = timedelta(minutes=1)

# Apply the window and aggregation
sdf = sdf.window(window_size).aggregate(
    calculate_average,
    stateful=False
)

# Log the results
sdf = sdf.update(
    lambda value: logger.info(f"Processed window: {json.dumps(value, default=str)}") or value
)

# Send the result to the output topic
sdf = sdf.to_topic(output_topic)

if __name__ == "__main__":
    logger.info("Starting Average Panel Values service...")
    app.run(sdf)
