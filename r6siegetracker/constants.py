# App constants
DB_VERSION = 9


# Constant fields
UBI_APP_ID = '39baebad-39e5-4552-8c25-2c9b919064e2'
GUN_LIST = [(1, 'ar', 'Assault Rifle', 'AR'),
            (2, 'smg', 'Submachine Gun', 'SMG'),
            (3, 'lmg', 'Light Machine Gun', 'LMG'),
            (4, 'marksman', 'Marksman Rifle', 'MR'),
            (5, 'handgun', 'Handgun', 'HG'),
            (6, 'shotgun', 'Shotgun', 'SH'),
            (7, 'mp', 'Machine Pistol', 'MP')]
GUN_STAT_LIST = [
    ('weapontypepvp_bulletfired', '{} Fired', 'fired'),
    ('weapontypepvp_bullethit', '{} Hit', 'hit'),
    ('weapontypepvp_kills', '{} Kills', 'kill'),
    ('weapontypepvp_headshot', '{} Headshots', 'headshot'),
    ]
OPERATOR_LIST = [
    ('2:1', 'Smoke', 'smoke', 'def'),
    ('2:2', 'Castle', 'castle', 'def'),
    ('2:3', 'Doc', 'doc', 'def'),
    ('2:4', 'Glaz', 'glaz', 'atk'),
    ('2:5', 'Blitz', 'blitz', 'atk'),
    ('2:6', 'Buck', 'buck', 'atk'),
    ('2:7', 'Blackbeard', 'bb', 'atk'),
    ('2:8', 'Capitao', 'capitao', 'atk'),
    ('2:9', 'Hibana', 'hibana', 'atk'),
    ('2:10', 'Maverick', 'maverick', 'atk'),
    ('2:11', 'Nomad', 'nomad', 'atk'),
    ('2:A', 'Jackal', 'jackal', 'atk'),
    ('2:B', 'Ying', 'ying', 'atk'),
    ('2:C', 'Ela', 'ela', 'def'),
    ('2:D', 'Dokkaebi', 'dokkaebi', 'atk'),
    ('2:F', 'Maestro', 'maestro', 'def'),
    ('3:1', 'Mute', 'mute', 'def'),
    ('3:2', 'Ash', 'ash', 'atk'),
    ('3:3', 'Rook', 'rook', 'def'),
    ('3:4', 'Fuze', 'fuze', 'atk'),
    ('3:5', 'IQ', 'iq', 'atk'),
    ('3:6', 'Frost', 'frost', 'def'),
    ('3:7', 'Valkyrie', 'valkyrie', 'def'),
    ('3:8', 'Caveira', 'cav', 'def'),
    ('3:9', 'Echo', 'echo', 'def'),
    ('3:10', 'Clash', 'clash', 'def'),
    ('3:11', 'Kaid', 'kaid', 'def'),
    ('3:A', 'Mira', 'mira', 'def'),
    ('3:B', 'Lesion', 'lesion', 'def'),
    ('3:C', 'Zofia', 'zofia', 'atk'),
    ('3:D', 'Vigil', 'vigil', 'def'),
    ('3:E', 'Lion', 'lion', 'atk'),
    ('3:F', 'Alibi', 'alibi', 'def'),
    ('4:1', 'Sledge', 'sledge', 'atk'),
    ('4:2', 'Pulse', 'pulse', 'def'),
    ('4:3', 'Twitch', 'twitch', 'atk'),
    ('4:4', 'Kapkan', 'kapkan', 'def'),
    ('4:5', 'Jager', 'jager', 'def'),
    ('4:E', 'Finka', 'finka', 'atk'),
    ('5:1', 'Thatcher', 'thatcher', 'atk'),
    ('5:2', 'Thermite', 'thermite', 'atk'),
    ('5:3', 'Montagne', 'montagne', 'atk'),
    ('5:4', 'Tachanka', 'tach', 'def'),
    ('5:5', 'Bandit', 'bandit', 'def')
    ]
SORTED_OPERATOR_LIST = sorted(OPERATOR_LIST, key=lambda x: (x[3], x[1]))
OPERATOR_STAT_LIST = [
    ('timeplayed', 'Time Played', 'tp'),
    ('roundwon', 'Round Won', 'rw'),
    ('roundlost', 'Round Lost', 'rl'),
    ('kills', 'Kills', 'k'),
    ('death', 'Deaths', 'd')
    ]
REGIONS = [('America', 'ncsa'),
           ('Europe', 'emea'),
           ('Asia', 'apac')]

