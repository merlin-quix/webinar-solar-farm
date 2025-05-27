import os
from quixstreams import Application
from datetime import datetime

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="enrichment-v1-test", 
                    auto_offset_reset="earliest", 
                    use_changelog_topics=False)

input_data_topic = app.topic(os.environ["data_topic"])
input_config_topic = app.topic(os.environ["config_topic"])
output_topic = app.topic(os.environ["output"])

data_sdf = app.dataframe(input_data_topic)
config_sdf = app.dataframe(input_config_topic)

def on_merge(left: dict, right: dict):
    left['config'] = right
    return left


data_sdf = data_sdf.join_asof(config_sdf)

# Create nice JSON alert message.
# data_sdf = data_sdf.apply(lambda row: {
#     "timestamp": str(datetime.fromtimestamp(row["timestamp"]/1000/1000/1000)),
#     "data": row,
#     "configuration": last_config
# })

# Print JSON messages in console.
data_sdf.print()

# Send the message to the output topic
# data_sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run()