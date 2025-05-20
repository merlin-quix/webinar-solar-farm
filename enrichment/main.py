import os
from quixstreams import Application
from datetime import datetime

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="enrichment-v1", 
                    auto_offset_reset="earliest", 
                    use_changelog_topics=False)

input_data_topic = app.topic(os.environ["data_topic"])
input_config_topic = app.topic(os.environ["config_topic"])
output_topic = app.topic(os.environ["output"])

data_sdf = app.dataframe(input_data_topic)
config_sdf = app.dataframe(input_config_topic)

last_config = {}

def save_config(data):
    global last_config
    print(data)
    last_config = data


config_sdf.apply(save_config)


# Filter items out without brake value.
# sdf = sdf[sdf.contains("Brake")]

# Calculate hopping window of 1s with 200ms steps.
# sdf = sdf.apply(lambda row: float(row["Brake"])) \
#         .hopping_window(1000, 200).mean().final() 

data_sdf.print()

# Create nice JSON alert message.
data_sdf = data_sdf.apply(lambda row: {
    "timestamp": str(datetime.fromtimestamp(row["timestamp"]/1000/1000/1000)),
    "data": row,
    "configuration": last_config
})

# Print JSON messages in console.
data_sdf.print()

# Send the message to the output topic
# data_sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run()