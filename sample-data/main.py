# import the Quix Streams modules for interacting with Kafka.
# For general info, see https://quix.io/docs/quix-streams/introduction.html
# For sources, see https://quix.io/docs/quix-streams/connectors/sources/index.html
from quixstreams import Application
from quixstreams.sources import Source
import time
import os
import random

# for local dev, you can load env vars from a .env file
# from dotenv import load_dotenv
# load_dotenv()


class MemoryUsageGenerator(Source):
    """
    A Quix Streams Source enables Applications to read data from something other
    than Kafka and publish it to a desired Kafka topic.

    You provide a Source to an Application, which will handle the Source's lifecycle.

    In this case, we have built a new Source that reads from a static set of
    already loaded json data representing a server's memory usage over time.

    There are numerous pre-built sources available to use out of the box; see:
    https://quix.io/docs/quix-streams/connectors/sources/index.html
    """

    memory_allocation_data = [
        {"m": "mem", "host": "host1", "used_percent": 64.56, "time": 1577836800000000000},
        {"m": "mem", "host": "host2", "used_percent": 71.89, "time": 1577836801000000000},
        {"m": "mem", "host": "host1", "used_percent": 63.27, "time": 1577836803000000000},
        {"m": "mem", "host": "host2", "used_percent": 73.45, "time": 1577836804000000000},
        {"m": "mem", "host": "host1", "used_percent": 62.98, "time": 1577836806000000000},
        {"m": "mem", "host": "host2", "used_percent": 74.33, "time": 1577836808000000000},
        {"m": "mem", "host": "host1", "used_percent": 65.21, "time": 1577836810000000000},
    ]

    def run(self):
        """
        Each Source must have a `run` method.

        It will include the logic behind your source, contained within a
        "while self.running" block for exiting when its parent Application stops.

        There a few methods on a Source available for producing to Kafka, like
        `self.serialize` and `self.produce`.
        """
        data = iter(self.memory_allocation_data)
        # either break when the app is stopped, or data is exhausted
        while self.running:
            try:
                event = next(data)
                event_serialized = self.serialize(key=event["host"], value=event)
                self.produce(key=event_serialized.key, value=event_serialized.value)
                print("Source produced event successfully!")
            except StopIteration:
                print("Source finished producing messages.")
                return


class SolarDataGenerator(Source):
    """
    A Quix Streams Source that generates realistic solar panel data over time.
    Simulates power output, temperature, irradiance, voltage, current, and inverter status.
    """
    
    def __init__(self):
        # Initialize base values
        self.base_power = 250.0  # Base power output in W
        self.base_temp = 25.0    # Base temperature in C
        self.base_irradiance = 800.0  # Base irradiance in W/m²
        self.base_voltage = 24.0  # Base voltage in V
        self.base_current = 10.0  # Base current in A
        
        # Time step in nanoseconds (1 second)
        self.time_step = 1000000000
        
        # Initialize time
        self.current_time = 1577836800000000000  # Start time
        
    def generate_next_data_point(self):
        """Generate a realistic data point with all sensor readings"""
        # Simulate daily cycle (lower power at night, higher during day)
        hour = (self.current_time // 1000000000) % 86400 // 3600
        
        # Power output varies with time of day and temperature
        power_output = self.base_power * (
            0.1 + 0.9 * max(0, min(1, (hour - 6) / 6))  # Daytime curve
        ) * (1 - 0.005 * (self.base_temp + 10))  # Temperature effect
        
        # Temperature increases during day
        temperature = self.base_temp + 10 * max(0, min(1, (hour - 6) / 6))
        
        # Irradiance follows similar pattern to power
        irradiance = self.base_irradiance * max(0, min(1, (hour - 6) / 6))
        
        # Voltage slightly varies with temperature
        voltage = self.base_voltage * (1 - 0.002 * (temperature - 25))
        
        # Current is derived from power and voltage
        current = power_output / voltage
        
        # Add some random noise to make it more realistic
        power_output += random.uniform(-5, 5)
        temperature += random.uniform(-1, 1)
        irradiance += random.uniform(-10, 10)
        voltage += random.uniform(-0.5, 0.5)
        current += random.uniform(-0.1, 0.1)
        
        return {
            "panel_id": "P001",
            "power_output": round(power_output, 1),
            "unit_power": "W",
            "temperature": round(temperature, 1),
            "unit_temp": "C",
            "irradiance": round(irradiance, 1),
            "unit_irradiance": "W/m²",
            "voltage": round(voltage, 1),
            "unit_voltage": "V",
            "current": round(current, 1),
            "unit_current": "A",
            "inverter_status": "OK" if power_output > 0 else "STANDBY",
            "timestamp": self.current_time
        }
    
    def run(self):
        """Generate data points every second"""
        while self.running:
            try:
                # Generate next data point
                event = self.generate_next_data_point()
                
                # Increment time
                self.current_time += self.time_step
                
                # Serialize and produce the event
                event_serialized = self.serialize(key=event["panel_id"], value=event)
                self.produce(key=event_serialized.key, value=event_serialized.value)
                print(f"Source produced event at time {event['timestamp']}")
                
                # Sleep for 1 second between data points
                time.sleep(1)
            except Exception as e:
                print(f"Error generating data: {str(e)}")
                break



def main():
    """ Here we will set up our Application. """

    # Setup necessary objects
    app = Application(consumer_group="data_producer", auto_create_topics=True)
    memory_usage_source = MemoryUsageGenerator(name="memory-usage-producer")
    solar = SolarDataGenerator(name="solar-data-generator")
    output_topic = app.topic(name=os.environ["output"])

    # --- Setup Source ---
    # OPTION 1: no additional processing with a StreamingDataFrame
    # Generally the recommended approach; no additional operations needed!
    app.add_source(source=memory_usage_source, topic=output_topic)

    # OPTION 2: additional processing with a StreamingDataFrame
    # Useful for consolidating additional data cleanup into 1 Application.
    # In this case, do NOT use `app.add_source()`.
    # sdf = app.dataframe(source=source)
    # <sdf operations here>
    # sdf.to_topic(topic=output_topic) # you must do this to output your data!

    # With our pipeline defined, now run the Application
    app.run()


#  Sources require execution under a conditional main
if __name__ == "__main__":
    main()
