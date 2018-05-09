UBI_APP_ID = '39baebad-39e5-4552-8c25-2c9b919064e2'
LOGIN_URL = 'https://uplayconnect.ubi.com/ubiservices/v2/profiles/sessions'
PLAYER_URL = 'https://public-ubiservices.ubi.com/v2/profiles?platformType=uplay&{key}={val}'
STATS_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/playerstats2/statistics?populations={id}&' +\
            'statistics=rankedpvp_kills,rankedpvp_death,rankedpvp_matchwon,rankedpvp_matchlost,casualpvp_kills,casualpvp_death,casualpvp_matchwon,casualpvp_matchlost'
PROFILE_PIC = 'https://ubisoft-avatars.akamaized.net/{id}/default_146_146.png?appId=39baebad-39e5-4552-8c25-2c9b919064e2'
STAT_LIST = [
    ('rankedpvp_kills:infinite', 'ranked_kill', 'Ranked Kills'),
    ('rankedpvp_death:infinite', 'ranked_death', 'Ranked Deaths'),
    ('rankedpvp_matchwon:infinite', 'ranked_won', 'Ranked Won'),
    ('rankedpvp_matchlost:infinite', 'ranked_lost', 'Ranked Lost'),
    ('casualpvp_kills:infinite', 'casual_kill', 'Casual Kills'),
    ('casualpvp_death:infinite', 'casual_death', 'Casual Deaths'),
    ('casualpvp_matchwon:infinite', 'casual_won', 'Casual Won'),
    ('casualpvp_matchlost:infinite', 'casual_lost', 'Casual Lost')
    ]