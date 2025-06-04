import os
from quixstreams import Application
from datetime import datetime

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(
    consumer_group="enrichment-v2",
    auto_offset_reset="earliest",
    use_changelog_topics=False,
    )

input_data_topic = app.topic(os.environ["data_topic"])
input_config_topic = app.topic(os.environ["config_topic"])
output_topic = app.topic(os.environ["output"])

data_sdf = app.dataframe(input_data_topic)
config_sdf = app.dataframe(input_config_topic)


def on_merge(left: dict, right: dict):
    """
    Merge left and right sides of the join into a new dictionary
    """
    timestamp = left.pop("timestamp")
    date_str = str(datetime.fromtimestamp(timestamp/1000/1000/1000))
    right['timestamp'] = str(datetime.fromtimestamp(right['timestamp']/1000/1000/1000))
    return {"timestamp": date_str, "data": left, "config": right}


# data_sdf = data_sdf.group_by(groupby_custom, name="unique_name")
data_sdf = data_sdf.group_by("location_id")

print("/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*")
data_sdf.print(metadata=True)
config_sdf.print(metadata=True)
print("/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*")

# Join the latest effective config with the data
data_sdf = data_sdf.join_asof(config_sdf, on_merge=on_merge)

# Send the message to the output topic
# data_sdf.to_topic(output_topic)
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
# data_sdf.print(metadata=True)
data_sdf.print_table()
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

if __name__ == "__main__":
    app.run()