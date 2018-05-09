import os
import sqlite3
from connect import UbiConnection
from constants import STAT_LIST
import datetime

class R6Tracker():

    def __init__(self):
        # Database information
        if not os.path.isfile('rainbow.db'):
            self.install()
        self.db = sqlite3.connect('rainbow.db')
        self.cursor = self.db.cursor()

    def install(self):
        self.db = sqlite3.connect('rainbow.db')
        self.cursor = self.db.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS players(id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100), userid VARCHAR(1000) UNIQUE);')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS dailystats(id INTEGER PRIMARY KEY AUTOINCREMENT, userid INTEGER, log_date DATE, ranked_kill INTEGER, ranked_death INTEGER, ranked_won INTEGER, ranked_lost INTEGER, casual_kill INTEGER, casual_death INTEGER, casual_won INTEGER, casual_lost INTEGER, CONSTRAINT unqentry UNIQUE(userid, log_date));')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS pingstats(id INTEGER PRIMARY KEY AUTOINCREMENT, userid INTEGER, log_datetime DATETIME, ranked_kill INTEGER, ranked_death INTEGER, ranked_won INTEGER, ranked_lost INTEGER, casual_kill INTEGER, casual_death INTEGER, casual_won INTEGER, casual_lost INTEGER);')
        self.db.commit()
        self.db.close()
        pass

    def add_player(self, name):
        u = UbiConnection()
        id = u.get_player_by_name(name)
        self.cursor.execute('INSERT OR IGNORE INTO players (name, userid) VALUES (?,?)',(name,id))
        self.db.commit()

    def log_daily(self):
        players = self.get_all_players()
        for player in players:
            print('Getting stats for {}'.format(player[1]))
            stats = u.get_stats(player[2])
            ordered_stats = []
            for s in STAT_LIST:
                ordered_stats.append(stats[s[0]])
            print(ordered_stats)

    def log_instant(self):
        u, players = self.get_all_players()
        u.print_session()
        for player in players:
            print('Getting stats for {}'.format(player[1]))
            stats = u.get_stats(player[2])
            ordered_stats = []
            for s in STAT_LIST:
                ordered_stats.append(str(stats[s[0]]))
            dt = str(datetime.datetime.now())
            sqcmd = 'INSERT INTO pingstats(userid, log_datetime, {}) VALUES({}, "{}", {})'.format(','.join([s[1] for s in STAT_LIST]), player[0], dt, ','.join(ordered_stats))
            print(sqcmd)
            self.cursor.execute(sqcmd)
            self.db.commit()

    def get_all_players(self):
        u = UbiConnection()
        self.cursor.execute('SELECT * FROM players')
        return u, self.cursor.fetchall()

    def quick_peek(self):
        pass

    def print_user_stats(self, id=None, name=None, stat=None):
        pass

    def print_all_db(self):
        tables = ['players', 'dailystats', 'pingstats']
        for t in tables:
            print(t)
            self.cursor.execute('SELECT * FROM {}'.format(t))
            rows = self.cursor.fetchall()
            for row in rows:
                print(row)

    def export_to_csv(self):
        pass

    '''
    Deletes rainbow.db file
    '''
    def _delete(self):
        if self.db:
            self.db.close()
        if os.path.isfile('rainbow.db'):
            os.remove('rainbow.db')

if __name__ == '__main__':
    r = R6Tracker()
    r.log_instant()
    r.print_all_db()
    #r._delete()
