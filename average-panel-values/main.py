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

from quixstreams.dataframe.windows import Aggregator

class PanelAggregator(Aggregator):
    def initialize(self):
        return {
            'power_output_sum': 0.0,
            'temperature_sum': 0.0,
            'irradiance_sum': 0.0,
            'voltage_sum': 0.0,
            'current_sum': 0.0,
            'panel_count': 0,
            'location_info': None,
            'latest_timestamp': 0
        }

    def agg(self, old, new, ts):
        # Store location info from the first record
        if old['location_info'] is None:
            old['location_info'] = {
                'location_id': new.get('location_id'),
                'location_name': new.get('location_name'),
                'latitude': new.get('latitude'),
                'longitude': new.get('longitude'),
                'timezone': new.get('timezone')
            }
        
        # Update metrics
        old['power_output_sum'] += float(new.get('power_output', 0))
        old['temperature_sum'] += float(new.get('temperature', 0))
        old['irradiance_sum'] += float(new.get('irradiance', 0))
        old['voltage_sum'] += float(new.get('voltage', 0))
        old['current_sum'] += float(new.get('current', 0))
        old['panel_count'] += 1
        
        # Track the latest timestamp
        timestamp = new.get('timestamp', 0)
        if timestamp > old['latest_timestamp']:
            old['latest_timestamp'] = timestamp
            
        return old

    def result(self, stored):
        if stored['panel_count'] == 0:
            return None
            
        location = stored['location_info'] or {}
        count = stored['panel_count']
        
        return {
            'location_id': location.get('location_id'),
            'location_name': location.get('location_name'),
            'latitude': location.get('latitude'),
            'longitude': location.get('longitude'),
            'timezone': location.get('timezone'),
            'timestamp': stored['latest_timestamp'],
            'panel_count': count,
            'avg_power_output': stored['power_output_sum'] / count,
            'avg_temperature': stored['temperature_sum'] / count,
            'avg_irradiance': stored['irradiance_sum'] / count,
            'avg_voltage': stored['voltage_sum'] / count,
            'avg_current': stored['current_sum'] / count,
            'window_end': stored['latest_timestamp'],
            'window_start': stored['latest_timestamp'] - 60_000_000_000  # 1 minute in ns
        }

# Create a streaming dataframe from the input topic
sdf = app.dataframe(input_topic)

# Process each message to extract the data
sdf = sdf.apply(process_message)

# Define a 1-minute window and apply aggregation
window_size = timedelta(minutes=1)

# Apply the window and aggregation
sdf = (
    # sdf.group_by(lambda x: x.get('location_id') if x else None)
    .tumbling_window(window_size)
    .agg(value=PanelAggregator())
    .current()
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
