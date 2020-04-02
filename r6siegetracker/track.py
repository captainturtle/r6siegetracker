import os
import sqlite3
from r6siegetracker.connect import UbiConnection
from r6siegetracker.constants import STAT_LIST, PROGRESS_LIST, RANKS, REGIONS, SEASONS, DB_VERSION
from r6siegetracker.constants import SORTED_OPERATOR_LIST, OPERATOR_COLUMN_LIST,  GUN_LIST, GUN_COLUMN_LIST
import datetime
from shutil import copyfile

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
        print('INFO: Initialized the tracker.')

    '''
    Creates database files for the first use
    '''
    def install(self, check=True):
        self.db = sqlite3.connect('rainbow.db', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        # Table 1 DBINFO
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                               dbinfo(tag INTEGER UNIQUE, value VARCHAR(100))
                            ''')
        # Check version
        if check:
            self.cursor.execute('SELECT * FROM dbinfo WHERE tag="version"')
            res = self.cursor.fetchone()
            if res is None:
                # New db - set the version
                self.cursor.execute('INSERT INTO dbinfo (tag, value) VALUES ("version", {});'.format(DB_VERSION))
                self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("install_date", "{}");'.format(datetime.datetime.now()))
                self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", NULL);')
                self.db.commit()
            else:
                print('Tracker database exists (DB version: {})'.format(res['value']))
                if DB_VERSION != int(res['value']):
                    print('An update is needed! DB version of the tracker object should be {}, updating.'.format(DB_VERSION))
                    self.update_db(res['value'])
                    return

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
                               stats(player_id INTEGER, record_id INTEGER,
                                     {} FLOAT,
                                     {} FLOAT,
                                     PRIMARY KEY (player_id, record_id));
                            '''.format(' INTEGER, '.join(s[1] for s in STAT_LIST), ' FLOAT, '.join(p[1] for p in PROGRESS_LIST)))
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                               seasons(player_id INTEGER, season INTEGER,
                                     {} FLOAT,
                                     PRIMARY KEY (player_id, season));
                            '''.format(' FLOAT, '.join(p[1] for p in PROGRESS_LIST)))
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                               op_stats(player_id INTEGER, record_id INTEGER,
                                         {} ,
                                         PRIMARY KEY (player_id, record_id))
                            '''.format(', '.join(o[2] + ' INTEGER DEFAULT 0' for o in OPERATOR_COLUMN_LIST)))
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                               gun_stats(player_id INTEGER, record_id INTEGER,
                                         {},
                                         PRIMARY KEY (player_id, record_id))
                            '''.format(' INTEGER, '.join(g[1] for g in GUN_COLUMN_LIST)))
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                               games(id INTEGER PRIMARY KEY AUTOINCREMENT, record_id INTEGER,
                               queue VARCHAR(10),
                               map VARCHAR(100),
                               round_wins INTEGER,
                               round_losses INTEGER,
                               attack_wins INTEGER,
                               attack_losses INTEGER,
                               defense_wins INTEGER,
                               defense_losses INTEGER)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                               game_players(game_id INTEGER, player_id INTEGER,
                               kills INTEGER,
                               assists INTEGER,
                               deaths INTEGER,
                               mmr FLOAT, PRIMARY KEY(game_id, player_id))''')
        self.db.commit()
        print('INFO: Installed or updated database rainbow.db.')

    '''
    Updates the database (new operators, etc..)
    '''
    def update_db(self, version):
        version = int(version)
        
        if version == 2: # 2 to 3 upgrade
            self.cursor.execute('ALTER TABLE operators RENAME TO _operators')
            self.cursor.execute('ALTER TABLE stats RENAME TO _stats')
            self.install(False)
            # op_stats
            self.cursor.execute('INSERT INTO op_stats SELECT * FROM _operators;')
            self.cursor.execute('DROP TABLE _operators;')
            self.db.commit()
            # gun_stats
            self.cursor.execute('INSERT INTO gun_stats ({cols}) SELECT {cols} FROM _stats;'.format(cols=', '.join(['player_id', 'record_id'] + [g[1] for g in GUN_COLUMN_LIST])))
            self.db.commit()
            # stats
            self.cursor.execute('INSERT INTO stats ({cols}) SELECT {cols} FROM _stats;'.format(cols=', '.join(['player_id', 'record_id'] + [s[1] for s in STAT_LIST] + [p[1] for p in PROGRESS_LIST])))
            self.cursor.execute('DROP TABLE _stats;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(3))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version 3')
            version += 1
        if version == 3: # 3 to 4 upgrade
            # No changes from 3 to 4, except new tables
            # dbinfo
            self.install(False)
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(4))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version 4')
            version += 1
        if version == 4: # 4 to 5 upgrade
            # New operators: Alibi and Maestro
            self.cursor.execute('ALTER TABLE op_stats RENAME TO _old_op_stats')
            self.install(False)
            self.cursor.execute('PRAGMA TABLE_INFO(_old_op_stats);')
            self.cursor.execute('INSERT INTO op_stats ({cols}) SELECT {cols} FROM _old_op_stats;'.format(cols=', '.join([i[1] for i in self.cursor.fetchall()])))
            self.cursor.execute('DROP TABLE _old_op_stats;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(5))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version 5')
            version += 1
        if version == 5: # 5 to 6 update
            # Replace NULL with 0
            self.cursor.execute('PRAGMA TABLE_INFO(op_stats);')
            self.cursor.execute('UPDATE op_stats SET {};'.format(', '.join(['{} = IFNULL({}, 0)'.format(col[1], col[1]) for col in self.cursor.fetchall()])))
            self.db.commit()
            self.cursor.execute('ALTER TABLE op_stats RENAME TO _copy;')
            self.db.commit()
            self.install(False)
            self.cursor.execute('INSERT INTO op_stats SELECT * FROM _copy;')
            self.cursor.execute('DROP TABLE _copy;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(6))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version 6')
            version += 1
        if version == 6: # 6 to 7 update
            # New operators clash and maverick
            self.cursor.execute('ALTER TABLE op_stats RENAME TO _old_op_stats')
            self.install(False)
            self.cursor.execute('PRAGMA TABLE_INFO(_old_op_stats);')
            self.cursor.execute('INSERT INTO op_stats ({cols}) SELECT {cols} FROM _old_op_stats;'.format(cols=', '.join([i[1] for i in self.cursor.fetchall()])))
            self.cursor.execute('DROP TABLE _old_op_stats;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(7))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version 7')
            version += 1
        if version == 7: # 7 to 8 update
            # Fix for Capitao typo
            self.cursor.execute('ALTER TABLE op_stats RENAME TO _old_op_stats')
            self.install(False)
            self.cursor.execute('PRAGMA TABLE_INFO(_old_op_stats);')
            old_cols = []
            new_cols = []
            for i in self.cursor.fetchall():
                if 'capiato' not in i[1]:
                    old_cols.append(i[1])
                    new_cols.append(i[1])
                else:
                    old_cols.append(i[1])
                    new_cols.append(i[1].replace('capiato', 'capitao'))
            self.cursor.execute('INSERT INTO op_stats ({new_cols}) SELECT {old_cols} FROM _old_op_stats;'.format(
                old_cols=', '.join(old_cols), new_cols=', '.join(new_cols)))
            self.cursor.execute('DROP TABLE _old_op_stats;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(8))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(
                datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version 8')
            version += 1
        if version == 8: # 8 to 9 update
            # New season operators, Nomad and Kaid
            self.cursor.execute('DROP TABLE IF EXISTS _op_stats;')
            self.db.commit()
            self.cursor.execute('ALTER TABLE op_stats RENAME TO _old_op_stats')
            self.install(False)
            self.cursor.execute('PRAGMA TABLE_INFO(_old_op_stats);')
            self.cursor.execute('INSERT INTO op_stats ({cols}) SELECT {cols} FROM _old_op_stats;'.format(cols=', '.join([i[1] for i in self.cursor.fetchall()])))
            self.cursor.execute('DROP TABLE _old_op_stats;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(9))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version 9')
            version += 1
        if version == 9: # 9 to 10 update
            # New season, new operators Mozzie and Gridlock
            self.cursor.execute('DROP TABLE IF EXISTS _op_stats;')
            self.db.commit()
            self.cursor.execute('ALTER TABLE op_stats RENAME TO _old_op_stats')
            self.install(False)
            self.cursor.execute('PRAGMA TABLE_INFO(_old_op_stats);')
            self.cursor.execute('INSERT INTO op_stats ({cols}) SELECT {cols} FROM _old_op_stats;'.format(cols=', '.join([i[1] for i in self.cursor.fetchall()])))
            self.cursor.execute('DROP TABLE _old_op_stats;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(10))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version 10')
            version += 1
        if version == 10:
            # New season, new operators
            self.cursor.execute('DROP TABLE IF EXISTS _op_stats;')
            self.db.commit()
            self.cursor.execute('ALTER TABLE op_stats RENAME TO _old_op_stats')
            self.install(False)
            self.cursor.execute('PRAGMA TABLE_INFO(_old_op_stats);')
            self.cursor.execute('INSERT INTO op_stats ({cols}) SELECT {cols} FROM _old_op_stats;'.format(cols=', '.join([i[1] for i in self.cursor.fetchall()])))
            self.cursor.execute('DROP TABLE _old_op_stats;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(version+1))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version {}'.format(version+1))
            version += 1
        if version == 11:
            # New season, new operators
            self.cursor.execute('DROP TABLE IF EXISTS _op_stats;')
            self.db.commit()
            self.cursor.execute('ALTER TABLE op_stats RENAME TO _old_op_stats')
            self.install(False)
            self.cursor.execute('PRAGMA TABLE_INFO(_old_op_stats);')
            self.cursor.execute('INSERT INTO op_stats ({cols}) SELECT {cols} FROM _old_op_stats;'.format(cols=', '.join([i[1] for i in self.cursor.fetchall()])))
            self.cursor.execute('DROP TABLE _old_op_stats;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(version+1))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version {}'.format(version+1))
            version += 1
        if version == 12:
            # New season, new operators
            self.cursor.execute('DROP TABLE IF EXISTS _op_stats;')
            self.db.commit()
            self.cursor.execute('ALTER TABLE op_stats RENAME TO _old_op_stats')
            self.install(False)
            self.cursor.execute('PRAGMA TABLE_INFO(_old_op_stats);')
            self.cursor.execute('INSERT INTO op_stats ({cols}) SELECT {cols} FROM _old_op_stats;'.format(cols=', '.join([i[1] for i in self.cursor.fetchall()])))
            self.cursor.execute('DROP TABLE _old_op_stats;')
            self.db.commit()
            # dbinfo
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("version", {});'.format(version+1))
            self.cursor.execute('INSERT OR REPLACE INTO dbinfo (tag, value) VALUES ("update_date", "{}");'.format(datetime.datetime.now()))
            self.db.commit()
            print('Updated DB to version {}'.format(version+1))
            version += 1
            
    '''
    Adds a new player to the database
    '''
    def add_player(self, name, region=None):
        u = self.u
        id = u.get_player_by_name(name)
        if id is None:
            print('ERROR: Failed to add {}, ID is not found'.format(name))
            return None
        print('INFO: Found user {} ({})'.format(name, id))
        try:
            self.u.get_stats(ids=[id])
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
        except:
            print('ERROR: An error occured while obtaining initial stats.')
            return
        self.cursor.execute('INSERT OR IGNORE INTO players (name, uplay_id, region) VALUES (?,?,?);',(name,id, region))
        self.db.commit()
        if self.cursor.rowcount == 1:
            print('INFO: Added player {} (ID={})'.format(name, id))
            self.save_state()
            return id
        else:
            print('WARNING: Could not add player {}, possible duplicate'.format(name))
            return None

    '''
    Removes a player from the database
    '''
    def remove_player(self, name):
        u = self.u
        id = u.get_player_by_name(name)
        self.cursor.execute('DELETE FROM players WHERE uplay_id = "{}"'.format(id))
        self.db.commit()
        if self.cursor.rowcount == 1:
            print('INFO: Removed player {} (ID={})'.format(name, id))
            return True
        else:
            print('WARNING: Could not remove player {}, does not exist!'.format(name))
            return False

    '''
    Creates an entry in records table, it checks all players record only those who have played games since the last record
    '''
    def save_state(self, verbose=False, force=False):
        # Get a list of all players
        u = self.u
        players = self.get_all_players()
        # Check if there are any updates
        if not players:
            print('ERROR: No players in DB')
            return None
        if not force:
            new_save = self.is_save_required(players)
            if not any(new_save):
                print('Checked the stats, no updates have been found.')
                return None
        else:
            new_save = [True for i in players]

        # Crete a new checkpoint
        print('Getting new records...')
        dt = str(datetime.datetime.now())
        # Create a new record point
        sqcmd = 'INSERT INTO records(dt) VALUES("{}")'.format(dt)
        self.cursor.execute(sqcmd)
        record_id = self.cursor.lastrowid
        # Get all stats
        stats = u.get_stats([p['uplay_id'] for p in players])
        ops = u.get_operator_stats([p['uplay_id'] for p in players])
        guns = u.get_gun_stats([p['uplay_id'] for p in players])
        for i, player in enumerate(players):
            p_stat = stats[i]
            p_op_stat = ops[i]
            p_gun_stat = guns[i]
            if not new_save[i]:
                continue
            print('Getting current stats for {}'.format(player['name']))
            # Get stats
            rank = u.get_rank(player['uplay_id'], region=player['region'])
            all_stats = []
            for s in STAT_LIST:
                try:
                    all_stats.append(str(p_stat[s[0]]))
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
            sqcmd = 'INSERT INTO stats VALUES({},{},{});'.format(player['id'], record_id, merged_stats)
            self.cursor.execute(sqcmd)
            op_merged_stats = ', '.join(str(p_op_stat[op[0]]) if op[0] in p_op_stat else '0' for op in OPERATOR_COLUMN_LIST)
            opsqcmd = 'INSERT INTO op_stats VALUES({}, {}, {});'.format(player['id'], record_id, op_merged_stats)
            self.cursor.execute(opsqcmd)
            gun_merge_stats = ', '.join(str(p_gun_stat[gn[0]]) if gn[0] in p_gun_stat else '0' for gn in GUN_COLUMN_LIST)
            gunsqcmd = 'INSERT INTO gun_stats VALUES({}, {}, {});'.format(player['id'], record_id, gun_merge_stats)
            self.cursor.execute(gunsqcmd)
        self.db.commit()
        
        # Update seasons stats
        # self.save_season_stats()
        
        print('Saved the current stats to DB.')
        return record_id

    def get_last_record_id(self):
        self.cursor.execute('SELECT id FROM records ORDER BY id DESC LIMIT 1;')
        return self.cursor.fetchone()[0]

    '''
    Creates an entry in records and games tables, returns the id of the game for individual stats
    '''
    def save_game(self, record_id=None, queue=None, map=None, round_wins=None, round_losses=None, attack_wins=None, attack_losses=None, defense_wins=None, defense_losses=None, player_data=None):
        if record_id is None:
            record_id = self.save_state(force=True)
        values = [record_id, queue, map, round_wins, round_losses, attack_wins, attack_losses, defense_wins, defense_losses]
        value_str = []
        for v in values:
            if v is None:
                value_str.append('NULL')
            elif type(v) == str:
                value_str.append('"{}"'.format(v))
            else:
                value_str.append(str(v))
        sqcmd = 'INSERT INTO games (record_id, queue, map, round_wins, round_losses, attack_wins, attack_losses, defense_wins, defense_losses) VALUES({vals});'.format(vals=', '.join(value_str))
        self.cursor.execute(sqcmd)
        self.db.commit()
        print('Saved the game, id={}'.format(self.cursor.lastrowid))
        if player_data:
            # Also record player stats, otherwise use save_player_game_stats
            print('Saving player stats in game.')

    '''
    Returns a list of booleans for players whose stats should be updated
    '''
    def is_save_required(self, player_list):
        lastgames = [0]*len(player_list)
        new_save = [False]*len(player_list)
        # Either has no records
        for i, player in enumerate(player_list):
            sqcmd = 'SELECT * FROM stats WHERE player_id = {} ORDER BY record_id DESC LIMIT 1;'.format(player[0])
            self.cursor.execute(sqcmd)
            lastgame = self.cursor.fetchall()
            if len(lastgame) == 0:
                print('No previous game record exists in DB for {}'.format(player['name']))
                new_save[i] = True
                lastgames[i] = 0
            else:
                lastgames[i] = lastgame[0]['match_played']
            sqcmd = 'SELECT * FROM op_stats WHERE player_id = {};'.format(player[0])
            self.cursor.execute(sqcmd)
            lastgame = self.cursor.fetchall()
            if len(lastgame) == 0:
                print('No operator stats exists in DB for {}'.format(player['name']))
                new_save[i] = True
        # Or the total games played is greater than previous record
        u = self.u
        games = u.get_total_games([player['uplay_id'] for player in player_list])
        for i in range(len(games)):
            if games[i] - lastgames[i] > 0.5:
                print('SUCCESS: {} new game(s) have been found for {}'.format(games[i]-lastgames[i], player_list[i]['name']))
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
    def get_player_progress(self, name, start_dt=None, end_dt=None, summary_type='Increment', increment=0, stype='Ranked', printStats=True, cutoff='00:00'):
        if start_dt is None:
            start_dt = self.custom_query('SELECT dt FROM records ORDER BY dt ASC LIMIT 1;')[0]['dt']
        if end_dt is None:
            end_dt = str(datetime.datetime.now())
        if increment > 0:
            start_dt = start_dt.split()[0] + ' ' + cutoff + ':00.000000'
        
        if stype == 'Ranked':
            ranked_stats = [2,3,4,5,10,11]
            
            if increment==0:
                # Get all stats first
                sqcmd = '''
                SELECT *
                FROM(
                SELECT dt, casual_won, casual_lost, {ranked}, {ranks} 
                FROM players, records, stats 
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt <= "{st}" ORDER BY stats.record_id DESC LIMIT 1
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
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt <= "{st}" ORDER BY stats.record_id DESC LIMIT 1
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
            
            if allrecords is None or len(allrecords) <= 1:
                print('WARNING: (Ranked stats) No game records between requested date-times.')
                return None
            else: 
                
                if summary_type=='Incremental':
                
                    # Ranked Progress: Ranked in-between stats
                    total_assists = 0
                    total_headshots = 0
                    
                    # The structure:
                    prog_table = [['Record', '# Games', 'K', 'A', 'D', 'K/D', 'HS', 'H/K', 'W', 'L', 'W/L', 'MMR', 'Skill', 'StDev']]
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
                            '{}{}'.format(r1['assists']-r0['assists'], '*' if inaccuracy else ''),
                            r1['ranked_death'] - r0['ranked_death'],
                            '{:.3f}'.format((r1['ranked_kill'] - r0['ranked_kill'])/max(1,r1['ranked_death'] - r0['ranked_death'])),
                            '{:.0f}{}'.format(r1['headshots']-r0['headshots'], '*' if inaccuracy else ''),
                            '{:4.2%}{}'.format((r1['headshots'] - r0['headshots'])/max(1,r1['ranked_kill']-r0['ranked_kill']), '*' if inaccuracy else ''),
                            r1['ranked_won'] - r0['ranked_won'],
                            r1['ranked_lost'] - r0['ranked_lost'],
                            '{:.3f}'.format((r1['ranked_won'] - r0['ranked_won'])/max(1,r1['ranked_lost'] - r0['ranked_lost'])),
                            '{:.2f}'.format(r1['mmr'] - r0['mmr']),
                            '{:.2f}'.format(r1['skill_mean'] - r0['skill_mean']),
                            '{:.2f}'.format(r1['skill_std'] - r0['skill_std'])
                            ])
                        total_assists += r1['assists'] - r0['assists']
                        total_headshots += r1['headshots'] - r0['headshots']
                        r0 = r1
                    prog_table.append([allrecords[-1]['dt'].split('.')[0]] + ['']*13)
                    prog_table.append(['---']*len(prog_table[0]))
                    p0 = allrecords[0]
                    p1 = allrecords[-1]
                    total = [
                        '(Total)',
                        p1['ranked_won'] + p1['ranked_lost'] - p0['ranked_won'] - p0['ranked_lost'], # Games
                        p1['ranked_kill'] - p0['ranked_kill'], # K
                        '{}{}'.format(total_assists, '*' if inaccuracy else ''),
                        p1['ranked_death'] - p0['ranked_death'], # D
                        '{:.3f}'.format((p1['ranked_kill'] - p0['ranked_kill']) / max(1, p1['ranked_death'] - p0['ranked_death'])), # K/D
                        '{:.0f}{}'.format(total_headshots,'*' if inaccuracy else ''),
                        '{:4.2%}{}'.format((total_headshots)/max(1,p1['ranked_kill']-p0['ranked_kill']), '*' if inaccuracy else ''), # H/K
                        p1['ranked_won'] - p0['ranked_won'], # W
                        p1['ranked_lost'] - p0['ranked_lost'], # L
                        '{:.3f}'.format((p1['ranked_won'] - p0['ranked_won'])/max(1,p1['ranked_lost'] - p0['ranked_lost'])), # W/L
                        '{:.2f}'.format(p1['mmr'] - p0['mmr']), # MMR
                        '{:.2f}'.format(p1['skill_mean'] - p0['skill_mean']), # Skill
                        '{:.2f}'.format(p1['skill_std'] - p0['skill_std'])
                        ]
                    prog_table.append(total)
                    
                    if printStats:
                        print('\nRanked In-Between Progress:')
                        pretty_print(prog_table)
                    return prog_table


                # Ranked Cumulative Progress:
                if summary_type=='Cumulative':

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
                        #if r1['d_from'] is not None:
                        #    recname = r1['d_from']
                        #else:
                        #    recname = r1['dt'].split('.')[0]
                        try:
                            if r1['d_to'] is None:
                                recname = r1['dt'].split(' ')[0]
                            else:
                                recname = r1['d_to']
                        except:
                            recname = r1['dt'].split('.')[0]
                        prog_table.append([
                            recname,
                            r1['ranked_won'] + r1['ranked_lost'],
                            r1['ranked_kill'],
                            r1['ranked_death'],
                            '{:.4f}'.format((r1['ranked_kill'])/max(1,r1['ranked_death'])),
                            '{:.4f}'.format((r1['ranked_kill'])/max(1,r1['ranked_won'] + r1['ranked_lost'])),
                            '{}{}'.format(r1['assists'], '*' if inaccuracy else ''),
                            '{:.4f}{}'.format(r1['assists']/max(1,r1['ranked_won'] + r1['ranked_lost']), '*' if inaccuracy else ''),
                            '{:.0f}{}'.format(r1['headshots'], '*' if inaccuracy else ''),
                            '{:.4f}{}'.format(r1['headshots']/max(1,r1['ranked_won'] + r1['ranked_lost']), '*' if inaccuracy else ''),
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
                        '{}{}'.format(int(p1[6].split('*')[0])-int(p0[6].split('*')[0]), '*' if isinstance(p1[6], str) or isinstance(p0[6], str) else ''), # A
                        '{:+.4f}{}'.format(float(p1[7].split('*')[0]) - float(p0[7].split('*')[0]), '*' if '*' in p1[7] else ''), # APG
                        '{}{}'.format(int(p1[8].split('*')[0])-int(p0[8].split('*')[0]), '*' if isinstance(p1[8], str) or isinstance(p0[8], str)  else ''), # HS
                        '{:+.4f}{}'.format(float(p1[9].split('*')[0]) - float(p0[9].split('*')[0]), '*' if '*' in p1[9] else ''), # HPG
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
                    if printStats:
                        print('\nRanked Cumulative Progress:')
                        pretty_print(prog_table)
                    return prog_table

        # Casual stats
        if stype == 'Casual':
            
            casual_stats = [6,7,8,9,10,11]

            if increment==0:
                # Get all stats first
                sqcmd = '''
                SELECT *
                FROM(
                SELECT dt, ranked_won, ranked_lost, {casual}, {ranks} 
                FROM players, records, stats 
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt <= "{st}" ORDER BY stats.record_id DESC LIMIT 1
                )
                UNION
                SELECT *
                FROM(
                SELECT dt, ranked_won, ranked_lost, {casual}, {ranks} 
                FROM players, records, stats 
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt BETWEEN "{st}" AND "{et}"
                );
                '''.format(casual=', '.join([STAT_LIST[i][1] for i in casual_stats]), ranks=', '.join([i[1] for i in PROGRESS_LIST]), name=name, st=start_dt, et=end_dt)
            else:
                sqcmd = '''
                SELECT NULL as d_from, NULL as d_to, *
                FROM(
                SELECT dt, ranked_won, ranked_lost, {casual}, {ranks} 
                FROM players, records, stats 
                WHERE players.name="{name}" AND players.id=stats.player_id AND records.id=stats.record_id AND records.dt <= "{st}" ORDER BY stats.record_id DESC LIMIT 1
                )
                '''
                
                daydiff = self.time_diff(start_dt, end_dt) #datetime.datetime.strptime(start_dt, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(end_dt, '%Y-%m-%d %H:%M:%S')
                for inc in range(0, daydiff.days+1, increment):
                    dailyunion = '''
                    UNION
                    SELECT date("{{st}}", '+{inc} days') as d_from, date("{{st}}", '+{inc1} days') as d_to, *  FROM(
                        SELECT dt, ranked_won, ranked_lost, {{casual}}, {{ranks}}
                        FROM players, records, stats 
                        WHERE players.name="{{name}}" AND players.id=stats.player_id AND records.id=stats.record_id AND dt BETWEEN datetime("{{st}}", '+{inc} days') AND datetime("{{st}}", '+{inc1} days') ORDER BY records.dt DESC LIMIT 1
                    )
                    '''.format(inc = inc, inc1 = inc+increment)
                    sqcmd += dailyunion
                # Calculate day diff

                sqcmd = sqcmd.format(casual=', '.join([STAT_LIST[i][1] for i in casual_stats]), ranks=', '.join([i[1] for i in PROGRESS_LIST]), name=name, st=start_dt, et=end_dt)
                # For loop for increment
                
                
            self.cursor.execute(sqcmd)
            allrecords = self.cursor.fetchall()
            
            if allrecords is None or len(allrecords) <= 1:
                print('WARNING: (Casual stats) No game records between requested date-times.')
                return None
            else: 
                
                if summary_type=='Incremental':
                
                    # Casual Progress: Casual in-between stats
                    total_assists = 0
                    total_headshots = 0
                    
                    # The structure:
                    prog_table = [['Record', '# Games', 'K', 'A', 'D', 'K/D', 'HS', 'H/K', 'W', 'L', 'W/L', 'MMR', 'Skill', 'StDev']]
                    
                    prog_table = [['Record', '# Games', 'K', 'A', 'D', 'K/D', 'HS', 'H/K', 'W', 'L', 'W/L']]
                    
                    r0 = allrecords[0]
                    inaccuracy = False
                    for r1 in allrecords:
                        if r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'] < 0.5:
                            # No casual games between records
                            r0 = r1
                            continue
                        inaccuracy = False
                        if (r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] > 0.5):
                            inaccuracy = True
                        try:
                            recname = r1['d_from'] + ' to ' + r1['d_to']
                        except:
                            recname = r0['dt'].split('.')[0]
                        prog_table.append([
                            recname,
                            r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'],
                            r1['casual_kill'] - r0['casual_kill'],
                            '{}{}'.format(r1['assists']-r0['assists'], '*' if inaccuracy else ''),
                            r1['casual_death'] - r0['casual_death'],
                            '{:.3f}'.format((r1['casual_kill'] - r0['casual_kill'])/max(1,r1['casual_death'] - r0['casual_death'])),
                            '{:.0f}{}'.format(r1['headshots']-r0['headshots'], '*' if inaccuracy else ''),
                            '{:4.2%}{}'.format((r1['headshots'] - r0['headshots'])/max(1,r1['casual_kill']-r0['casual_kill']), '*' if inaccuracy else ''),
                            r1['casual_won'] - r0['casual_won'],
                            r1['casual_lost'] - r0['casual_lost'],
                            '{:.3f}'.format((r1['casual_won'] - r0['casual_won'])/max(1,r1['casual_lost'] - r0['casual_lost'])),
                            ])
                        total_assists += r1['assists'] - r0['assists']
                        total_headshots += r1['headshots'] - r0['headshots']
                        r0 = r1
                    prog_table.append([allrecords[-1]['dt'].split('.')[0]] + ['']*10)
                    prog_table.append(['---']*len(prog_table[0]))
                    p0 = allrecords[0]
                    p1 = allrecords[-1]
                    total = [
                        '(Total)',
                        p1['casual_won'] + p1['casual_lost'] - p0['casual_won'] - p0['casual_lost'], # Games
                        p1['casual_kill'] - p0['casual_kill'], # K
                        '{}{}'.format(total_assists, '*' if inaccuracy else ''),
                        p1['casual_death'] - p0['casual_death'], # D
                        '{:.3f}'.format((p1['casual_kill'] - p0['casual_kill']) / max(1, p1['casual_death'] - p0['casual_death'])), # K/D
                        '{:.0f}{}'.format(total_headshots,'*' if inaccuracy else ''),
                        '{:4.2%}{}'.format((total_headshots)/max(1,p1['casual_kill']-p0['casual_kill']), '*' if inaccuracy else ''), # H/K
                        p1['casual_won'] - p0['casual_won'], # W
                        p1['casual_lost'] - p0['casual_lost'], # L
                        '{:.3f}'.format((p1['casual_won'] - p0['casual_won'])/max(1,p1['casual_lost'] - p0['casual_lost'])), # W/L
                        ]
                    prog_table.append(total)
                    
                    if printStats:
                        print('\nCasual In-Between Progress:')
                        pretty_print(prog_table)
                    return prog_table


                # Casual Cumulative Progress:
                if summary_type=='Cumulative':

                    # The structure:
                    prog_table = [['Record', '# Games', 'K', 'D', 'K/D', 'KPG', 'Assists', 'APG', 'Headshots', 'HPG', 'W', 'L', 'W/L']]
                    r0 = allrecords[0]
                    for r1 in allrecords:
                        if r1 != r0  and (r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'] < 0.5):
                            # No casual games between records
                            r0 = r1
                            continue
                        inaccuracy = False
                        if (r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] > 0.5):
                            inaccuracy = True
                        #if r1['d_from'] is not None:
                        #    recname = r1['d_from']
                        #else:
                        #    recname = r1['dt'].split('.')[0]
                        try:
                            if r1['d_to'] is None:
                                recname = r1['dt'].split(' ')[0]
                            else:
                                recname = r1['d_to']
                        except:
                            recname = r1['dt'].split('.')[0]
                        prog_table.append([
                            recname,
                            r1['casual_won'] + r1['casual_lost'],
                            r1['casual_kill'],
                            r1['casual_death'],
                            '{:.4f}'.format((r1['casual_kill'])/max(1,r1['casual_death'])),
                            '{:.4f}'.format((r1['casual_kill'])/max(1,r1['casual_won'] + r1['casual_lost'])),
                            '{}{}'.format(r1['assists'], '*' if inaccuracy else ''),
                            '{:.4f}{}'.format(r1['assists']/max(1,r1['casual_won'] + r1['casual_lost']), '*' if inaccuracy else ''),
                            '{:.0f}{}'.format(r1['headshots'], '*' if inaccuracy else ''),
                            '{:.4f}{}'.format(r1['headshots']/max(1,r1['casual_won'] + r1['casual_lost']), '*' if inaccuracy else ''),
                            r1['casual_won'],
                            r1['casual_lost'],
                            '{:.4f}'.format((r1['casual_won'])/max(1,r1['casual_lost'])),
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
                        '{}{}'.format(int(p1[6].split('*')[0])-int(p0[6].split('*')[0]), '*' if isinstance(p1[6], str) or isinstance(p0[6], str) else ''), # A
                        '{:+.4f}{}'.format(float(p1[7].split('*')[0]) - float(p0[7].split('*')[0]), '*' if '*' in p1[7] else ''), # APG
                        '{}{}'.format(int(p1[8].split('*')[0])-int(p0[8].split('*')[0]), '*' if isinstance(p1[8], str) or isinstance(p0[8], str)  else ''), # HS
                        '{:+.4f}{}'.format(float(p1[9].split('*')[0]) - float(p0[9].split('*')[0]), '*' if '*' in p1[9] else ''), # HPG
                        p1[10] - p0[10], # W
                        p1[11] - p0[11], # L
                        '{:+.4f}'.format(float(p1[12]) - float(p0[12])), # W/L
                        ]
                    prog_table.append(diff)
                    if printStats:
                        print('\nCasual Cumulative Progress:')
                        pretty_print(prog_table)
                    return prog_table
            
            
        if stype == 'Gun':
            
            if increment==0:
                sqcmd = '''
                SELECT *
                FROM(
                SELECT dt, gun_stats.*, stats.ranked_won, stats.ranked_lost, stats.casual_won, stats.casual_lost
                FROM players, records, gun_stats, stats
                WHERE players.name="{name}" AND 
                      players.id=gun_stats.player_id AND
                      records.id=gun_stats.record_id AND 
                      players.id=stats.player_id AND
                      records.id=stats.record_id AND
                      records.dt <= "{st}" ORDER BY records.id DESC LIMIT 1
                )
                UNION
                SELECT *
                FROM(
                SELECT dt, gun_stats.*, stats.ranked_won, stats.ranked_lost, stats.casual_won, stats.casual_lost
                FROM players, records, gun_stats, stats
                WHERE players.name="{name}" AND 
                      players.id=gun_stats.player_id AND
                      records.id=gun_stats.record_id AND 
                      players.id=stats.player_id AND
                      records.id=stats.record_id AND
                      records.dt BETWEEN "{st}" AND "{et}"
                );
                '''.format(name=name, st=start_dt, et=end_dt)
            else:
                sqcmd = '''
                SELECT NULL as d_from, NULL as d_to, *
                FROM(
                SELECT dt, gun_stats.*, stats.ranked_won, stats.ranked_lost, stats.casual_won, stats.casual_lost
                FROM players, records, gun_stats, stats
                WHERE players.name="{name}" AND 
                      players.id=gun_stats.player_id AND
                      records.id=gun_stats.record_id AND 
                      players.id=stats.player_id AND
                      records.id=stats.record_id AND
                      records.dt <= "{st}" ORDER BY records.id DESC LIMIT 1
                )
                '''
                
                daydiff = self.time_diff(start_dt, end_dt)
                for inc in range(0, daydiff.days+1, increment):
                    dailyunion = '''
                    UNION
                    SELECT date("{{st}}", '+{inc} days') as d_from, date("{{st}}", '+{inc1} days') as d_to, *  FROM(
                        SELECT dt, gun_stats.*, stats.ranked_won, stats.ranked_lost, stats.casual_won, stats.casual_lost
                        FROM players, records, gun_stats, stats
                        WHERE players.name="{{name}}" AND
                              players.id=gun_stats.player_id AND
                              records.id=gun_stats.record_id AND
                              players.id=stats.player_id AND
                              records.id=stats.record_id AND
                              dt BETWEEN datetime("{{st}}", '+{inc} days') AND datetime("{{st}}", '+{inc1} days') ORDER BY records.dt DESC LIMIT 1
                    )
                    '''.format(inc = inc, inc1 = inc+increment)
                    sqcmd += dailyunion
                sqcmd = sqcmd.format(name=name, st=start_dt, et=end_dt)

            self.cursor.execute(sqcmd)
            allrecords = self.cursor.fetchall()

            if allrecords is None or len(allrecords) == 0:
                print('WARNING: (Gun stats) No game records between requested date-times.')
            elif len(allrecords) == 1:
                print('WARNING: (Gun stats) Only 1 record has been found between date-times.')
            else: 
                
                # Gun Progress: In-Between
                
                # The structure:
                gun_table = [['Record', '# Games', 'Ranked W/L', 'Casual W/L', 'Gun', 'Fired', 'Hit', 'Kills', 'HS', 'Kill/Hit', 'HS/Kill', 'HS/Hit']]
                r0 = allrecords[0]
                for r1 in allrecords:
                    if r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] + r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'] < 0.5:
                        # No games between records, this should not have happened anyway
                        r0 = r1
                        continue
                    try:
                        recname = r1['d_from'] + ' to ' + r1['d_to']
                    except:
                        recname = r0['dt'].split('.')[0]
                    # First row
                    gun_table.append([
                        recname, # Records
                        r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] + r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'], # Games
                        str(r1['ranked_won'] - r0['ranked_won']) + '/' +  # Won
                        str(r1['ranked_lost'] - r0['ranked_lost']), # Lost
                        str(r1['casual_won'] - r0['casual_won']) + '/' + # Casual won
                        str(r1['casual_lost'] - r0['casual_lost']), # Casual lost
                        ] + ['-']*8)

                    # Gun loop
                    for gn in GUN_LIST:
                        gndict = {'fired': 'fired_{}'.format(gn[1]), 'hit': 'hit_{}'.format(gn[1]), 'kill': 'kill_{}'.format(gn[1]), 'hs': 'headshot_{}'.format(gn[1])}
                        hit_total = r1[gndict['hit']] - r0[gndict['hit']]
                        if  hit_total < 0.5: # This gun should has hit at least once
                            continue
                        gun_table.append(['']*4 + [
                            gn[2], # Gun name
                            r1[gndict['fired']] - r0[gndict['fired']], # Fired
                            r1[gndict['hit']] - r0[gndict['hit']], # Hit
                            r1[gndict['kill']] - r0[gndict['kill']], # Kills
                            r1[gndict['hs']] - r0[gndict['hs']], # HS
                            '{:.2%}'.format((r1[gndict['kill']] - r0[gndict['kill']])/max(1,r1[gndict['hit']] - r0[gndict['hit']])), # K/Hit
                            '{:.2%}'.format((r1[gndict['hs']] - r0[gndict['hs']])/max(1,r1[gndict['kill']] - r0[gndict['kill']])), # HS/K
                            '{:.2%}'.format((r1[gndict['hs']] - r0[gndict['hs']])/max(1,r1[gndict['hit']] - r0[gndict['hit']])), # HS/Hit
                            ])
                    totalfired = sum([int(r1[i]) - int(r0[i]) for i in r0.keys() if 'fired_' in i])
                    totalhit =   sum([int(r1[i]) - int(r0[i]) for i in r0.keys() if 'hit_' in i])
                    totalkill =  sum([int(r1[i]) - int(r0[i]) for i in r0.keys() if 'kill_' in i])
                    totalhs =    sum([int(r1[i]) - int(r0[i]) for i in r0.keys() if 'headshot_' in i])
                    
                    gun_table.append(['']*4 + [
                        '(Total)',
                        totalfired,
                        totalhit,
                        totalkill,
                        totalhs,
                        '{:.2%}'.format(totalkill/max(1,totalhit)),
                        '{:.2%}'.format(totalhs/max(1,totalkill)),
                        '{:.2%}'.format(totalhs/max(1,totalhit))
                        ])
                    r0 = r1
                # Grand total
                gun_table.append(['---']*len(gun_table[0]))
                p1 = allrecords[-1]
                p0 = allrecords[0]
                gun_table.append([
                    '(Grand Total)', # Records
                    p1['ranked_won'] + p1['ranked_lost'] - p0['ranked_won'] - p0['ranked_lost'] + p1['casual_won'] + p1['casual_lost'] - p0['casual_won'] - p0['casual_lost'], # Games
                    str(p1['ranked_won'] - p0['ranked_won']) + '/' +  # Won
                    str(p1['ranked_lost'] - p0['ranked_lost']), # Lost
                    str(p1['casual_won'] - p0['casual_won']) + '/' + # Casual won
                    str(p1['casual_lost'] - p0['casual_lost']), # Casual lost
                    ] + ['-']*8)
                del r0
                del r1
                for gn in GUN_LIST:
                    gndict = {'fired': 'fired_{}'.format(gn[1]), 'hit': 'hit_{}'.format(gn[1]), 'kill': 'kill_{}'.format(gn[1]), 'hs': 'headshot_{}'.format(gn[1])}
                    hit_total = p1[gndict['hit']] - p0[gndict['hit']]
                    if  hit_total < 0.5: # This gun should has hit at least once
                        continue
                    gun_table.append(['']*4 + [
                        gn[2], # Gun name
                        p1[gndict['fired']] - p0[gndict['fired']], # Fired
                        p1[gndict['hit']] - p0[gndict['hit']], # Hit
                        p1[gndict['kill']] - p0[gndict['kill']], # Kills
                        p1[gndict['hs']] - p0[gndict['hs']], # HS
                        '{:.2%}'.format((p1[gndict['kill']] - p0[gndict['kill']])/max(1,p1[gndict['hit']] - p0[gndict['hit']])), # K/Hit
                        '{:.2%}'.format((p1[gndict['hs']] - p0[gndict['hs']])/max(1,p1[gndict['kill']] - p0[gndict['kill']])), # HS/K
                        '{:.2%}'.format((p1[gndict['hs']] - p0[gndict['hs']])/max(1,p1[gndict['hit']] - p0[gndict['hit']])) # HS/Hit
                        ])
                
                if printStats:
                    print('\nGun In-Between Stats')
                    pretty_print(gun_table)
                return gun_table

        if stype == 'Operator':
            if increment==0:
                sqcmd = '''
                SELECT *
                FROM(
                SELECT dt, op_stats.*, stats.ranked_won, stats.ranked_lost, stats.casual_won, stats.casual_lost
                FROM players, records, op_stats, stats
                WHERE players.name="{name}" AND 
                      players.id=op_stats.player_id AND
                      records.id=op_stats.record_id AND 
                      players.id=stats.player_id AND
                      records.id=stats.record_id AND
                      records.dt <= "{st}" ORDER BY records.id DESC LIMIT 1
                )
                UNION
                SELECT *
                FROM(
                SELECT dt, op_stats.*, stats.ranked_won, stats.ranked_lost, stats.casual_won, stats.casual_lost
                FROM players, records, op_stats, stats
                WHERE players.name="{name}" AND 
                      players.id=op_stats.player_id AND
                      records.id=op_stats.record_id AND 
                      players.id=stats.player_id AND
                      records.id=stats.record_id AND
                      records.dt BETWEEN "{st}" AND "{et}"
                );
                '''.format(name=name, st=start_dt, et=end_dt)
            else:
                sqcmd = '''
                SELECT NULL as d_from, NULL as d_to, *
                FROM(
                SELECT dt, op_stats.*, stats.ranked_won, stats.ranked_lost, stats.casual_won, stats.casual_lost
                FROM players, records, op_stats, stats
                WHERE players.name="{name}" AND 
                      players.id=op_stats.player_id AND
                      records.id=op_stats.record_id AND 
                      players.id=stats.player_id AND
                      records.id=stats.record_id AND
                      records.dt <= "{st}" ORDER BY records.id DESC LIMIT 1
                )
                '''
                
                daydiff = self.time_diff(start_dt, end_dt)
                for inc in range(0, daydiff.days+1, increment):
                    dailyunion = '''
                    UNION
                    SELECT date("{{st}}", '+{inc} days') as d_from, date("{{st}}", '+{inc1} days') as d_to, *  FROM(
                        SELECT dt, op_stats.*, stats.ranked_won, stats.ranked_lost, stats.casual_won, stats.casual_lost
                        FROM players, records, op_stats, stats
                        WHERE players.name="{{name}}" AND
                              players.id=op_stats.player_id AND
                              records.id=op_stats.record_id AND
                              players.id=stats.player_id AND
                              records.id=stats.record_id AND
                              dt BETWEEN datetime("{{st}}", '+{inc} days') AND datetime("{{st}}", '+{inc1} days') ORDER BY records.dt DESC LIMIT 1
                    )
                    '''.format(inc = inc, inc1 = inc+increment)
                    sqcmd += dailyunion
                sqcmd = sqcmd.format(name=name, st=start_dt, et=end_dt)
            
            self.cursor.execute(sqcmd)
            allrecords = self.cursor.fetchall()

            if allrecords is None or len(allrecords) == 0:
                print('WARNING: (Operator Stats) No game records between requested date-times.')
            elif len(allrecords) == 1:
                print('WARNING: (Operator Stats) Only 1 record has been found between date-times.')
            else: 
                
                # Operator Progress: In-Between
                # The structure:
                opd_table = [['Record', '# Games', 'Ranked W', 'Ranked L', 'Casual W', 'Casual L', 'Side', 'Operator', 'Round W', 'Round L', 'W/L', 'K', 'D', 'K/D', 'Survival%', 'Time Played']]
                r0 = allrecords[0]
                for r1 in allrecords:
                    if r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] + r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'] < 0.5:
                        # No games between records, this should not have happened anyway
                        r0 = r1
                        continue
                    try:
                        recname = r1['d_from'] + ' to ' + r1['d_to']
                    except:
                        recname = r0['dt'].split('.')[0]
                    prevop = None
                    # First row
                    opd_table.append([
                        recname, # Records
                        r1['ranked_won'] + r1['ranked_lost'] - r0['ranked_won'] - r0['ranked_lost'] + r1['casual_won'] + r1['casual_lost'] - r0['casual_won'] - r0['casual_lost'], # Games
                        r1['ranked_won'] - r0['ranked_won'], # Won
                        r1['ranked_lost'] - r0['ranked_lost'], # Lost
                        r1['casual_won'] - r0['casual_won'], # Casual won
                        r1['casual_lost'] - r0['casual_lost'], # Casual lost
                        ] + ['-']*10)
                    
                    # Operator loop
                    for op in SORTED_OPERATOR_LIST:
                        opdict = {'played': '{}_tp'.format(op[2]), 'won': '{}_rw'.format(op[2]), 'lost': '{}_rl'.format(op[2]), 'kill': '{}_k'.format(op[2]), 'death': '{}_d'.format(op[2])}
                        number_of_round = r1[opdict['won']] + r1[opdict['lost']] - r0[opdict['won']] - r0[opdict['lost']]
                        if  number_of_round < 0.5: # This operator has chosen at least once
                            continue
                        try:
                            side = '' if prevop[3] == op[3] else op[3]
                        except:
                            side = op[3]
                        opd_table.append(['']*6 + [
                            side, # Side
                            op[1], # Operator name
                            r1[opdict['won']] - r0[opdict['won']], # Round won
                            r1[opdict['lost']] - r0[opdict['lost']], # Round won
                            '{:.3f}'.format((r1[opdict['won']] - r0[opdict['won']])/max(1,r1[opdict['lost']] - r0[opdict['lost']])), # W/L
                            r1[opdict['kill']] - r0[opdict['kill']], # K
                            r1[opdict['death']] - r0[opdict['death']], # D
                            '{:.3f}'.format((r1[opdict['kill']] - r0[opdict['kill']])/max(1,r1[opdict['death']] - r0[opdict['death']])), # K/D
                            '{:.2%}'.format((number_of_round - (r1[opdict['death']] - r0[opdict['death']]))/number_of_round), # Survival
                            time_to_string(r1[opdict['played']] - r0[opdict['played']]), # Time played
                            ])
                        prevop = op
                    totalwon = sum([r1[i] - r0[i] for i in r0.keys() if '_rw' in i])
                    totallost = sum([r1[i] - r0[i] for i in r0.keys() if '_rl' in i])
                    totalkill = sum([r1[i] - r0[i] for i in r0.keys() if '_k' in i])
                    totaldeath = sum([r1[i] - r0[i] for i in r0.keys() if '_d' in i])
                    totaltp =  sum([r1[i] - r0[i] for i in r0.keys() if '_tp' in i])
                    opd_table.append(['']*6 + [
                        '(Total)',
                        '-',
                        totalwon,
                        totallost,
                        '{:.3f}'.format(totalwon/max(1,totallost)),
                        totalkill,
                        totaldeath,
                        '{:.3f}'.format(totalkill/max(1,totaldeath)),
                        '{:.2%}'.format((totalwon+totallost-totaldeath)/max(1,totalwon+totallost)),
                        time_to_string(totaltp)
                        ])
                    r0 = r1
                # Grand total
                opd_table.append(['---']*len(opd_table[0]))
                p1 = allrecords[-1]
                p0 = allrecords[0]
                opd_table.append([
                    '(Grand Total)', # Records
                    p1['ranked_won'] + p1['ranked_lost'] - p0['ranked_won'] - p0['ranked_lost'] + p1['casual_won'] + p1['casual_lost'] - p0['casual_won'] - p0['casual_lost'], # Games
                    p1['ranked_won'] - p0['ranked_won'], # Won
                    p1['ranked_lost'] - p0['ranked_lost'], # Lost
                    p1['casual_won'] - p0['casual_won'], # Casual won
                    p1['casual_lost'] - p0['casual_lost'], # Casual lost
                    ] + ['-']*10)
                for op in SORTED_OPERATOR_LIST:
                    opdict = {'played': '{}_tp'.format(op[2]), 'won': '{}_rw'.format(op[2]), 'lost': '{}_rl'.format(op[2]), 'kill': '{}_k'.format(op[2]), 'death': '{}_d'.format(op[2])}
                    number_of_round = p1[opdict['won']] + p1[opdict['lost']] - p0[opdict['won']] - p0[opdict['lost']]
                    if  number_of_round < 0.5: # This operator has chosen at least once
                        continue
                    try:
                        side = '' if prevop[3] == op[3] else op[3]
                    except:
                        side = op[3]
                    opd_table.append(['']*6 + [
                        side, # Side
                        op[1], # Operator name
                        p1[opdict['won']] - p0[opdict['won']], # Round won
                        p1[opdict['lost']] - p0[opdict['lost']], # Round won
                        '{:.3f}'.format((p1[opdict['won']] - p0[opdict['won']])/max(1,p1[opdict['lost']] - p0[opdict['lost']])), # W/L
                        p1[opdict['kill']] - p0[opdict['kill']], # K
                        p1[opdict['death']] - p0[opdict['death']], # D
                        '{:.3f}'.format((p1[opdict['kill']] - p0[opdict['kill']])/max(1,p1[opdict['death']] - p0[opdict['death']])), # K/D
                        '{:.2%}'.format((number_of_round - (p1[opdict['death']] - p0[opdict['death']]))/number_of_round), # Survival
                        time_to_string(p1[opdict['played']] - p0[opdict['played']]), # Time played
                        ])
                    prevop = op
                
                if printStats:
                    print('\nOperator In-Between Stats')
                    pretty_print(opd_table)
                return opd_table

                # TODO: Operator Cumulative Progress
                # Idea: Find operator whose stats has changed, add them to columns, and print changes?
                

    '''
    Prints a list of fields for analysis: ID, Date, Map, Players, Result, Notes
    '''
    def get_team_summary(self, names):
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
                stats.record_id = (SELECT MAX(record_id) FROM stats as s2 WHERE s2.player_id = players.id) AND players.id = stats.player_id
            ORDER BY stats.skill_mean DESC
        '''
        self.cursor.execute(sqcmd)
        allplayers = self.cursor.fetchall()
        comp_table = [['Player', '# Games', 'Total Time Played', 'K', 'D', 'K/D', 'HS', 'HPK', 'W', 'L', 'W/L', 'Rank', 'Max Rank', 'MMR',  'Max MMR', 'Skill', 'Skill Std']]
        
        for p in allplayers:
            #total_time = datetime.timedelta(seconds=p['time_played'])
            #print(datetime.timedelta.(total_time))
            #total_time = '{} hours {} minutes'.format(divmod(p['time_played'],3600)[0],divmod(p['time_played'],60)[1])
            total_time = time_to_string(p['time_played'])
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
    Return the region info for a given user id
    '''
    def find_region(self, id):
        max_games = 0
        region = 'ncsa'
        for i in REGIONS:
            r_dict = self.u.get_rank(id, i[1])
            region_games = r_dict['wins'] + r_dict['losses']
            if region_games > max_games:
                region = i[1]
                max_games = region_games
        return region


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
                self.cursor.execute(sqcmd)
                seasons = self.cursor.fetchall()
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

    def update_names(self):
        change = False
        players = self.get_all_players()
        for player in players:
            info = self.u.get_player_by_id(player['uplay_id'])
            if info is None:
                print('Cannot get user information for ID {}'.format(player['uplay_id']))
                continue
            newname = info['nameOnPlatform']
            oldname = player['name']
            try:
                if newname != oldname:
                    change = True
                    sqcmd = '''UPDATE players SET name = '{}' WHERE uplay_id = '{}';'''.format(newname, player['uplay_id'])
                    print('Changing names: {} -> {}'.format(oldname, newname))
                    self.cursor.execute(sqcmd)
                    self.db.commit()
            except Exception as e:
                print('An error occured: {}'.format(e))
        return change

    def get_db_version(self):
        self.cursor.execute('SELECT * FROM dbinfo WHERE tag="version"')
        res = self.cursor.fetchone()
        return res['value']

    def save_season_stats(self):
        players = self.get_all_players()
        #print('WARNING: Ubi has a problem listing seasons before Velvet Shell (5)')
        # Get current season stats to find out max number of seasons to be pulled
        res = self.u.get_rank(id=players[0]['uplay_id'], region=players[0]['region'])
        current_season = res['season']
        np = len(players)
        for pno, player in enumerate(players):
            print('Getting season stats of {} ({}/{})'.format(player['name'], pno+1, np))
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
        tables = ['dbinfo', 'players', 'records', 'stats', 'seasons', 'op_stats', 'gun_stats']
        for t in tables:
            print(t)
            self.cursor.execute('SELECT * FROM {};'.format(t))
            rows = self.cursor.fetchall()
            for row in rows:
                print(list(row))

    '''
    Peek stats of teams
    '''
    def peek_stats(self, players, teams=[], op_stats=True):
        if not teams:
            teams = [1] * len(players)
        ptable = [['Player', 'Team', 'MMR', 'Std', 'Rank', 'Season-W', 'Season-L', 'Atk', 'WL', 'KD', 'Def', 'WL', 'KD']]
        tsums = []
        for team in [1, 2]:
            team_total = 0
            for i in range(len(players)):
                if teams[i] == team:
                    try:
                        uid = self.u.get_player_by_name(players[i])
                        if uid is None:
                            continue
                    except:
                        continue
                    res = self.u.get_rank(id=uid)
                    mmr = res['mmr']
                    std = res['skill_stdev']
                    rank = RANKS[int(res['rank'])]
                    wins = res['wins']
                    losses = res['losses']
                    if op_stats:
                        ops = self.u.get_operator_stats(ids=[uid])
                        #import pprint
                        #pprint.pprint(ops)
                        # Attackers
                        for side in ['atk', 'def']:
                            thelist = [None, 0, 0, 0]
                            for j in SORTED_OPERATOR_LIST:
                                if j[3] == side:
                                    try:
                                        tp = ops[0]['operatorpvp_timeplayed:' + j[0] + ':infinite']
                                    except:
                                        tp = 0
                                    try:
                                        wl = ops[0]['operatorpvp_roundwon:' + j[0] + ':infinite'] / max(ops[0]['operatorpvp_roundlost:' + j[0] + ':infinite'], 1)
                                    except:
                                        wl = 0
                                    try:
                                        kd = ops[0]['operatorpvp_kills:' + j[0] + ':infinite'] / max(ops[0]['operatorpvp_death:' + j[0] + ':infinite'], 1)
                                    except:
                                        kd = 0
                                    if tp >= thelist[1]:
                                        thelist = [j[1], tp, wl, kd]
                            if side == 'atk':
                                atk_op = thelist
                            else:
                                def_op = thelist
                        #freq_atk = max()
                        #import pprint
                        #pprint.pprint(ops)
                        oprow = [atk_op[0], '{:.2f}'.format(atk_op[2]), '{:.2f}'.format(atk_op[3]), def_op[0], '{:.2f}'.format(def_op[2]), '{:.2f}'.format(def_op[3])]
                    else:
                        oprow = ['-', 0, 0, '-', 0, 0]
                    #print('{}: {:.3f} (stdev: {:.3f})'.format(
                    #    players[i], mmr, std))
                    crow = [players[i], team, mmr, std, rank, wins, losses]
                    crow.extend(oprow)

                    ptable.append(crow)
                    team_total += mmr
            tsums.append(['(Team {} Total)'.format(team), team, team_total, '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'])
        print('Copy-row')
        print([i[2] for i in ptable[1:]] + [i[3] for i in ptable[1:]]) 
        ptable.append(['---']*13)
        pretty_print(ptable + tsums)

    '''
    Prints all logs to csv files (daily.csv and pings.csv)
    '''
    def export_to_csv(self, filename='export.csv', verbose=True):
        if verbose:
            print('CSV data:')
        sqcmd = '''SELECT players.name,
                          records.dt,
                          stats.*,
                          gun_stats.*,
                          op_stats.*
                   FROM   players, 
                          records,
                          stats,
                          op_stats,
                          gun_stats
                   WHERE players.id = stats.player_id AND records.id = stats.record_id AND 
                         players.id = gun_stats.player_id AND records.id = gun_stats.record_id AND
                         players.id = op_stats.player_id AND records.id = op_stats.record_id;
                '''
        self.cursor.execute(sqcmd)
        rows = self.cursor.fetchall()
        csvdata = [','.join(d[0] for d in self.cursor.description)]
        for row in rows:
            csvdata.append(','.join([str(i) for i in list(row)]))
        csvfile = open(filename, 'w')
        for r in csvdata:
            csvfile.write(r + '\n')
            if verbose:
                print(r)
        csvfile.close()

    '''
    Imports other records from an existing db file
    '''
    def import_from_db(self, fileaddress):
        print('NOT IMPLEMENTED')
        return None
        # Step 1 - Check version, if version mismatch, update it
        newdb = sqlite3.connect(fileaddress, check_same_thread=False)
        newdb.row_factory = sqlite3.Row
        newcursor = newdb.cursor()
        
        # Step 1b - Create a copy of db file named (rainbow_backup.db)
        self.export_to_db('rainbow_backup.db')
        
        if True:
            # Attach DB
            self.cursor.execute('ATTACH DATABASE "{}" as imported'.format(fileaddress))
            self.db.commit()
            
            # Step 1c - Clean empty ids from stats, op_stats, gun_stats for BOTH tables
            print('''
                DELETE FROM imported.stats i
                WHERE NOT EXISTS (SELECT i.player_id FROM imported.players p WHERE p.id=i.player_id);
            ''')
            
            self.cursor.execute('''
                DELETE FROM imported.stats i
                WHERE NOT EXISTS (SELECT i.player_id FROM imported.players p WHERE p.id=i.player_id);
            ''')
            
            
            # Step 2 - Add players to players table one by one, keep both old and new ID numbers
            
            self.cursor.execute('''INSERT INTO players
                SELECT NULL, np.name, np.uplay_id, np.region
                FROM imported.players np
                WHERE NOT EXISTS(SELECT * FROM players op WHERE op.uplay_id=np.uplay_id);
                ''')
            self.cursor.execute('''
                CREATE TABLE _playerfix AS
                SELECT i.id as imported_id, c.id as current_id
                FROM imported.players i, players c
                WHERE i.uplay_id = c.uplay_id;
                ''')
            self.db.commit()
            
            # Step 3 - Replace player_id numbers in gun_stats, op_stats, stats
            self.cursor.execute('''
                UPDATE imported.stats
                SET player_id=c.current_id
                FROM _playerfix as c
                WHERE player_id=c.imported_id
                ''')
            self.db.execute()
            
            # Step 4 - Find where each record would fit after merge, find ID numbers
            
            # Step 4a - Replace all existing record_ids with new ones starting with largest entries
            
            # Step 4b - Replace all new record_ids with new ones starting with largest entries in gun_stats, op_stats, new_stats
            
            # Step 4c - Add all records to records table one by one, keep both old and new ID numbers
            
            # Step 5 - Replace record_id in gun_stats, op_stats, stats
            
            # Step 6 - Add all entries in stats file to stats
            
            # Step 7 - Add all entries in gun_stats to gun_stats
            
            # Step 8 - Add all entries in op_stats to op_stats
            
            # Step 9 - Sort stats, gun_stats, op_stats by record_id ASC and player_id ASC
            
            # Completed!
        
        #except Exception as e:
        #    # If something goes wrong, replace current file with rainbow_backup
        #    print('An error has occured, reinstating using backup file.', e)
        
        return True
        

    '''
    Copies the db into another db file
    '''
    def export_to_db(self, filename='rainbow_copy.db'):
        copyfile('rainbow.db', filename)

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
        sqcmd = 'SELECT {} FROM stats, players WHERE stats.player_id = players.id AND players.name = "{}" ORDER BY stats.record_id DESC LIMIT 1;'.format(info, name)
        self.cursor.execute(sqcmd)
        rows = self.cursor.fetchall()
        if len(rows) == 0:
            return None
        else:
            return rows[0][info]

    '''
    Runs custom queries
    '''
    def custom_query(self, sqcmd):
        u = self.u
        self.cursor.execute(sqcmd)
        rows = self.cursor.fetchall()
        if len(rows) == 0:
            return None
        else:
            return rows

    def time_diff(self, start, end):
        try:
            mask = '%Y-%m-%d %H:%M:%S.%f'
            st = datetime.datetime.strptime(start, mask)
            en = datetime.datetime.strptime(end, mask)
        except:
            pass
        try:
            mask = '%Y-%m-%d %H:%M:%S'
            st = datetime.datetime.strptime(start, mask)
            en = datetime.datetime.strptime(end, mask)
        except:
            pass
        try:
            mask = '%Y-%m-%d %H:%M'
            st = datetime.datetime.strptime(start, mask)
            en = datetime.datetime.strptime(end, mask)
        except:
            pass
        try:
            mask = '%Y-%m-%d'
            st = datetime.datetime.strptime(start, mask)
            en = datetime.datetime.strptime(end, mask)
        except:
            pass
        return en-st

def pretty_print(table):
    c_sizes = [max(len(str(table[i][c])) for i in range(len(table)))  for c in range(len(table[0]))]
    c_sizes = '}  {:>'.join(str(i) for i in c_sizes)
    mask = '{:>' + c_sizes + '}'
    for row in table:
        str_row = [str(v) for v in row]
        print(mask.format(*str_row))

def time_to_string(tm):
    m, s = divmod(tm, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return '{} hours {} minutes'.format(h, m)
    else:
        return '{} minutes'.format(m)
