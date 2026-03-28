import os
from pyairtable import Api
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from datetime import datetime, timedelta
import array

# This sample slack application uses SocketMode
# For the companion getting started setup guide,
# see: https://docs.slack.dev/tools/bolt-python/getting-started
load_dotenv()
# Initializes your app with your bot token
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
api = Api(os.environ.get('AIRTABLE_API_KEY'))
print(os.environ.get('APP_KEY'))
print(os.environ.get('PROJECTS_TABLE_KEY'))
table = api.table(os.environ.get('APP_KEY'), os.environ.get('PROJECTS_TABLE_KEY'))



REFRESH_PROJECTS_TIMEOUT = timedelta(seconds=5)

def getProjectsFromAirtable():
    all_projects = table.all()
    class user_info:
        projects: list[str]
        hackatime_name: str
        total_hours: int
    info_dict = {}
    for entry in all_projects:
            email = entry["fields"]["email (from registered_users)"][0]
        
            if email not in info_dict.keys():
                info_dict[email] = user_info()
                info_dict[email].projects = []
            try:
                info_dict[email].projects.append(entry["fields"]['hackatime_name'][0])
            except KeyError:
                print(f"user {email} didn't have an associated hackatime project name. skipping!" )

    return info_dict 
    
# Listens to incoming messages that contain "hello"
@app.message("e")
def message_hello(message, say, client):
    channel_id = message["channel"]
    
    response = client.chat_postMessage(
        channel=channel_id,
        text="ok!"
    )
    message_ts = response['ts']
    airtable_info = getProjectsFromAirtable()
    last_refresh = datetime.now()
    while True:
        if datetime.now() - last_refresh > REFRESH_PROJECTS_TIMEOUT:
        # airtable_info = getProjectsFromAirtable()
            client.chat_update(
                channel=channel_id,
                ts=message_ts,
                text="updated"
        )
            last_refresh = datetime.now()
        


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
