import os
import requests
import json
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()
api = Api(os.environ.get('AIRTABLE_API_KEY'))
print(os.environ.get('APP_KEY'))
print(os.environ.get('PROJECTS_TABLE_KEY'))
table = api.table(os.environ.get('APP_KEY'), os.environ.get('PROJECTS_TABLE_KEY'))
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
            res = requests.post(url="https://hackatime.hackclub.com/api/admin/v1/user/get_user_by_email",
                     headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {os.environ.get('HACKATIME_API_KEY')}'
                     },
                     data=json.dumps({"email": email}))
            print(res.json()["user_id"])
            info_dict[email].hackatime_email = res.json()["user_id"]
        try:
            cur_project = entry["fields"]['hackatime_name']
            
        except KeyError:
            print(f"user {email} didn't have an associated hackatime project name. skipping!" )
            continue
        
       
        

