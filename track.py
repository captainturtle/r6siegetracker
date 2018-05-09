import os
import sqlite3
from connect import UbiConnection
from constants import STAT_LIST
import datetime

class R6Tracker():

    '''
    R6Tracker objects is used to record stats into local database
    '''
    def __init__(self):
        # Database information
        if not os.path.isfile('rainbow.db'):
            self.install()
        self.db = sqlite3.connect('rainbow.db')
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

    '''
    Creates database files for the first use
    '''
    def install(self):
        self.db = sqlite3.connect('rainbow.db')
        self.cursor = self.db.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS players(id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100), userid VARCHAR(1000) UNIQUE);')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS dailystats(id INTEGER PRIMARY KEY AUTOINCREMENT, userid INTEGER, log_date DATE, ranked_kill INTEGER, ranked_death INTEGER, ranked_won INTEGER, ranked_lost INTEGER, casual_kill INTEGER, casual_death INTEGER, casual_won INTEGER, casual_lost INTEGER, CONSTRAINT unqentry UNIQUE(userid, log_date));')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS pingstats(id INTEGER PRIMARY KEY AUTOINCREMENT, userid INTEGER, log_datetime DATETIME, ranked_kill INTEGER, ranked_death INTEGER, ranked_won INTEGER, ranked_lost INTEGER, casual_kill INTEGER, casual_death INTEGER, casual_won INTEGER, casual_lost INTEGER);')
        self.db.commit()
        self.db.close()
        pass

    '''
    Adds a new player to the database
    '''
    def add_player(self, name):
        u = UbiConnection()
        id = u.get_player_by_name(name)
        self.cursor.execute('INSERT OR IGNORE INTO players (name, userid) VALUES (?,?);',(name,id))
        self.db.commit()

    '''
    Creates an entry in dailystats table, it is aimed to be used with a scheduler
    '''
    def log_daily(self):
        u, players = self.get_all_players()
        for player in players:
            print('Getting daily stats for {}'.format(player[1]))
            stats = u.get_stats(player[2])
            ordered_stats = []
            for s in STAT_LIST:
                ordered_stats.append(str(stats[s[0]]))
            dt = str(datetime.datetime.now().date())
            sqcmd = 'INSERT OR IGNORE INTO dailystats(userid, log_date, {}) VALUES({}, "{}", {});'.format(','.join([s[1] for s in STAT_LIST]), player[0], dt, ','.join(ordered_stats))
            self.cursor.execute(sqcmd)
            self.db.commit()

    '''
    Creates an entry in pingstats table immediately, it is aimed to be used after every game
    '''
    def log_instant(self):
        u, players = self.get_all_players()
        for player in players:
            print('Getting current stats for {}'.format(player[1]))
            stats = u.get_stats(player[2])
            ordered_stats = []
            for s in STAT_LIST:
                ordered_stats.append(str(stats[s[0]]))
            dt = str(datetime.datetime.now())
            sqcmd = 'INSERT INTO pingstats(userid, log_datetime, {}) VALUES({}, "{}", {});'.format(','.join([s[1] for s in STAT_LIST]), player[0], dt, ','.join(ordered_stats))
            self.cursor.execute(sqcmd)
            self.db.commit()

    '''
    Returns a list of requested players, names should be a list
    '''
    def get_players(self, names):
        u = UbiConnection()
        self.cursor.execute('SELECT * FROM players WHERE name IN ({});'.format(','.join(['"' + str(name) + '"' for name in names])))
        return u, self.cursor.fetchall()

    '''
    Returns a list of all players in the database
    '''
    def get_all_players(self):
        u = UbiConnection()
        self.cursor.execute('SELECT * FROM players;')
        return u, self.cursor.fetchall()

    '''
    Checks the performance since the last record without saving
    '''
    def quick_peek(self, names=None):
        if names is None:
            u, players = self.get_all_players()
        else:
            u, players = self.get_players(names)

        requested_stats = [i[1] for i in STAT_LIST]
        for player in players:
            stats = u.get_stats(player[2])
            print('Peeking stats for {}:'.format(player[1]))
            print('-----\nSince yesterday: ')
            sqcmd = 'SELECT * FROM dailystats WHERE userid = {} ORDER BY id DESC LIMIT 1;'.format(player[0])
            self.cursor.execute(sqcmd)
            dailystats = self.cursor.fetchone()
            prevs = 0
            for i, st in enumerate(STAT_LIST):
                curs = stats[st[0]] - dailystats[st[1]]
                if i % 2 == 0:
                    ratio = ''
                else:
                    ratio = '[{}/{} = {:.2f}]'.format(prevs,curs,prevs/max([curs, 1]))
                print('{}: {} {}'.format(st[2], curs, ratio))
                prevs = curs
            print('-----\nSince last record: ')
            sqcmd = 'SELECT * FROM pingstats WHERE userid = {} ORDER BY id DESC LIMIT 1;'.format(player[0])
            self.cursor.execute(sqcmd)
            pingstats = self.cursor.fetchone()
            for i, st in enumerate(STAT_LIST):
                curs = stats[st[0]] - pingstats[st[1]]
                if i % 2 == 0:
                    ratio = ''
                else:
                    ratio = '[{}/{} = {:.2f}]'.format(prevs,curs,prevs/max([curs, 1]))
                print('{}: {} {}'.format(st[2], curs, ratio))
                prevs = curs

    '''
    Prints stats of an individual player
    '''
    def print_player_stats(self, logtype='daily', limit=10, name=None, stat=None, today=False):
        u, players = self.get_players([name])
        player = players[0]
        print('Stats for {}\n-----'.format(player[1]))
        if logtype == 'daily':
            # Daily stats
            sqcmd = 'SELECT * FROM dailystats WHERE userid = {} ORDER BY id DESC LIMIT {};'.format(player[0], limit+1)
            self.cursor.execute(sqcmd)
            pstats = self.cursor.fetchall()
            
            if len(pstats) > 1:
                print('Daily stats:')
                last_row = []
                records = []
                for i, row in enumerate(pstats):
                    current_row = row
                    if last_row:
                        date = current_row['log_date'] + ' to ' + last_row['log_date']
                        rmp = last_row['ranked_won'] + last_row['ranked_lost'] - current_row['ranked_won'] - current_row['ranked_lost']
                        rwl = (last_row['ranked_won'] - current_row['ranked_won'])/max(last_row['ranked_lost'] - current_row['ranked_lost'],1)
                        rkd = (last_row['ranked_kill'] - current_row['ranked_kill'])/max(last_row['ranked_death'] - current_row['ranked_death'],1)
                        cmp = last_row['casual_won'] + last_row['casual_lost'] - current_row['casual_won'] - current_row['casual_lost']
                        cwl = (last_row['casual_won'] - current_row['casual_won'])/max(last_row['casual_lost'] - current_row['casual_lost'],1)
                        ckd = (last_row['casual_kill'] - current_row['casual_kill'])/max(last_row['casual_death'] - current_row['casual_death'],1)
                        records.append([date, rmp, rwl, rkd, cmp, cwl, ckd])
                    last_row = current_row
                # Print
                print('{:<24} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10}'.format('Date', 'Ranked MP', 'Ranked W/L', 'Ranked K/D', 'Casual MP', 'Casual W/L', 'Casual K/D'))
                for record in records:
                    print('{:24} {:10} {:10.2f} {:10.2f} {:10} {:10.2f} {:10.2f}'.format(*record))
            else:
                print('Not enough data to print daily stats')

        elif logtype == 'checkpoint':
            # Ping stats
            sqcmd = 'SELECT * FROM pingstats WHERE userid = {} ORDER BY id DESC LIMIT {};'.format(player[0], limit+1)
            self.cursor.execute(sqcmd)
            pstats = self.cursor.fetchall()
            if len(pstats) > 1:
                print('Checkpoint stats:')
                last_row = []
                records = []
                for i, row in enumerate(pstats):
                    current_row = row
                    if last_row:
                        rmp = last_row['ranked_won'] + last_row['ranked_lost'] - current_row['ranked_won'] - current_row['ranked_lost']
                        rwl = (last_row['ranked_won'] - current_row['ranked_won'])/max(last_row['ranked_lost'] - current_row['ranked_lost'],1)
                        rkd = (last_row['ranked_kill'] - current_row['ranked_kill'])/max(last_row['ranked_death'] - current_row['ranked_death'],1)
                        cmp = last_row['casual_won'] + last_row['casual_lost'] - current_row['casual_won'] - current_row['casual_lost']
                        cwl = (last_row['casual_won'] - current_row['casual_won'])/max(last_row['casual_lost'] - current_row['casual_lost'],1)
                        ckd = (last_row['casual_kill'] - current_row['casual_kill'])/max(last_row['casual_death'] - current_row['casual_death'],1)
                        records.append([rmp, rwl, rkd, cmp, cwl, ckd])
                    last_row = current_row
                # Print
                print('{:>10} {:>10} {:>10} {:>10} {:>10} {:>10}'.format('Ranked MP', 'Ranked W/L', 'Ranked K/D', 'Casual MP', 'Casual W/L', 'Casual K/D'))
                for record in records:
                    print('{:10} {:10.2f} {:10.2f} {:10} {:10.2f} {:10.2f}'.format(*record))
            else:
                print('Not enough data to print ping stats')
        elif logtype == 'cumulative':
            sqcmd = 'SELECT * FROM dailystats WHERE userid = {} ORDER BY id DESC LIMIT {};'.format(player[0], limit+1)
            self.cursor.execute(sqcmd)
            pstats = self.cursor.fetchall()
            
            if len(pstats) > 1:
                print('Cumulative stats:')
                records = []
                for i, row in enumerate(pstats):
                    date = row['log_date']
                    rmp = row['ranked_won'] + row['ranked_lost']
                    rwl = row['ranked_won'] / max(row['ranked_lost'], 1)
                    rkd = row['ranked_kill'] / max(row['ranked_death'], 1)
                    cmp = row['casual_won'] + row['casual_lost']
                    cwl = row['casual_won'] / max(row['casual_lost'], 1)
                    ckd = row['casual_kill'] / max(row['casual_death'], 1)
                    records.append([date, rmp, rwl, rkd, cmp, cwl, ckd])
                # Print
                print('{:<10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10}'.format('Date', 'Ranked MP', 'Ranked W/L', 'Ranked K/D', 'Casual MP', 'Casual W/L', 'Casual K/D'))
                for record in records:
                    print('{:10} {:10} {:10.4f} {:10.4f} {:10} {:10.4f} {:10.4f}'.format(*record))
            else:
                print('Not enough data to print daily stats')
        

    '''
    Prints all table contents to console
    '''
    def print_all_db(self):
        tables = ['players', 'dailystats', 'pingstats']
        for t in tables:
            print(t)
            self.cursor.execute('SELECT * FROM {};'.format(t))
            rows = self.cursor.fetchall()
            for row in rows:
                print(list(row))

    '''
    Prints all logs to csv files (daily.csv and pings.csv)
    '''
    def export_to_csv(self):
        print('CSV data:')
        sqcmd = '''SELECT log_date as dt, 'daily' as type, name, ranked_won, ranked_lost,
                          ranked_kill, ranked_death, casual_won, casual_lost,
                          casual_kill, casual_death FROM players, dailystats 
                   WHERE dailystats.userid = players.id
                   UNION
                   SELECT log_datetime as dt, 'cp' as type, name, ranked_won, ranked_lost,
                          ranked_kill, ranked_death, casual_won, casual_lost,
                          casual_kill, casual_death FROM players, pingstats 
                   WHERE pingstats.userid = players.id
                   ORDER BY type DESC, dt, name;'''
        self.cursor.execute(sqcmd)
        rows = self.cursor.fetchall()
        for row in rows:
            print(','.join([str(i) for i in list(row)]))
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
    # Init
    r = R6Tracker()
    # Print functions
    r.quick_peek()
    r.print_player_stats(name='TurtleBud.ZB', logtype='daily')
    r.print_player_stats(name='TurtleBud.ZB', logtype='cumulative')
    r.print_player_stats(name='TurtleBud.ZB', logtype='checkpoint')
    r.export_to_csv()
    # Tracking functions
    # r.log_instant()
    # r.log_daily()
    r.print_all_db()
