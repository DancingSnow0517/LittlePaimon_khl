import json

from utils import requests
from utils.auth_util import get_headers, get_use_cookie, check_retcode


async def get_abyss_data(user_id: str, uid: str, schedule_type='1'):
    server_id = "cn_qd01" if uid[0] == '5' else "cn_gf01"
    url = "https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/spiralAbyss"
    params = {
        "schedule_type": schedule_type,
        "role_id":       uid,
        "server":        server_id
    }

    cookie = get_use_cookie(user_id, uid=uid, action='查询深渊')
    if cookie is None:
        return '现在派蒙没有可以用的cookie哦，可能是:\n1.公共cookie全都达到了每日30次上限\n2.公共池全都失效了或没有cookie\n让管理员使用 添加公共ck 吧!'
    headers = get_headers(q=f'role_id={uid}&schedule_type={schedule_type}&server={server_id}',
                          cookie=cookie)

    resp = await requests.get(url=url, headers=headers, params=params)
    data = json.loads(resp)
    print(data)
    check = check_retcode(data)
    if check:
        return data
    else:
        return None


