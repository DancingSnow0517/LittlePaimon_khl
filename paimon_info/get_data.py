import json

from littlepaimon_utils import aiorequests

from utils import requests
from utils.auth_util import get_headers, get_use_cookie, check_retcode, get_own_cookie, get_sign_headers


async def get_abyss_data(user_id: str, uid: str, schedule_type='1'):
    server_id = "cn_qd01" if uid[0] == '5' else "cn_gf01"
    url = "https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/spiralAbyss"
    params = {
        "schedule_type": schedule_type,
        "role_id": uid,
        "server": server_id
    }

    cookie = get_use_cookie(user_id, uid=uid, action='查询深渊')
    if cookie is None:
        return '现在派蒙没有可以用的cookie哦，可能是:\n1.公共cookie全都达到了每日30次上限\n2.公共池全都失效了或没有cookie\n让管理员使用 添加公共ck 吧!'
    headers = get_headers(q=f'role_id={uid}&schedule_type={schedule_type}&server={server_id}',
                          cookie=cookie)

    resp = await requests.get(url=url, headers=headers, params=params)
    data = json.loads(resp)
    if check_retcode(data):
        return data
    else:
        return None


async def get_daily_note_data(user_id, uid):
    server_id = "cn_qd01" if uid[0] == '5' else "cn_gf01"
    url = "https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/dailyNote"
    cookie = get_own_cookie(user_id, uid, action='查询实时便签')
    if cookie is None:
        return f'你的uid{uid}没有绑定对应的cookie,使用ysb绑定才能用实时便签哦!或这个不是你的账户'
    headers = get_headers(q=f'role_id={uid}&server={server_id}', cookie=cookie)
    params = {
        "server": server_id,
        "role_id": uid
    }
    resp = await aiorequests.get(url=url, headers=headers, params=params)
    data = resp.json()
    if check_retcode(data):
        return data
    else:
        return f'你的uid{uid}的cookie已过期,需要重新绑定哦!'


async def get_monthinfo_data(user_id, uid, month):
    server_id = "cn_qd01" if uid[0] == '5' else "cn_gf01"
    url = 'https://hk4e-api.mihoyo.com/event/ys_ledger/monthInfo'
    cookie = get_own_cookie(user_id, uid, action='查询每月札记')
    if not cookie:
        return f'你的uid{uid}没有绑定对应的cookie,使用ysb绑定才能用每月札记哦!'
    headers = get_headers(q=f'month={month}&bind_uid={uid}&bind_region={server_id}', cookie=cookie)
    params = {
        "month": int(month),
        "bind_uid": uid,
        "bind_region": server_id
    }
    resp = await aiorequests.get(url=url, headers=headers, params=params)
    data = resp.json()
    if check_retcode(data):
        return data
    else:
        return f'你的uid{uid}的cookie已过期,需要重新绑定哦!'


async def get_player_card_data(user_id, uid):
    server_id = "cn_qd01" if uid[0] == '5' else "cn_gf01"
    url = "https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/index"
    params = {
        "server": server_id,
        "role_id": uid
    }
    while True:
        cookie = get_use_cookie(user_id, uid=uid, action='查询原神卡片')
        if not cookie:
            return '现在派蒙没有可以用的cookie哦，可能是:\n1.公共cookie全都达到了每日30次上限\n2.公共池全都失效了或没有cookie\n让管理员使用 添加公共ck 吧!'
        headers = get_headers(q=f'role_id={uid}&server={server_id}', cookie=cookie)
        resp = await aiorequests.get(url=url, headers=headers, params=params)
        data = resp.json()
        if check_retcode(data):
            return data
        else:
            return None


async def get_chara_detail_data(user_id, uid):
    server_id = "cn_qd01" if uid[0] == '5' else "cn_gf01"
    json_data = {
        "server": server_id,
        "role_id": uid,
        "character_ids": []
    }
    url = 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/character'
    while True:
        cookie = get_use_cookie(user_id, uid=uid, action='查询角色详情')
        if not cookie:
            return '现在派蒙没有可以用的cookie哦，可能是:\n1.公共cookie全都达到了每日30次上限\n2.公共池全都失效了或没有cookie\n让管理员使用 添加公共ck 吧!'
        headers = get_headers(b=json_data, cookie=cookie)
        resp = await aiorequests.post(url=url, headers=headers, json=json_data)
        data = resp.json()
        if check_retcode(data):
            return data
        else:
            return None


async def get_sign_list():
    url = 'https://api-takumi.mihoyo.com/event/bbs_sign_reward/home'
    headers = {
        'x-rpc-app_version': '2.11.1',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                      'KHTML, like Gecko) miHoYoBBS/2.11.1',
        'x-rpc-client_type': '5',
        'Referer': 'https://webstatic.mihoyo.com/'
    }
    params = {
        'act_id': 'e202009291139501'
    }
    resp = await aiorequests.get(url=url, headers=headers, params=params)
    data = resp.json()
    return data


async def get_sign_info(user_id, uid):
    server_id = "cn_qd01" if uid[0] == '5' else "cn_gf01"
    url = 'https://api-takumi.mihoyo.com/event/bbs_sign_reward/info'
    cookie = get_own_cookie(user_id, uid, action='查询米游社签到')
    if not cookie:
        return f'你的uid{uid}没有绑定对应的cookie,使用ysb绑定才能用米游社签到哦!'
    headers = {
        'x-rpc-app_version': '2.11.1',
        'x-rpc-client_type': '5',
        'Origin': 'https://webstatic.mihoyo.com',
        'Referer': 'https://webstatic.mihoyo.com/',
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS '
                      'X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
    }
    params = {
        'act_id': 'e202009291139501',
        'region': server_id,
        'uid': uid
    }
    resp = await aiorequests.get(url=url, headers=headers, params=params)
    data = resp.json()
    if check_retcode(data):
        return data
    else:
        return f'你的uid{uid}的cookie已过期,需要重新绑定哦!'


async def sign(user_id, uid):
    server_id = "cn_qd01" if uid[0] == '5' else "cn_gf01"
    url = 'https://api-takumi.mihoyo.com/event/bbs_sign_reward/sign'
    cookie = get_own_cookie(user_id, uid, action='米游社签到')
    if not cookie:
        return f'你的uid{uid}没有绑定对应的cookie,使用ysb绑定才能用米游社签到哦!'
    headers = get_sign_headers(cookie)
    json_data = {
        'act_id': 'e202009291139501',
        'uid': uid,
        'region': server_id
    }
    resp = await aiorequests.post(url=url, headers=headers, json=json_data)
    try:
        data = resp.json()
    except:
        return resp.read()
    if check_retcode(data):
        return data
    else:
        return f'你的uid{uid}的cookie已过期,需要重新绑定哦!'
