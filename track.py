import os
import sqlite3
from connect import UbiConnection
from constants import STAT_LIST, PROGRESS_LIST, RANKS, REGIONS
import datetime

class R6Tracker():

    '''
    R6Tracker objects is used to record stats into local database
    '''
    def __init__(self, ubiconnect):
        # Database information
        if not os.path.isfile('rainbow.db'):
            self.install()
        self.db = sqlite3.connect('rainbow.db', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        self.u = ubiconnect
        print('Initialized the tracker.')

    '''
    Creates database files for the first use
    '''
    def install(self):
        self.db = sqlite3.connect('rainbow.db', check_same_thread=False)
        self.cursor = self.db.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS 
                               players(id INTEGER PRIMARY KEY AUTOINCREMENT,
                                       name VARCHAR(100), 
                                       uplay_id VARCHAR(1000) UNIQUE,
                                       region VARCHAR(10));
                            ''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                               records(id INTEGER PRIMARY KEY AUTOINCREMENT, dt DATETIME);
                            ''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                               stats(id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER, record_id INTEGER,
                                     {} FLOAT,
                                     {} FLOAT,
                                     CONSTRAINT uq UNIQUE(player_id, record_id));
                            '''.format(' INTEGER, '.join(s[1] for s in STAT_LIST), ' FLOAT, '.join(p[1] for p in PROGRESS_LIST)))
        self.db.commit()
        self.db.close()
        print('Installed database rainbow.db!')

    '''
    Adds a new player to the database
    '''
    def add_player(self, name, region=None):
        u = self.u
        id = u.get_player_by_name(name)
        if id is None:
            print('ERROR: Failed to add {}'.format(name))
            return None
        if region is None:
            # Try all regions, choose the one with highest games
            max_games = 0
            region = 'ncsa'
            for r in REGIONS:
                r_dict = u.get_rank(id, r[1])
                region_games = r_dict['wins'] + r_dict['losses']
                if region_games > max_games:
                    region = r[1]
                    max_games = region_games
        self.cursor.execute('INSERT OR IGNORE INTO players (name, uplay_id, region) VALUES (?,?,?);',(name,id, region))
        self.db.commit()
        if self.cursor.rowcount == 1:
            print('Added player {} (ID={})'.format(name, id))
        else:
            print('WARNING: Could not add player {}, possible duplicate'.format(name))

    '''
    Removes a player from the database
    '''
    def remove_player(self, name):
        u = self.u
        id = u.get_player_by_name(name)
        self.cursor.execute('DELETE FROM players WHERE uplay_id = "{}"'.format(id))
        self.db.commit()
        if self.cursor.rowcount == 1:
            print('Removed player {} (ID={})'.format(name, id))
        else:
            print('WARNING: Could not remove player {}, does not exist!'.format(name))

    '''
    Creates an entry in records table immediately, it checks all players record only those who have played games since last record
    '''
    def save_state(self, verbose=False):
        u = self.u
        players = self.get_all_players()
        new_save = self.is_save_required(players)
        if not any(new_save):
            print('No changes...')
            return
        dt = str(datetime.datetime.now())
        # Create a new record point
        sqcmd = 'INSERT INTO records(dt) VALUES("{}")'.format(dt)
        self.cursor.execute(sqcmd)
        record_id = self.cursor.lastrowid
        for i, player in enumerate(players):
            if not new_save[i]:
                print('No changes for player {}'.format(player['name']))
                continue
            print('Getting current stats for {}'.format(player['name']))
            # Get stats
            stats = u.get_stats(player['uplay_id'])
            rank = u.get_rank(player['uplay_id'], region=player['region'])
            all_stats = []
            for s in STAT_LIST:
                all_stats.append(str(stats[s[0]]))
                if verbose:
                    print('{}: {}'.format(s[2], all_stats[-1]))
            for p in PROGRESS_LIST:
                all_stats.append(str(rank[p[0]]))
                if verbose:
                    print('{}: {}'.format(p[2], all_stats[-1]))
            merged_stats = ','.join(all_stats)
            # Insert to DB
            sqcmd = 'INSERT INTO stats VALUES(NULL,{},{},{});'.format(player['id'], record_id, merged_stats)
            self.cursor.execute(sqcmd)
        self.db.commit()

    '''
    Returns a list of booleans for players whose stats should be updated
    '''
    def is_save_required(self, player_list):
        lastgames = [0]*len(player_list)
        new_save = [False]*len(player_list)
        # Either has no records
        for i, player in enumerate(player_list):
            sqcmd = 'SELECT * FROM stats WHERE player_id = {} ORDER BY id DESC LIMIT 1;'.format(player[0])
            self.cursor.execute(sqcmd)
            lastgame = self.cursor.fetchall()
            if len(lastgame) == 0:
                print('No previous game record exists in DB for {}'.format(player['name']))
                new_save[i] = True
                lastgames[i] = 0
            else:
                lastgames[i] = lastgame[0]['match_played']
        # Or the total games played is greater than previous record
        u = self.u
        games = u.get_total_games([player['uplay_id'] for player in player_list])
        for i in range(len(games)):
            if games[i] - lastgames[i] > 0.5:
                print('{} new game(s) have found for {}'.format(games[i]-lastgames[i], player_list[i]['name']))
                new_save[i] = True
        # If all fails, it means there is no new update
        return new_save

    '''
    Returns the progress info for user
    '''
    def get_player_progress(self, name, start_dt, end_dt, ranked=True, casual=False, gun=False):
        if ranked:
            ranked_stats = [2,3,4,5,10,11]

            # Get all stats first
            sqcmd = 'SELECT dt, {}, {} FROM players, records, stats WHERE players.name="{}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt BETWEEN "{}" AND "{}";'.format(
                ', '.join([STAT_LIST[i][1] for i in ranked_stats]), 
                ', '.join([i[1] for i in PROGRESS_LIST]),
                name,
                start_dt,
                end_dt
                )
            self.cursor.execute(sqcmd)
            allrecords = self.cursor.fetchall()
            
            if allrecords is None or len(allrecords) == 0:
                print('WARNING: No records between requested date-times.')
            #elif len(allrecords) == 1:
            #    print('WARNING: Only 1 record has been found between date-times.')
            else: 
                
                # Ranked Progress: Ranked in-between stats
                
                # The structure:
                prog_table = [['Record', '# Games', 'K', 'D', 'K/D', 'W', 'L', 'W/L', 'MMR', 'Skill', 'Lower CI']]
                r0 = allrecords[0]
                for r1 in allrecords:
                    if r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] < 0.5:
                        # No ranked games between records
                        continue
                    prog_table.append([
                        #r0['dt'].split('.')[0] + ' to ' + r1['dt'].split('.')[0],
                        r0['dt'].split('.')[0],
                        r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'],
                        r1['ranked_kill'] - r0['ranked_kill'],
                        r1['ranked_death'] - r0['ranked_death'],
                        '{:.3f}'.format((r1['ranked_kill'] - r0['ranked_kill'])/max(1,r1['ranked_death'] - r0['ranked_death'])),
                        r1['ranked_won'] - r0['ranked_won'],
                        r1['ranked_lost'] - r0['ranked_lost'],
                        '{:.3f}'.format((r1['ranked_won'] - r0['ranked_won'])/max(1,r1['ranked_lost'] - r0['ranked_lost'])),
                        '{:.2f}'.format(r1['mmr'] - r0['mmr']),
                        '{:.2f}'.format(r1['skill_mean'] - r0['skill_mean']),
                        '{:.2f}'.format((r1['skill_mean'] - 1.96*r1['skill_std'])-(r0['skill_mean'] - 1.96*r0['skill_std']))
                        ])
                    r0 = r1
                prog_table.append([allrecords[-1]['dt'].split('.')[0]] + ['']*10)
                print('\nRanked In-Between Progress:')
                pretty_print(prog_table)


                # Ranked Cumulative Progress:

                # The structure:
                prog_table = [['Record', '# Games', 'K', 'D', 'K/D', 'KPG', 'Assists', 'APG', 'Headshots', 'HPG', 'W', 'L', 'W/L', 'Season W', 'Season L', 'Season W/L', 'MMR', 'Rank', 'Skill', 'Skill SD']]
                r0 = allrecords[0]
                for r1 in allrecords:
                    if r1 != r0  and (r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] < 0.5):
                        # No ranked games between records
                        continue
                    prog_table.append([
                        r1['dt'].split('.')[0],
                        r1['ranked_won'] + r1['ranked_lost'],
                        r1['ranked_kill'],
                        r1['ranked_death'],
                        '{:.4f}'.format((r1['ranked_kill'])/max(1,r1['ranked_death'])),
                        '{:.4f}'.format((r1['ranked_kill'])/max(1,r1['ranked_won'] + r1['ranked_lost'])),
                        r1['assists'],
                        '{:.4f}'.format(r1['assists']/max(1,r1['ranked_won'] + r1['ranked_lost'])),
                        r1['headshots'],
                        '{:.4f}'.format(r1['headshots']/max(1,r1['ranked_won'] + r1['ranked_lost'])),
                        r1['ranked_won'],
                        r1['ranked_lost'],
                        '{:.4f}'.format((r1['ranked_won'])/max(1,r1['ranked_lost'])),
                        '{:.0f}'.format(r1['season_wins']),
                        '{:.0f}'.format(r1['season_losses']),
                        '{:.4f}'.format((r1['season_wins'])/max(1,r1['season_losses'])),
                        '{:.2f}'.format(r1['mmr']),
                        RANKS[int(r1['rank'])],
                        '{:.2f}'.format(r1['skill_mean']),
                        '{:.2f}'.format(r1['skill_std'])
                        ])
                    r0 = r1
                p0 = prog_table[1]
                p1 = prog_table[-1]
                
                diff = [
                    '(Diff)',
                    p1[1] - p0[1], # Games
                    p1[2] - p0[2], # K
                    p1[3] - p0[3], # D
                    '{:.4f}'.format(float(p1[4]) - float(p0[4])), # K/D
                    '{:.4f}'.format(float(p1[5]) - float(p0[5])), # KPG
                    p1[6] - p0[6], # A
                    '{:.4f}'.format(float(p1[7]) - float(p0[7])), # APG
                    p1[8] - p0[8], # HS
                    '{:.4f}'.format(float(p1[9]) - float(p0[9])), # HPG
                    p1[10] - p0[10], # W
                    p1[11] - p0[11], # L
                    '{:.4f}'.format(float(p1[12]) - float(p0[12])), # W/L
                    '{:.0f}'.format(float(p1[13]) - float(p0[13])), # SW
                    '{:.0f}'.format(float(p1[14]) - float(p0[14])), # SL
                    '{:.4f}'.format(float(p1[15]) - float(p0[15])), # SWL
                    '{:.2f}'.format(float(p1[16]) - float(p0[16])), # MMR
                    round(allrecords[-1]['rank'] - allrecords[0]['rank']), # Rank
                    '{:.2f}'.format(float(p1[18]) - float(p0[18])), # Skill
                    '{:.2f}'.format(float(p1[19]) - float(p0[19])) # Skill SD
                    ]
                prog_table.append(diff)
                print('\nRanked Cumulative Progress:')
                pretty_print(prog_table)

        #if casual:
            
        #if gun:
        
        pass

    '''
    Returns a list of requested players, names should be a list
    '''
    def get_players(self, names):
        u = self.u
        self.cursor.execute('SELECT * FROM players WHERE name IN ({});'.format(','.join(['"' + str(name) + '"' for name in names])))
        return self.cursor.fetchall()

    '''
    Returns a list of all players in the database
    '''
    def get_all_players(self):
        u = self.u
        self.cursor.execute('SELECT * FROM players;')
        return self.cursor.fetchall()

    '''
    Prints all table contents to console
    '''
    def print_all_db(self):
        tables = ['players', 'records', 'stats']
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
        sqcmd = 'SELECT players.name, records.dt, stats.* FROM players, records, stats WHERE players.id = stats.player_id AND records.id = stats.record_id;'
        self.cursor.execute(sqcmd)
        rows = self.cursor.fetchall()
        csvdata = [','.join(d[0] for d in self.cursor.description)]
        for row in rows:
            csvdata.append(','.join([str(i) for i in list(row)]))
        csvfile = open('export.csv', 'w')
        for r in csvdata:
            csvfile.write(r + '\n')
            print(r)
        csvfile.close()

    '''
    Resets rainbow.db file
    '''
    def _reset(self):
        print('Resetting the database...')
        if self.db:
            self.db.close()
        if os.path.isfile('rainbow.db'):
            os.remove('rainbow.db')
        self.install()
        self.db = sqlite3.connect('rainbow.db', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

    '''
    Returns the requested info of a user
    '''
    def get_user_info(self, name, info):
        sqcmd = 'SELECT {} FROM stats, players WHERE stats.player_id = players.id AND players.name = "{}" ORDER BY stats.id DESC LIMIT 1;'.format(info, name)
        self.cursor.execute(sqcmd)
        rows = self.cursor.fetchall()
        if len(rows) == 0:
            return None
        else:
            return rows[0][info]

    def time_diff(self, start, end):
        mask = '%Y-%m-%d %H:%M:%S.%f'
        st = datetime.datetime.strptime(start, mask)
        en = datetime.datetime.strptime(end, mask)
        return en-st

def pretty_print(table):
    c_sizes = [max(len(str(table[i][c])) for i in range(len(table)))  for c in range(len(table[0]))]
    c_sizes = '}  {:>'.join(str(i) for i in c_sizes)
    mask = '{:>' + c_sizes + '}'
    for row in table:
        str_row = [str(v) for v in row]
        print(mask.format(*str_row))

if __name__ == '__main__':
    # Init
    r = R6Tracker(UbiConnection())
    #r._reset()
    #r.add_player('TurtleBud.ZB')
    #r.save_state()
    #r.print_all_db()
    #print(r.get_user_info('TurtleBud.ZB', 'mmr'))
    #r.export_to_csv()
