from r6siegetracker.constants import *
import requests
from requests.auth import HTTPBasicAuth
import json
import pprint
import os.path

class UbiConnection:
    '''
    UbiConnection provides functionality to connect Ubisoft servers and pull stats data
    '''

    def __init__(self, master_password=None):

        self.connected = False

        if not os.path.exists('login.txt'):
            raise Exception('You need to have login.txt in the directory, use UbiConnection.encrypt_to_file function')
        else:
            try:
                try:
                    self.SECRET_USERNAME, self.SECRET_PASSWORD = UbiConnection.decrypt_from_file(master_password)
                except:
                    raise Exception('Wrong master password! Try again or recreate login.txt using UbiConnection.encrypt_to_file!')
            except:
                return
        self.session = {}
        # Session information
        if os.path.exists('info.txt'):
            self.read_ticket()
            if not self.get_stats():
                self.login()
        else:
            self.login()

    '''
    Stores mail address and password to encrpyted file
    Stores information as plain text if master_password is None or empty
    '''
    @classmethod
    def encrypt_to_file(cls, mail, password, master_password):
        if master_password is None or master_password == '':
            logintext = open('login.txt', 'w')
            logintext.write(mail + ' ' + password)
            logintext.close()
        else:
            import os
            import hashlib
            import base64
            from cryptography.fernet import Fernet
            key_base = hashlib.sha256(master_password.encode())
            key = base64.urlsafe_b64encode(key_base.digest())
            f = Fernet(key)
            enc_text = f.encrypt(('{} {}'.format(mail, password)).encode())
            logintext = open('login.txt', 'w') 
            logintext.write(enc_text.decode())
            logintext.close()

    '''
    Reads the encrypted login information from file
    '''
    @classmethod
    def decrypt_from_file(cls, master_password=''):
        import os.path
        if not os.path.exists('login.txt'):
            raise Exception('You need to have login.txt in the directory, use UbiConnection.encyrpt_to_file function')
        logintext = open('login.txt', 'r')
        raw_info = logintext.readline()
        logintext.close()
        if len(raw_info.split()) == 1: # Encrypted text
            import os
            import hashlib
            import base64
            from cryptography.fernet import Fernet
            key_base = hashlib.sha256(master_password.encode())
            key = base64.urlsafe_b64encode(key_base.digest())
            f = Fernet(key)
            decrypted_info = f.decrypt(raw_info.encode()).decode().split()
            return tuple(decrypted_info)
        else:
            return tuple(raw_info.split())

    '''
    Tries logging in with custom settings to see if the mail / password combination is valid.
    Does not store passwords or session info.
    '''
    @classmethod
    def validate(cls, username, password):
        HEADERS = {
            'Ubi-AppId': UBI_APP_ID,
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0',
            'Ubi-LocaleCode': 'en-US',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        payload = {'rememberMe': 'true'}
        r = requests.post(LOGIN_URL, headers=HEADERS, auth=HTTPBasicAuth(username, password), json=payload)
        if r.status_code == 200:
            return True
        else:
            return False

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
        payload = {'rememberMe': 'true'}
        r = requests.post(LOGIN_URL, headers=HEADERS, auth=HTTPBasicAuth(self.SECRET_USERNAME, self.SECRET_PASSWORD), json=payload)
        if r.status_code == 200:
            self.session = json.loads(r.text)
            f = open('info.txt', 'w')
            json.dump(r.json(), f)
            f.close()
            print('INFO: Created a new session successfully.')
            self.connected = True
            return True
        else:
            #raise Exception('ERROR: Login request failed:')
            print(r)
            print(type(r))
            pprint.pprint(r.text)
            self.connected = False
            return False
            

    '''
    Reads the info.txt file for current session information
    '''
    def read_ticket(self):
        f = open('info.txt', 'r')
        self.session = json.load(f)
        self.connected = True

    '''
    Creates HTTP requests and parses results as dictionary
    '''
    def get(self, url, params={}, force=True):
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
            print(r)
        else:
            # Try logging in and send request again
            if force:
                print('WARNING: Connection failed (possibly expired), renewing connection to server.')
                self.login()
                r = self.get(url, params, force=False)
                return r
            else:
                return None

    '''
    Returns ID of the given player name
    '''
    def get_player_by_name(self, name):
        REQ_URL = PLAYER_URL.format(key='nameOnPlatform', val=name)
        r_dict = self.get(REQ_URL)
        if r_dict:
            if len(r_dict['profiles']) == 0:
                print('ERROR: No such name exists in Uplay database: {}'.format(name))
                return None
            else:
                userid = r_dict['profiles'][0]['profileId']
                return userid
        else:
            raise Exception('ERROR: Cannot get Uplay ID')

    def get_level(self):
        pass

    '''
    Returns info for a player
    '''
    def get_player_by_id(self, id):
        REQ_URL = PROFILE_URL.format(id)
        r_dict = self.get(REQ_URL)
        if r_dict:
            if len(r_dict['profiles']) == 0:
                print('ERROR: Player could not found with ID {}'.format(id))
                return None
            else:
                userinfo = r_dict['profiles'][0]
                return userinfo
        else:
            raise Exception('ERROR: Cannot find ID')

    '''
    Returns stats of the requested user
    '''
    def get_stats(self, ids=None):
        if ids is None:
            ids = [self.session['userId']]
        REQ_URL = STATS_URL.format(ids=','.join(ids))
        r_dict = self.get(REQ_URL)
        if r_dict:
            return [r_dict['results'][id] for id in ids]
        else:
            print('ERROR: Cannot get player stats {}'.format(id))
            return None

    def get_operator_stats(self, ids=None):
        if ids is None:
            ids = [self.session['userId']]
        REQ_URL = OPERATOR_URL.format(ids=','.join(ids))
        r_dict = self.get(REQ_URL)
        if r_dict:
            op_list = [r_dict['results'][id] for id in ids]
            return op_list
        else:
            print('ERROR: Cannot get operator stats')
            return None

    '''
    Returns gun stats of the requested users
    '''
    def get_gun_stats(self, ids=None):
        if ids is None:
            ids = [self.session['userId']]
        REQ_URL = GUN_URL.format(ids=','.join(ids))
        r_dict = self.get(REQ_URL)
        if r_dict:
            return [r_dict['results'][id] for id in ids]
        else:
            print('ERROR: Cannot get player stats {}'.format(id))
            return None

    '''
    Returns the matchmatking stats of the requested user
    '''
    def get_rank(self, id=None, region='ncsa', season=-1): # Todo make ids, try with multiple seasons as well!
        if id is None:
            id = self.session['userId']
        REQ_URL = PROGRESS_URL.format(region=region, id=id, season=season)
        r_dict = self.get(REQ_URL)
        if r_dict:
            return r_dict['players'][id]
        else:
            print('ERROR: Cannot get player ranks {}.'.format(id))
            return None

    '''
    Returns the total number of games played for each user
    '''
    def get_total_games(self, ids):
        total_games = []
        REQ_URL = GAME_PLAYERD_URL.format(ids=','.join(ids))
        r_dict = self.get(REQ_URL)
        if r_dict:
            tgp_list = []
            for id in ids:
                try:
                    tgp_list.append(r_dict['results'][id]['generalpvp_matchplayed:infinite'])
                except KeyError:
                    tgp_list.append(0)
            return tgp_list
        else:
            print('ERROR: Cannot get total games played for requested users.')
            return None

    '''
    Prints all fields in session
    '''
    def print_session(self):
        pprint.pprint(self.session)
