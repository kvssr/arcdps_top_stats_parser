import requests
import json

# Test function to send a request with links to the json page
# You can run this file to send the request
def get_raid_json():
    # url = 'http://127.0.0.1:5000/json'
    url = 'http://192.168.2.10:4411/json'
    # url = 'http://192.168.2.11:5678/json'
    #url = 'https://arc-parser-api.herokuapp.com/json'

    data = {'links':[
        {'href': 'https://dps.report/getJson?id=Aq3l-20240108-213755'},
        {'href': 'https://dps.report/getJson?id=7ZGM-20240108-214552'},
    ]}
    headers = {'Content-Type':'application/json'}

    r = requests.post(url, data=json.dumps(data), headers=headers)
    print(r.status_code)
    if r.status_code == 202:
        print(r.json())
        print(r.headers)
    pass

get_raid_json()