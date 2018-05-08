from constants import *
from secrets import *
import requests
from requests.auth import HTTPBasicAuth
import json
import pprint
import base64

class UbiConnection:
    
    def __init__(self):
        self.session = {}

    

    def login(self):
        
        r = requests.post(LOGIN_URL, headers=HEADERS,
                          auth=HTTPBasicAuth(SECRET_USERNAME, SECRET_PASSWORD))
        print(r.status_code)
        if r.status_code == 200:
            self.conn_info = json.loads(r.text)
            f = open('info.txt', 'w')
            json.dump(r.json(), f)
            f.close()
            HEADERS['Authorization'] = 'Ubi_v1 t=' + self.conn_info['ticket']
        else:
            print(r.text)

    def read_ticket(self):
        f = open('info.txt', 'r')
        self.conn_info = json.load(f)
        HEADERS['Authorization'] = 'Ubi_v1 t=' + self.conn_info['ticket']
        HEADERS['ubi-sessionid'] = self.conn_info['sessionId']

    def get(self, url, params={}, auth={}):
        headers = {
            'Ubi-AppId': ubi_app_id,
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0',
            'Ubi-LocaleCode': 'en-US',
            'Accept-Language': 'en-US,en;q=0.9'
            }
        for key, value in params.values():
            headers[key] = value
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            return None

    def get_player_by_name(self, name):
        REQ_URL = PLAYER_URL.format(key='nameOnPlatform', val=name)
        r = requests.get(REQ_URL, headers=HEADERS)
        if r.status_code == 200:
            r_dict = json.loads(r.text)
            userid = r_dict['profiles'][0]['profileId']
            return userid
        else:
            print(r.text)
            return None

    def get_level(self):
        pass

    def get_stats(self, id=None):
        if id is None:
            id = self.conn_info['userId']
        REQ_URL = STATS_URL.format(id=id)
        r = requests.get(REQ_URL, headers=HEADERS)
        if r.status_code == 200:
            r_dict = json.loads(r.text)
            return r_dict['results'][id]
        else:
            print(r.text)
        return

if __name__ == '__main__':
    u = UbiConnection()
    #u.login()
    u.read_ticket()
    st = u.get_stats()
    print(st)
    