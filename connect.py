from constants import *
from secrets import *
import requests
from requests.auth import HTTPBasicAuth
import json
import pprint
import os.path

class UbiConnection:
    '''
    UbiConnection provides functionality to connect Ubisoft servers and pull stats data
    '''
    
    def __init__(self):
        self.session = {}
        # Session information
        if os.path.exists('info.txt'):
            self.read_ticket()
            if not self.get_stats():
                self.login()
        else:
            self.login()

    '''
    Creates a ubisoft session and records the ticket
    '''
    def login(self):
        HEADERS = {
            'Ubi-AppId': UBI_APP_ID,
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0',
            'Ubi-LocaleCode': 'en-US',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        r = requests.post(LOGIN_URL, headers=HEADERS, auth=HTTPBasicAuth(SECRET_USERNAME, SECRET_PASSWORD))
        if r.status_code == 200:
            self.session = json.loads(r.text)
            f = open('info.txt', 'w')
            json.dump(r.json(), f)
            f.close()
            print('Created a new session successfully.')
        else:
            raise Exception('Error in login request:')
            pprint.pprint(r.text)

    '''
    Reads the info.txt file for current session information
    '''
    def read_ticket(self):
        f = open('info.txt', 'r')
        self.session = json.load(f)

    '''
    Creates HTTP requests and parses results as dictionary
    '''
    def get(self, url, params={}):
        headers = {
            'Ubi-AppId': UBI_APP_ID,
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0',
            'Ubi-LocaleCode': 'en-US',
            'Accept-Language': 'en-US,en;q=0.9',
            'Authorization': 'Ubi_v1 t=' + self.session['ticket'],
            'ubi-sessionid': self.session['sessionId']
            }
        for key, value in params.values():
            headers[key] = value
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            return None

    '''
    Returns ID of the given player name
    '''
    def get_player_by_name(self, name):
        REQ_URL = PLAYER_URL.format(key='nameOnPlatform', val=name)
        r_dict = self.get(REQ_URL)
        if r_dict:
            userid = r_dict['profiles'][0]['profileId']
            return userid
        else:
            raise Exception('Error while getting the player ID')
            return None

    def get_level(self):
        pass

    '''
    Returns casual and ranked game stats of the user
    '''
    def get_stats(self, id=None):
        if id is None:
            id = self.session['userId']
        REQ_URL = STATS_URL.format(id=id)
        r_dict = self.get(REQ_URL)
        if r_dict:
            return r_dict['results'][id]
        else:
            print('ERROR: Cannot get player stats {}'.format(id))
            return None

    '''
    Saves stats to a local database file
    '''
    def log_stats(self):
        pass

    '''
    Prints all fields in session
    '''
    def print_session(self):
        pprint.pprint(self.session)

if __name__ == '__main__':
    u = UbiConnection()
    st = u.get_stats()
    print(st)
    