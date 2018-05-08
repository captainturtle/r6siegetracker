
ubi_app_id = '39baebad-39e5-4552-8c25-2c9b919064e2'

LOGIN_URL = 'https://uplayconnect.ubi.com/ubiservices/v2/profiles/sessions'
HEADERS = {
    'Ubi-AppId': ubi_app_id,
    'Content-Type': 'application/json; charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
    'Ubi-LocaleCode': 'en-US',
    'Referer': 'https://overlay.ubisoft.com/?owner=https://rainbow6.ubisoft.com',
    'Origin': 'https://game-rainbow6.ubi.com',
    'Access-Control-Request-Headers': 'authorization,ubi-appid,ubi-sessionid',
    'Accept-Language': 'en-US,en;q=0.9'
    }

PLAYER_URL = 'https://public-ubiservices.ubi.com/v2/profiles?platformType=uplay&{key}={val}'
STATS_URL = 'https://public-ubiservices.ubi.com/v1/spaces/5172a557-50b5-4665-b7db-e3f2e8c5041d/sandboxes/OSBOR_PC_LNCH_A/playerstats2/statistics?populations={id}&' +\
            'statistics=rankedpvp_kills,rankedpvp_death,rankedpvp_matchwon,rankedpvp_matchlost,casualpvp_kills,casualpvp_death,casualpvp_matchwon,casualpvp_matchlost'
PROFILE_PIC = 'https://ubisoft-avatars.akamaized.net/{id}/default_146_146.png?appId=39baebad-39e5-4552-8c25-2c9b919064e2'
