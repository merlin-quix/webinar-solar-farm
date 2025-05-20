# import the Quix Streams modules for interacting with Kafka.
# For general info, see https://quix.io/docs/quix-streams/introduction.html
# For sources, see https://quix.io/docs/quix-streams/connectors/sources/index.html
from quixstreams import Application
from quixstreams.sources import Source
import os
import random
import time


class ConfigGenerator(Source):
    """
    A Quix Streams Source that generates configuration data for solar panels.
    Emits new configuration settings every 30 seconds.
    """
    
    def __init__(self, name):
        # Initialize base class
        Source.__init__(self, name)
        
        # Time step in nanoseconds (30 seconds)
        self.time_step = 30 * 1000000000
        
        # Initialize time
        self.current_time = 1577836800000000000  # Start time
        
    def generate_next_config(self):
        """Generate a new configuration data point"""
        # Generate random values within specified ranges
        output_pct = random.randint(0, 100)
        on_off = random.choice(["ON", "OFF"])
        forecast_temp = random.randint(-40, 50)
        forecast_cloud = random.randint(0, 100)
        
        return {
            "timestamp": self.current_time,
            "output_pct": output_pct,
            "on_off": on_off,
            "forecast_temp": forecast_temp,
            "forecast_cloud": forecast_cloud
        }
    
    def run(self):
        """Generate configuration data every 30 seconds"""
        while self.running:
            try:
                # Generate next configuration
                config = self.generate_next_config()
                
                # Increment time
                self.current_time += self.time_step
                
                # Serialize and produce the event
                event_serialized = self.serialize(key="config", value=config)
                self.produce(key=event_serialized.key, value=event_serialized.value)
                print(f"Config generated at time {config['timestamp']}")
                
                # Sleep for 30 seconds between configurations
                time.sleep(30)
            except Exception as e:
                print(f"Error generating config: {str(e)}")
                break


def main():
    """Here we will set up our Application."""

    # Setup necessary objects
    app = Application(consumer_group="config_producer", auto_create_topics=True)
    config_source = ConfigGenerator(name="config-producer")
    output_topic = app.topic(name=os.environ["config_output"])

    # --- Setup Source ---
    # Generally the recommended approach; no additional operations needed!
    app.add_source(source=config_source, topic=output_topic)

    # With our pipeline defined, now run the Application
    app.run()


# Sources require execution under a conditional main
if __name__ == "__main__":
    main()
