import math
import os
from pyairtable import Api
from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler
from dotenv import load_dotenv
import threading
from datetime import datetime, timedelta
from refreshData import refreshData

# This sample slack application uses SocketMode
# For the companion getting started setup guide,
# see: https://docs.slack.dev/tools/bolt-python/getting-started
load_dotenv()
# Initializes your app with your bot token
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.get("/")
def healthcheck():
    return "ok", 200


REFRESH_PROJECTS_TIMEOUT = timedelta(hours=16)
channel_stop_events = {}
channel_lock = threading.Lock()


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


def refresh_loop(channel_id, message_ts, client, stop_event):
    while not stop_event.is_set():
        data = refreshData()
        blocks = organizeData(data)
        client.chat_update(channel=channel_id, ts=message_ts, blocks=blocks)
        stop_event.wait(REFRESH_PROJECTS_TIMEOUT.total_seconds())

    with channel_lock:
        channel_stop_events.pop(channel_id, None)


# Listens to incoming messages that contain "hello"
@app.message("show me the leaderboard!")
def message_hello(message, say, client):
    channel_id = message["channel"]

    with channel_lock:
        if channel_id in channel_stop_events:
            client.chat_postMessage(
                channel=channel_id,
                text="Leaderboard is already running in this channel. Say 'stop leaderboard' to stop it.",
            )
            return

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

    stop_event = threading.Event()
    with channel_lock:
        channel_stop_events[channel_id] = stop_event

    worker = threading.Thread(
        target=refresh_loop,
        args=(channel_id, message_ts, client, stop_event),
        daemon=True,
    )
    worker.start()


@app.message("stop leaderboard")
def stop_leaderboard(message, say, client):
    channel_id = message["channel"]
    with channel_lock:
        stop_event = channel_stop_events.get(channel_id)

    if stop_event is None:
        client.chat_postMessage(
            channel=channel_id,
            text="No running leaderboard refresh found in this channel.",
        )
        return

    stop_event.set()
    client.chat_postMessage(channel=channel_id, text="Stopped leaderboard refresh.")


# Start your app

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    