import os
import requests
import json
import ast
import re
from datetime import datetime, timedelta
from pyairtable import Api
from dotenv import load_dotenv



def refreshData():



    load_dotenv()
    api = Api(os.environ.get("AIRTABLE_API_KEY"))
    print(os.environ.get("APP_KEY"))
    print(os.environ.get("PROJECTS_TABLE_KEY"))
    table = api.table(os.environ.get("APP_KEY"), os.environ.get("PROJECTS_TABLE_KEY"))
    all_projects = table.all(formula="{worked_on_in_last_day}=TRUE()")
    count = 0

    class user_info:
        projects: list[str]
        hackatime_id: str
        total_hours: int
        hackatime_info: object
        name: str
        slack_id: str
        


    info_dict = {}
    unmatched_projects = []
    start_date = (datetime.today()).strftime("%Y-%m-%d")


    def parse_project_candidates(raw_value):
        if isinstance(raw_value, list):
            return [str(v).strip().lower() for v in raw_value if str(v).strip()]

        if isinstance(raw_value, str):
            value = raw_value.strip()
            if not value:
                return []

            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, list):
                        return [str(v).strip().lower() for v in parsed if str(v).strip()]
                except (SyntaxError, ValueError):
                    pass

            return [value.lower()]

        return []


    def normalize_name(value):
        return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())

    def getUserIDByEmail(email):
        res = requests.post(
                url="https://hackatime.hackclub.com/api/admin/v1/user/get_user_by_email",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('HACKATIME_API_KEY')}",
                },
                data=json.dumps({"email": email}),
            )
        if "user_id" not in res.json().keys():
            return ""
        return res.json()["user_id"]

    def getUserInfo(user_id): #can be id or slack id!
        res = requests.get(
                url=f"https://hackatime.hackclub.com/api/v1/users/{user_id}/stats?features=projects&start_date={start_date}",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('HACKATIME_API_KEY')}",
                },
            )
        if res.status_code == 404:
            return ""
        else:
            return res
        
        
        
    def getHackatimeInfo(email, slack_id):
        #first try by slackid
        res = getUserInfo(slack_id)
        if res == "":
            user_id = getUserIDByEmail(email)
            if user_id == "":
                return ""
            else:
                res = getUserInfo(user_id)
        return res.json() #type: ignore            

    for entry in all_projects:
        print(entry)
        count += 1
        start_time = datetime.now()
        email = entry["fields"]["email (from registered_users)"][0]
        slack_id = entry["fields"]["slack_id (from registered_users)"][0]
        
        if email not in info_dict.keys():
            info_dict[email] = user_info()
            info_dict[email].projects = []
            info_dict[email].total_hours = 0
            info_dict[email].name = entry["fields"]["slack_display_name (from registered_users)"][0]
            info_dict[email].slack_id = slack_id
            res = getHackatimeInfo(email, slack_id)
            if res == "":
                print("couldn't get hackatime info")
                continue
            info_dict[email].hackatime_info = res
            
            
            
        raw_project = entry["fields"].get("hackatime_name", "")
        project_candidates = parse_project_candidates(raw_project)
        print(project_candidates)
        if not project_candidates:
            print("couldn't get hackatime name")
            continue

        matched = False
        projects = info_dict[email].hackatime_info["data"]["projects"]
        normalized_candidates = {normalize_name(name) for name in project_candidates}
        for proj in projects:
            proj_name = proj.get("name", "").strip().lower()
            normalized_proj_name = normalize_name(proj_name)

            if (
                proj_name in project_candidates
                or normalized_proj_name in normalized_candidates
            ):
                print("found project!")
                new_hours = (proj.get("hours", 0) * 60) + proj.get("minutes", 0)
                info_dict[email].total_hours += new_hours
                info_dict[email].projects.append(proj.get("name", ""))
                matched = True
                break

        if not matched:
            print("couldn't find project")
            unmatched_projects.append(
                {
                    "email": email,
                    "candidates": project_candidates,
                    "available_count": len(projects),
                    "available_names": [p.get("name", "") for p in projects[:5]],
                }
            )


    sorted_info_dict = dict(
        sorted(
            info_dict.items(),
            key=lambda item: getattr(item[1], "total_hours", 0),
            reverse=True,
        )[:8]
    )
    for email, user in sorted_info_dict.items():
        print(email, user.total_hours / 60, user.projects)

    if unmatched_projects:
        print("unmatched project rows:", len(unmatched_projects))
        for row in unmatched_projects[:10]:
            print(row)

    """
    ima put it to you like this i dont play about you 
    the stuff i be saying im something like shakespeare u hear me
    i know ur feeling me like im feeling u cuz its written all over ur face
    like our love is written like the stars
    but lemme stop because y ou know when its about  u i got endless bars
    """
    print(datetime.now() - start_time)
    
    return sorted_info_dict
    

if __name__ == "__main__":
    refreshData() #debugging