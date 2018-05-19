import os
import sqlite3
from connect import UbiConnection
from constants import STAT_LIST, PROGRESS_LIST, RANKS, REGIONS, SEASONS
import datetime

class R6Tracker():

    '''
    R6Tracker objects is used to record stats into local database
    '''
    def __init__(self, ubiconnect):
        # Database information
        if not os.path.isfile('rainbow.db'):
            self.install()
        else:
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
        self.db.row_factory = sqlite3.Row
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
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                               seasons(player_id INTEGER, season INTEGER,
                                     {} FLOAT,
                                     PRIMARY KEY (player_id, season));
                            '''.format(' FLOAT, '.join(p[1] for p in PROGRESS_LIST)))
        # Operator table
        self.db.commit()
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
    Creates an entry in records table, it checks all players record only those who have played games since the last record
    '''
    def save_state(self, verbose=False):
        u = self.u
        players = self.get_all_players()
        new_save = self.is_save_required(players)
        if not any(new_save):
            print('Checked the stats, no updates have been found.')
            return
        print('Getting new records...')
        dt = str(datetime.datetime.now())
        # Create a new record point
        sqcmd = 'INSERT INTO records(dt) VALUES("{}")'.format(dt)
        self.cursor.execute(sqcmd)
        record_id = self.cursor.lastrowid
        for i, player in enumerate(players):
            if not new_save[i]:
                continue
            print('Getting current stats for {}'.format(player['name']))
            # Get stats
            stats = u.get_stats(player['uplay_id'])
            rank = u.get_rank(player['uplay_id'], region=player['region'])
            all_stats = []
            for s in STAT_LIST:
                try:
                    all_stats.append(str(stats[s[0]]))
                except: # When a specific stat is not available (e.g. never played ranked...)
                    all_stats.append('0')
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
                print('{} new game(s) have been found for {}'.format(games[i]-lastgames[i], player_list[i]['name']))
                new_save[i] = True
        # If all fails, it means there is no new update
        return new_save

    '''
    Returns the progress info for user

    Parameters
    ----------
    name : string
        Name of the requested player
    start_dt : datetime
        Date and time of the range beginning
    end_dt : datetime
        Date and time of the range ending
    increment : integer, optional
        Increment of days for the requested range
    ranked : boolean, optional
        Option for requesting ranked stats
    casual : boolean, optional
        Option for requesting casual stats
    gun : boolean, optional
        Option for requesting gun stats
    operator: boolean, optional
        Option for requesting operator stats
    '''
    def get_player_progress(self, name, start_dt, end_dt, increment=0, ranked=True, casual=False, gun=False, operator=False):
        if ranked:
            ranked_stats = [2,3,4,5,10,11]
            
            if increment==0:
                # Get all stats first
                sqcmd = '''
                SELECT *
                FROM(
                SELECT dt, casual_won, casual_lost, {ranked}, {ranks} 
                FROM players, records, stats 
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt <= "{st}" ORDER BY stats.id DESC LIMIT 1
                )
                UNION
                SELECT *
                FROM(
                SELECT dt, casual_won, casual_lost, {ranked}, {ranks} 
                FROM players, records, stats 
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt BETWEEN "{st}" AND "{et}"
                );
                '''.format(ranked=', '.join([STAT_LIST[i][1] for i in ranked_stats]), ranks=', '.join([i[1] for i in PROGRESS_LIST]), name=name, st=start_dt, et=end_dt)
            else:
                sqcmd = '''
                SELECT NULL as d_from, NULL as d_to, *
                FROM(
                SELECT dt, casual_won, casual_lost, {ranked}, {ranks} 
                FROM players, records, stats 
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt <= "{st}" ORDER BY stats.id DESC LIMIT 1
                )
                '''
                
                daydiff = self.time_diff(start_dt, end_dt) #datetime.datetime.strptime(start_dt, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(end_dt, '%Y-%m-%d %H:%M:%S')
                for inc in range(0, daydiff.days+1, increment):
                    dailyunion = '''
                    UNION
                    SELECT date("{{st}}", '+{inc} days') as d_from, date("{{st}}", '+{inc1} days') as d_to, *  FROM(
                        SELECT dt, casual_won, casual_lost, {{ranked}}, {{ranks}}
                        FROM players, records, stats 
                        WHERE players.name="{{name}}" AND players.id=stats.player_id AND records.id=stats.record_id AND dt BETWEEN datetime("{{st}}", '+{inc} days') AND datetime("{{st}}", '+{inc1} days') ORDER BY records.dt DESC LIMIT 1
                    )
                    '''.format(inc = inc, inc1 = inc+increment)
                    sqcmd += dailyunion
                # Calculate day diff

                sqcmd = sqcmd.format(ranked=', '.join([STAT_LIST[i][1] for i in ranked_stats]), ranks=', '.join([i[1] for i in PROGRESS_LIST]), name=name, st=start_dt, et=end_dt)
                # For loop for increment
                
                
            self.cursor.execute(sqcmd)
            allrecords = self.cursor.fetchall()
            
            if allrecords is None or len(allrecords) == 0:
                print('WARNING: No ranked game records between requested date-times.')
            elif len(allrecords) == 1:
                print('WARNING: Only 1 record has been found between date-times.')
            else: 
                
                # Ranked Progress: Ranked in-between stats
                
                # The structure:
                prog_table = [['Record', '# Games', 'K', 'A', 'D', 'K/D', 'HS', 'H/K', 'W', 'L', 'W/L', 'MMR', 'Skill', 'Skill-StDev']]
                r0 = allrecords[0]
                inaccuracy = False
                for r1 in allrecords:
                    if r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] < 0.5:
                        # No ranked games between records
                        r0 = r1
                        continue
                    inaccuracy = False
                    if (r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'] > 0.5):
                        inaccuracy = True
                    try:
                        recname = r1['d_from'] + ' to ' + r1['d_to']
                    except:
                        recname = r0['dt'].split('.')[0]
                    prog_table.append([
                        #r0['dt'].split('.')[0] + ' to ' + r1['dt'].split('.')[0],
                        recname,
                        r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'],
                        r1['ranked_kill'] - r0['ranked_kill'],
                        '*' if inaccuracy else r1['assists'] - r0['assists'],
                        r1['ranked_death'] - r0['ranked_death'],
                        '{:.3f}'.format((r1['ranked_kill'] - r0['ranked_kill'])/max(1,r1['ranked_death'] - r0['ranked_death'])),
                        '*' if inaccuracy else r1['headshots'] - r0['headshots'],
                        '*' if inaccuracy else '{:4.2%}'.format((r1['headshots'] - r0['headshots'])/max(1,r1['ranked_kill']-r0['ranked_kill'])),
                        r1['ranked_won'] - r0['ranked_won'],
                        r1['ranked_lost'] - r0['ranked_lost'],
                        '{:.3f}'.format((r1['ranked_won'] - r0['ranked_won'])/max(1,r1['ranked_lost'] - r0['ranked_lost'])),
                        '{:.2f}'.format(r1['mmr'] - r0['mmr']),
                        '{:.2f}'.format(r1['skill_mean'] - r0['skill_mean']),
                        '{:.2f}'.format(r1['skill_std'] - r0['skill_std'])
                        ])
                    r0 = r1
                prog_table.append([allrecords[-1]['dt'].split('.')[0]] + ['']*13)
                prog_table.append(['---']*len(prog_table[0]))
                p0 = allrecords[0]
                p1 = allrecords[-1]
                total = [
                    '(Total)',
                    p1['ranked_won'] + p1['ranked_lost'] - p0['ranked_won'] - p0['ranked_lost'], # Games
                    p1['ranked_kill'] - p0['ranked_kill'], # K
                    '*' if inaccuracy else p1['assists'] - p0['assists'], # A
                    p1['ranked_death'] - p0['ranked_death'], # D
                    '{:.3f}'.format((p1['ranked_kill'] - p0['ranked_kill']) / max(1, p1['ranked_death'] - p0['ranked_death'])), # K/D
                    '*' if inaccuracy else p1['headshots'] - p0['headshots'], # HS
                    '*' if inaccuracy else '{:4.2%}'.format((p1['headshots'] - p0['headshots'])/max(1,p1['ranked_kill']-p0['ranked_kill'])), # H/K
                    p1['ranked_won'] - p0['ranked_won'], # W
                    p1['ranked_lost'] - p0['ranked_lost'], # L
                    '{:.3f}'.format((p1['ranked_won'] - p0['ranked_won'])/max(1,p1['ranked_lost'] - p0['ranked_lost'])), # W/L
                    '{:.2f}'.format(p1['mmr'] - p0['mmr']), # MMR
                    '{:.2f}'.format(p1['skill_mean'] - p0['skill_mean']), # Skill
                    '{:.2f}'.format(p1['skill_std'] - p0['skill_std'])
                    ]
                prog_table.append(total)
                
                print('\nRanked In-Between Progress:')
                pretty_print(prog_table)


                # Ranked Cumulative Progress:

                # The structure:
                prog_table = [['Record', '# Games', 'K', 'D', 'K/D', 'KPG', 'Assists', 'APG', 'Headshots', 'HPG', 'W', 'L', 'W/L', 'Season W', 'Season L', 'Season W/L', 'MMR', 'Rank', 'Skill', 'Skill SD']]
                r0 = allrecords[0]
                for r1 in allrecords:
                    if r1 != r0  and (r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] < 0.5):
                        # No ranked games between records
                        r0 = r1
                        continue
                    inaccuracy = False
                    if (r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'] > 0.5):
                        inaccuracy = True
                    try:
                        recname = r1['d_from']
                    except:
                        recname = r1['dt'].split('.')[0]
                    prog_table.append([
                        #r1['dt'].split('.')[0],
                        recname,
                        r1['ranked_won'] + r1['ranked_lost'],
                        r1['ranked_kill'],
                        r1['ranked_death'],
                        '{:.4f}'.format((r1['ranked_kill'])/max(1,r1['ranked_death'])),
                        '{:.4f}'.format((r1['ranked_kill'])/max(1,r1['ranked_won'] + r1['ranked_lost'])),
                        '*' if inaccuracy else r1['assists'],
                        '*' if inaccuracy else '{:.4f}'.format(r1['assists']/max(1,r1['ranked_won'] + r1['ranked_lost'])),
                        '*' if inaccuracy else r1['headshots'],
                        '*' if inaccuracy else '{:.4f}'.format(r1['headshots']/max(1,r1['ranked_won'] + r1['ranked_lost'])),
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
                
                prog_table.append(['---']*len(prog_table[0]))
                
                diff = [
                    '(Diff)',
                    p1[1] - p0[1], # Games
                    p1[2] - p0[2], # K
                    p1[3] - p0[3], # D
                    '{:+.4f}'.format(float(p1[4]) - float(p0[4])), # K/D
                    '{:+.4f}'.format(float(p1[5]) - float(p0[5])), # KPG
                    '*' if isinstance(p1[6], str) or isinstance(p0[6], str) else p1[6] - p0[6], # A
                    '*' if '*' in p1[7] else '{:+.4f}'.format(float(p1[7]) - float(p0[7])), # APG
                    '*' if isinstance(p1[8], str) or isinstance(p0[8], str)  else p1[8] - p0[8], # HS
                    '*' if '*' in p1[9] else '{:+.4f}'.format(float(p1[9]) - float(p0[9])), # HPG
                    p1[10] - p0[10], # W
                    p1[11] - p0[11], # L
                    '{:+.4f}'.format(float(p1[12]) - float(p0[12])), # W/L
                    '{:.0f}'.format(float(p1[13]) - float(p0[13])), # SW
                    '{:.0f}'.format(float(p1[14]) - float(p0[14])), # SL
                    '{:+.4f}'.format(float(p1[15]) - float(p0[15])), # SWL
                    '{:+.2f}'.format(float(p1[16]) - float(p0[16])), # MMR
                    round(allrecords[-1]['rank'] - allrecords[0]['rank']), # Rank
                    '{:+.2f}'.format(float(p1[18]) - float(p0[18])), # Skill
                    '{:+.2f}'.format(float(p1[19]) - float(p0[19])) # Skill SD
                    ]
                prog_table.append(diff)
                print('\nRanked Cumulative Progress:')
                pretty_print(prog_table)

        if casual:
            
            casual_stats = [6,7,8,9,10,11]

            # Get all stats first
            sqcmd = '''
                SELECT *
                FROM(
                SELECT dt, ranked_won, ranked_lost, {casual}
                FROM players, records, stats
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt <= "{st}" ORDER BY stats.id DESC LIMIT 1
                )
                UNION
                SELECT *
                FROM(
                SELECT dt, ranked_won, ranked_lost, {casual}
                FROM players, records, stats
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt BETWEEN "{st}" AND "{et}"
                );
                '''.format(
                casual=', '.join([STAT_LIST[i][1] for i in casual_stats]),
                name=name,
                st=start_dt,
                et=end_dt
                )
            self.cursor.execute(sqcmd)
            allrecords = self.cursor.fetchall()
            
            if allrecords is None or len(allrecords) == 0:
                print('WARNING: No casual game records between requested date-times.')
            else: 
                
                # Casual Progress: In-between stats
                
                # The structure:
                prog_table = [['Record', '# Games', 'K', 'A', 'D', 'K/D', 'HS', 'W', 'L', 'W/L']]
                r0 = allrecords[0]
                for r1 in allrecords:
                    if r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'] < 0.5:
                        # No ranked games between records
                        r0 = r1
                        continue
                    inaccuracy = False
                    if (r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] > 0.5):
                        inaccuracy = True
                    prog_table.append([
                        #r0['dt'].split('.')[0] + ' to ' + r1['dt'].split('.')[0],
                        r0['dt'].split('.')[0],
                        r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'],
                        r1['casual_kill'] - r0['casual_kill'],
                        '*' if inaccuracy else r1['assists'] - r0['assists'],
                        r1['casual_death'] - r0['casual_death'],
                        '{:.3f}'.format((r1['casual_kill'] - r0['casual_kill'])/max(1,r1['casual_death'] - r0['casual_death'])),
                        '*' if inaccuracy else r1['headshots'] - r0['headshots'],
                        r1['casual_won'] - r0['casual_won'],
                        r1['casual_lost'] - r0['casual_lost'],
                        '{:.3f}'.format((r1['casual_won'] - r0['casual_won'])/max(1,r1['casual_lost'] - r0['casual_lost'])),
                        ])
                    r0 = r1
                prog_table.append([allrecords[-1]['dt'].split('.')[0]] + ['']*9)
                print('\nCasual In-Between Progress:')
                pretty_print(prog_table)


                # Casual Cumulative Progress:

                # The structure:
                prog_table = [['Record', '# Games', 'K', 'D', 'K/D', 'KPG', 'Assists', 'APG', 'Headshots', 'HPG', 'W', 'L', 'W/L']]
                r0 = allrecords[0]
                for r1 in allrecords:
                    if r1 != r0  and (r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'] < 0.5):
                        # No ranked games between records
                        r0 = r1
                        continue
                    inaccuracy = False
                    if (r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] > 0.5):
                        inaccuracy = True
                    prog_table.append([
                        r1['dt'].split('.')[0],
                        r1['casual_won'] + r1['casual_lost'],
                        r1['casual_kill'],
                        r1['casual_death'],
                        '{:.4f}'.format((r1['casual_kill'])/max(1,r1['casual_death'])),
                        '{:.4f}'.format((r1['casual_kill'])/max(1,r1['casual_won'] + r1['casual_lost'])),
                        '*' if inaccuracy else r1['assists'],
                        '*' if inaccuracy else '{:.4f}'.format(r1['assists']/max(1,r1['casual_won'] + r1['casual_lost'])),
                        '*' if inaccuracy else r1['headshots'],
                        '*' if inaccuracy else '{:.4f}'.format(r1['headshots']/max(1,r1['casual_won'] + r1['casual_lost'])),
                        r1['casual_won'],
                        r1['casual_lost'],
                        '{:.4f}'.format((r1['casual_won'])/max(1,r1['casual_lost']))
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
                    '*' if isinstance(p1[6], str) or isinstance(p0[6], str) else p1[6] - p0[6], # A
                    '*' if '*' in p1[7] else '{:.4f}'.format(float(p1[7]) - float(p0[7])), # APG
                    '*' if isinstance(p1[8], str) or isinstance(p0[8], str) else p1[8] - p0[8], # HS
                    '*' if '*' in p1[9] else '{:.4f}'.format(float(p1[9]) - float(p0[9])), # HPG
                    p1[10] - p0[10], # W
                    p1[11] - p0[11], # L
                    '{:.4f}'.format(float(p1[12]) - float(p0[12])) # W/L
                    ]
                prog_table.append(diff)
                print('\nCasual Cumulative Progress:')
                pretty_print(prog_table)
            
            
        if gun:
            
            gun_stats = list(range(12,39))
            
            # Get all stats first
            sqcmd = '''
                SELECT *
                FROM(
                SELECT dt, ranked_won, ranked_lost, casual_won, casual_lost, headshots, ranked_kill, casual_kill, {gun} 
                FROM players, records, stats 
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt <= "{st}" ORDER BY stats.id DESC LIMIT 1
                )
                UNION
                SELECT *
                FROM(
                SELECT dt, ranked_won, ranked_lost, casual_won, casual_lost, headshots, ranked_kill, casual_kill, {gun} 
                FROM players, records, stats 
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt BETWEEN "{st}" AND "{et}"
                );
                '''.format(
                gun=', '.join([STAT_LIST[i][1] for i in gun_stats]),
                name=name,
                st=start_dt,
                et=end_dt
                )
            self.cursor.execute(sqcmd)
            allrecords = self.cursor.fetchall()
            
            if allrecords is None or len(allrecords) == 0:
                print('WARNING: No records between requested date-times.')
            else: 
                
                # Gun Progress: In-between stats
                print('WARNING: Ubi does not update bullets fired stats sometimes, ignore these columns if it is constant accross records.')
                
                # The structure:
                gun_table = [['Record', '# Games', 'Kills', 'HS'] + [STAT_LIST[i][2] for i in gun_stats]]
                r0 = allrecords[0]
                for r1 in allrecords:
                    if r1 == r0:
                        r0 = r1
                        continue
                    new_row = [r0['dt'].split('.')[0],
                               (r1['ranked_won'] + r1['casual_won'] + r1['ranked_lost'] + r1['casual_lost']) - (r0['ranked_won'] + r0['casual_won'] + r0['ranked_lost'] + r0['casual_lost']),
                               r1['ranked_kill'] + r1['casual_kill'] - r0['ranked_kill'] - r0['casual_kill'],
                               r1['headshots'] - r0['headshots']]
                    for i in gun_stats:
                        cs = STAT_LIST[i][1]
                        new_row.append(r1[cs] - r0[cs])
                    gun_table.append(new_row)
                    r0 = r1
                gun_table.append([allrecords[-1]['dt'].split('.')[0]] + ['']*(len(gun_table[0])-1))
                print('\nGun Stats In-Between Progress:')
                pretty_print(gun_table)

                # Gun Cumulative Progress:

                # The structure:
                gun_table = [['Record', '# Games', 'Kills', 'HS'] + [STAT_LIST[i][2] for i in gun_stats]]
                r0 = allrecords[0]
                for r1 in allrecords:
                    new_row = [
                        r1['dt'].split('.')[0],
                        r1['ranked_won'] + r1['casual_won'] + r1['ranked_lost'] + r1['casual_lost'],
                        r1['ranked_kill'] + r1['casual_kill'],
                        r1['headshots']
                        ]
                    for i in gun_stats:
                        cs = STAT_LIST[i][1]
                        new_row.append(r1[cs])
                    gun_table.append(new_row)
                    r0 = r1
                p0 = gun_table[1]
                p1 = gun_table[-1]
                
                diff = [
                    '(Diff)',
                    p1[1] - p0[1], # Games
                    p1[2] - p0[2], # Kills
                    p1[3] - p0[3], # HS
                    ]
                for i in range(4, len(gun_table[0])):
                    diff.append(p1[i] - p0[i])
                gun_table.append(diff)
                print('\nGun Stats Cumulative Progress:')
                pretty_print(gun_table)
            
            
        
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
    Returns a list of last records of all players in database
    '''
    def get_last_records(self):
        sqcmd = '''SELECT players.id, players.name, stats.*
            FROM players, stats
            WHERE
                stats.id = (SELECT MAX(id) FROM stats as s2 WHERE s2.player_id = players.id)
            ORDER BY stats.skill_mean DESC
        '''
        self.cursor.execute(sqcmd)
        allplayers = self.cursor.fetchall()
        comp_table = [['Player', '# Games', 'Total Time Played', 'K', 'D', 'K/D', 'HS', 'HPK', 'W', 'L', 'W/L', 'Rank', 'Max Rank', 'MMR',  'Max MMR', 'Skill', 'Skill Std']]
        
        for p in allplayers:
            total_time = datetime.timedelta(seconds=p['time_played'])
            #print(datetime.timedelta.(total_time))
            total_time = '{} hours {} minutes'.format(divmod(p['time_played'],3600)[0],divmod(p['time_played'],60)[1])
            comp_table.append([
                p['name'],
                p['match_played'],
                #p['time_played'],
                total_time,
                p['ranked_kill'],
                p['ranked_death'],
                '{:.4f}'.format(p['ranked_kill']/max(1,p['ranked_death'])),
                p['headshots'],
                '{:.4f}'.format(p['headshots']/max(1,p['ranked_kill']+p['casual_kill'])),
                p['ranked_won'],
                p['ranked_lost'],
                '{:.4f}'.format(p['ranked_won']/max(1,p['ranked_lost'])),
                RANKS[round(p['rank'])],
                RANKS[round(p['max_rank'])],
                '{:.3f}'.format(p['mmr']),
                '{:.3f}'.format(p['max_mmr']),
                '{:.3f}'.format(p['skill_mean']),
                '{:.3f}'.format(p['skill_std'])
                ])
        print('Player comparison:')
        pretty_print(comp_table)

    '''
    Prints season stats for all players
    '''
    def get_season_stats(self):
        players = self.get_all_players()
        for player in players:
            sqcmd = 'SELECT * FROM seasons WHERE seasons.player_id = {} ORDER BY season DESC'.format(player['id'])
            self.cursor.execute(sqcmd)
            seasons = self.cursor.fetchall()
            if len(seasons) == 0:
                self.save_season_stats()
            player_table = [['Season Name', 'Season', 'W', 'L', 'W/L', 'Last Rank', 'MMR', 'Max Rank', 'Max MMR', 'Skill', 'Skill-Low', 'Skill-High']]
            for s in seasons:
                if s['season_wins'] + s['season_losses'] <= 0.5:
                    continue
                try:
                    season_name = SEASONS[s['season']]
                except:
                    season_name = ''
                player_table.append([
                    season_name,
                    s['season'],
                    int(s['season_wins']),
                    int(s['season_losses']),
                    '{:.4f}'.format(s['season_wins']/max(1,s['season_losses'])),
                    RANKS[int(s['rank'])],
                    '{:.3f}'.format(s['mmr']),
                    RANKS[int(s['max_rank'])],
                    '{:.3f}'.format(s['max_mmr']),
                    '{:.3f}'.format(s['skill_mean']),
                    '{:.3f}'.format(s['skill_mean'] - 1.96*s['skill_std']),
                    '{:.3f}'.format( s['skill_mean'] + 1.96*s['skill_std'])
                    ])
            print('Season Stats for {}'.format(player['name']))
            pretty_print(player_table)
            print('')

    def save_season_stats(self):
        players = self.get_all_players()
        print('WARNING: Ubi has a problem listing seasons before Velvet Shell (5)')
        # Get current season stats to find out max number of seasons to be pulled
        res = self.u.get_rank(id=players[0]['uplay_id'], region=players[0]['region'])
        current_season = res['season']
        for player in players:
            for season in range(1,current_season+1):
                ps = self.u.get_rank(id=player['uplay_id'], region=player['region'], season=season)
                cols = ', '.join(p[1] for p in PROGRESS_LIST)
                vals = '{}, {}, '.format(player['id'], season) + ', '.join(str(ps[p[0]]) for p in PROGRESS_LIST)
                sqcmd = 'INSERT OR REPLACE INTO seasons (player_id, season, {cols}) VALUES ({vals});'.format(cols=cols, vals=vals)
                self.cursor.execute(sqcmd)
        self.db.commit()

    '''
    Prints all table contents to console
    '''
    def print_all_db(self):
        tables = ['players', 'records', 'stats', 'seasons']
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
