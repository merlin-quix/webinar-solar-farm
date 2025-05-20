# import the Quix Streams modules for interacting with Kafka.
# For general info, see https://quix.io/docs/quix-streams/introduction.html
# For sources, see https://quix.io/docs/quix-streams/connectors/sources/index.html
from quixstreams import Application
from quixstreams.sources import Source
import os
import random
import time

# for local dev, you can load env vars from a .env file
# from dotenv import load_dotenv
# load_dotenv()


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
    solar_data_source = SolarDataGenerator(name="solar-data-producer")
    output_topic = app.topic(name=os.environ["output"])

    # --- Setup Source ---
    # OPTION 1: no additional processing with a StreamingDataFrame
    # Generally the recommended approach; no additional operations needed!
    app.add_source(source=solar_data_source, topic=output_topic)

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