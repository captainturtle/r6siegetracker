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
    ] + [('{}:{}:infinite'.format(s[0], g[0]), '{}_{}'.format(s[2], g[1]), s[1].format(g[3]), s[0]) for g in GUN_LIST for s in GUN_STAT_LIST]
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
REGIONS = [('America', 'ncsa'),
           ('Europe', 'emea'),
           ('Asia', 'apac')]

# Entry points
LOGIN_URL = 'https://uplayconnect.ubi.com/ubiservices/v2/profiles/sessions'
PLAYER_URL = 'https://public-ubiservices.ubi.com/v2/profiles?platformType=uplay&{key}={val}'
STATS_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/playerstats2/statistics?populations={id}&' +\
            'statistics='+','.join(set(s[3] for s in STAT_LIST))
PROFILE_PIC = 'https://ubisoft-avatars.akamaized.net/{id}/default_146_146.png?appId=39baebad-39e5-4552-8c25-2c9b919064e2'
PROGRESS_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/r6karma/players?board_id=pvp_ranked&region_id={region}&profile_ids={id}&season_id=-1'
GAME_PLAYERD_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/playerstats2/statistics?populations={ids}&statistics=generalpvp_matchplayed'

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
