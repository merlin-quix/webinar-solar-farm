import os
from quixstreams import Application
from datetime import datetime

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="danger-v2", 
                auto_offset_reset="earliest", 
                use_changelog_topics=False)

input_topic = app.topic(os.environ["input"])
output_topic = app.topic(os.environ["output"])

sdf = app.dataframe(input_topic)

# Filter items out without data and config values.
sdf = sdf[sdf.contains("data")]
sdf = sdf[sdf.contains("configuration")]

def check_for_danger(row):
    # print(row)
    panel_temp = float(row["data"]["temperature"])

    if "forecast_temp" in row["configuration"]:
        forecast_temp = float(row["configuration"]["forecast_temp"])
        forecast_cloud = float(row["configuration"]["forecast_cloud"])
    else:
        return {}

    if panel_temp > 25 and forecast_temp > 40 and forecast_cloud < 40:
        row["danger"] = True
    else:
        row["danger"] = False

    return row



# Calculate hopping window of 1s with 200ms steps.
sdf = sdf.apply(check_for_danger)
#         .hopping_window(1000, 200).mean().final() 

sdf = sdf[sdf.contains("data")]

sdf.apply(lambda row: print(row["danger"]))

# Filter only windows where danger is True
sdf = sdf[sdf["danger"] is True]
sdf.print()

# Send the message to the output topic
# sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run()