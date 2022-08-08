import hashlib
import json
import logging
import random
import string
from time import time
from typing import Optional

from utils import requests
from utils.config import cookie_data

log = logging.getLogger(__name__)


# md5加密
def md5(text: str) -> str:
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()


# 米游社headers的ds_token，对应版本2.11.1
def get_ds(q="", b=None) -> str:
    if b:
        br = json.dumps(b)
    else:
        br = ""
    s = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    t = str(int(time()))
    r = str(random.randint(100000, 200000))
    c = md5("salt=" + s + "&t=" + t + "&r=" + r + "&b=" + br + "&q=" + q)
    return f"{t},{r},{c}"


def random_hex(length):
    result = hex(random.randint(0, 16 ** length)).replace('0x', '').upper()
    if len(result) < length:
        result = '0' * (length - len(result)) + result
    return result


def get_old_version_ds(mhy_bbs: bool = False) -> str:
    if mhy_bbs:
        s = 'dWCcD2FsOUXEstC5f9xubswZxEeoBOTc'
    else:
        s = 'h8w582wxwgqvahcdkpvdhbh2w9casgfl'
    t = str(int(time()))
    r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c = md5("salt=" + s + "&t=" + t + "&r=" + r)
    return f"{t},{r},{c}"


# 米游社爬虫headers
def get_headers(cookie, q='', b=None):
    headers = {
        'DS': get_ds(q, b),
        'Origin': 'https://webstatic.mihoyo.com',
        'Cookie': cookie,
        'x-rpc-app_version': "2.11.1",
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS '
                      'X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
        'x-rpc-client_type': '5',
        'Referer': 'https://webstatic.mihoyo.com/'
    }
    return headers


def get_sign_headers(cookie):
    headers = {
        'User_Agent': 'Mozilla/5.0 (Linux; Android 10; MIX 2 Build/QKQ1.190825.002; wv) AppleWebKit/537.36 ('
                      'KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36 '
                      'miHoYoBBS/2.3.0',
        'Cookie': cookie,
        'x-rpc-device_id': random_hex(32),
        'Origin': 'https://webstatic.mihoyo.com',
        'X_Requested_With': 'com.mihoyo.hyperion',
        'DS': get_old_version_ds(mhy_bbs=True),
        'x-rpc-client_type': '2',
        'Referer': 'https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?'
                   'bbs_auth_required=true&act_id=e202009291139501&utm_source=bbs&utm_medium=mys&utm_campaign=icon',
        'x-rpc-app_version': '2.28.1'
    }
    return headers


# 检查数据返回状态，10001为ck过期了，10101为达到每日30次上线了
def check_retcode(data) -> bool:
    if data['retcode'] == 10001 or data['retcode'] == -100:
        return False
    elif data['retcode'] == 10101:
        log.info('cookie达到了每日30次查询上限')
        return False
    else:
        return True


# 获取可用的cookie
def get_use_cookie(user_id, uid='', mys_id='', action='') -> Optional[str]:
    public_cookie = cookie_data.get_public_cookies()
    cookies = cookie_data.get_user_cookies(user_id)

    for cookie in public_cookie:
        if cookie_data.is_cookie_can_use(cookie):
            log.info(f'派蒙调用公共的 cookie 来执行 {action} 操作')
            return cookie

    for uid in cookies:
        if cookie_data.is_cookie_can_use(cookies[uid].cookie):
            log.info(f'使用用户 {user_id} 的 cookie 来执行 {action} 操作')
            return cookies[uid].cookie

    return None


def get_own_cookie(user_id, uid, action=''):
    info = cookie_data.get_cookie_by_uid(uid)
    if info is None or (user_id != '-1' and info.owner != user_id):
        return None
    log.info(f'使用用户 {info.owner} 的 cookie 来执行 {action} 操作')
    return info.cookie


# 检查cookie是否有效，通过查看个人主页来判断
async def check_cookie(cookie):
    url = 'https://bbs-api.mihoyo.com/user/wapi/getUserFullInfo?gids=2'
    headers = {
        'DS': get_ds(),
        'Origin': 'https://webstatic.mihoyo.com',
        'Cookie': cookie,
        'x-rpc-app_version': "2.11.1",
        'x-rpc-client_type': '5',
        'Referer': 'https://webstatic.mihoyo.com/'
    }
    res = await requests.get(url=url, headers=headers)
    res = json.loads(res)
    if res['retcode'] != 0:
        return False
    else:
        return True
