import math
import os
from pyairtable import Api
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from datetime import datetime, timedelta
from refreshData import refreshData

# This sample slack application uses SocketMode
# For the companion getting started setup guide,
# see: https://docs.slack.dev/tools/bolt-python/getting-started
load_dotenv()
# Initializes your app with your bot token
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


REFRESH_PROJECTS_TIMEOUT = timedelta(minutes=5)


def makeBlock(slack_id, hours, lastProject, rank):
    print(slack_id)
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f":sleepover-{rank+1}: <@{slack_id}> with {hours} hours, working on {lastProject[0]} {" ".join(f"and {proj}" for proj in lastProject[1:])}!!",
        },
    }


def organizeData(data):
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "top sleepers!!!!!!! :pancake-sleeping:",
                "emoji": True,
            },
            "level": 1,
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "showcasing the top sleepers and their hours within the last *24 hours*.",
            },
        },
    ]
    for i, row in enumerate(data.values()):
        print(row)
        block = makeBlock(
            row.slack_id, math.ceil(row.total_hours / 60), row.projects, i
        )
        blocks.append(block)
    return blocks


# Listens to incoming messages that contain "hello"
@app.message("show me the leaderboard!")
def message_hello(message, say, client):
    channel_id = message["channel"]

    response = client.chat_postMessage(
        channel=channel_id,
        blocks=[
            {
                "type": "section",
                "text": {"type": "plain_text", "text": "ok, one sec!!!", "emoji": True},
            }
        ],
    )
    message_ts = response["ts"]

    print("running")
    data = refreshData()
    blocks = organizeData(data)
    client.chat_update(channel=channel_id, ts=message_ts, blocks=blocks)
    last_refresh = datetime.now()
    while False:
        if datetime.now() - last_refresh > REFRESH_PROJECTS_TIMEOUT:
            # data = refreshData()
            client.chat_update(channel=channel_id, ts=message_ts, blocks=blocks)
        # last_refresh = datetime.now()


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