# DB fields: [0] JSON name, [1] DB column name, [2] User-friendly column name, [3] API request field name
STAT_LIST = [
    ('generalpvp_matchplayed:infinite', 'match_played', 'Matches Played', 'generalpvp_matchplayed'),
    ('generalpvp_timeplayed:infinite', 'time_played', 'Time Played', 'generalpvp_timeplayed'),
    ('rankedpvp_kills:infinite', 'ranked_kill', 'Ranked Kills', 'rankedpvp_kills'),
    ('rankedpvp_death:infinite', 'ranked_death', 'Ranked Deaths', 'rankedpvp_death'),
    ('rankedpvp_matchwon:infinite', 'ranked_won', 'Ranked Won', 'rankedpvp_matchwon'),
    ('rankedpvp_matchlost:infinite', 'ranked_lost', 'Ranked Lost', 'rankedpvp_matchlost'),
    ('casualpvp_kills:infinite', 'casual_kill', 'Casual Kills', 'casualpvp_kills'),
    ('casualpvp_death:infinite', 'casual_death', 'Casual Deaths', 'casualpvp_death'),
    ('casualpvp_matchwon:infinite', 'casual_won', 'Casual Won', 'casualpvp_matchwon'),
    ('casualpvp_matchlost:infinite', 'casual_lost', 'Casual Lost', 'casualpvp_matchlost'),
    ('generalpvp_killassists:infinite', 'assists', 'Assists', 'generalpvp_killassists'),
    ('generalpvp_headshot:infinite', 'headshots', 'Headshots', 'generalpvp_headshot')
    ]
GUN_COLUMN_LIST = [('{}:{}:infinite'.format(s[0], g[0]), '{}_{}'.format(s[2], g[1]), s[1].format(g[3]), s[0]) for g in GUN_LIST for s in GUN_STAT_LIST]
PROGRESS_LIST = [
    ('mmr', 'mmr', 'MMR'),
    ('max_mmr', 'max_mmr', 'Max MMR'),
    ('skill_mean', 'skill_mean', 'Skill Mean'),
    ('skill_stdev', 'skill_std', 'Skill St.Dev'),
    ('rank', 'rank', 'Rank'),
    ('max_rank', 'max_rank', 'Max.Rank'),
    ('wins', 'season_wins', 'Season Wins'),
    ('losses', 'season_losses', 'Season Losses')
    ]
OPERATOR_COLUMN_LIST = [('operatorpvp_{}:{}:infinite'.format(s[0], o[0]), '{} {}'.format(o[1], s[1])  , o[2] + '_' + s[2]) for o in OPERATOR_LIST for s in OPERATOR_STAT_LIST]

# Entry points
LOGIN_URL = 'https://uplayconnect.ubi.com/ubiservices/v2/profiles/sessions'
PLAYER_URL = 'https://public-ubiservices.ubi.com/v2/profiles?platformType=uplay&{key}={val}'
STATS_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/playerstats2/statistics?populations={ids}&' +\
            'statistics='+','.join(set(s[3] for s in STAT_LIST))
PROFILE_PIC = 'https://ubisoft-avatars.akamaized.net/{id}/default_146_146.png?appId=39baebad-39e5-4552-8c25-2c9b919064e2'
PROGRESS_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/r6karma/players?board_id=pvp_ranked&region_id={region}&profile_ids={id}&season_id={season}'
GAME_PLAYERD_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/playerstats2/statistics?populations={ids}&statistics=generalpvp_matchplayed'
OPERATOR_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/playerstats2/statistics?populations={ids}&statistics=operatorpvp_timeplayed,operatorpvp_roundwon,operatorpvp_roundlost,operatorpvp_kills,operatorpvp_death'
GUN_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/playerstats2/statistics?populations={ids}&' +\
          'statistics='+','.join(set(s[3] for s in GUN_COLUMN_LIST))
PROFILE_URL = 'https://public-ubiservices.ubi.com/v2/users/{}/profiles'

RANKS = [
    'Unranked',
    'Copper IV',
    'Copper III',
    'Copper II',
    'Copper I',
    'Bronze IV',
    'Bronze III',
    'Bronze II',
    'Bronze I',
    'Silver IV',
    'Silver III',
    'Silver II',
    'Silver I',
    'Gold IV',
    'Gold III',
    'Gold II',
    'Gold I',
    'Platinum III',
    'Platinum II',
    'Platinum I',
    'Diamond'
    ]

SEASONS = [
    '',
    'BLACK ICE',
    'DUST LINE',
    'SKULL RAIN',
    'RED CROW',
    'VELVET SHELL',
    'HEALTH',
    'BLOOD ORCHID',
    'WHITE NOISE',
    'CHIMERA',
    'PARA BELLUM',
    'GRIM SKY',
    'WIND BASTION'
    ]

MAP_LIST = [
    'Bank',
    'Bartlett',
    'Border',
    'Chalet',
    'Clubhouse',
    'Coastline',
    'Consulate',
    'Favela',
    'Hereford',
    'House',
    'Kafe Dostoyevsky',
    'Kanal',
    'Oregon',
    'Plane',
    'Skyscraper',
    'Theme Park',
    'Tower',
    'Villa',
    'Yacht',
    'Fortress'
    ]
# REFERENCES
# Operator info json object: https://game-rainbow6.ubi.com/assets/data/operators.bbbf29a090.json


