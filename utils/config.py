import os.path
from typing import List, Dict

from ruamel import yaml


class Config:
    token: str = ''
    log_level: str = 'INFO'
    data_path: str = 'data'

    def __init__(self, **data) -> None:
        self.log_level = data.get('log_level')
        self.token = data.get('token', '')
        self.data_path = data.get('data_path', 'data')

    @classmethod
    def load(cls) -> 'Config':
        if not os.path.exists('config.yml'):
            with open('resources/default_config.yml', 'rb') as df:
                with open('config.yml', 'wb') as f:
                    f.write(df.read())
        with open('config.yml', 'r', encoding='utf-8') as f:
            data = yaml.round_trip_load(f)
        return cls(**data)


class CookieInfo:
    owner: str = ''
    guild: str = ''
    cookie: str = ''

    def __init__(self, owner: str, guild: str, cookie: str) -> None:
        self.owner = owner
        self.guild = guild
        self.cookie = cookie

    def to_data(self):
        return {
            'owner': self.owner,
            'guild': self.guild,
            'cookie': self.cookie
        }


class CookieData:
    public_cookies: List[str] = []
    cookies: Dict[str, CookieInfo] = {}
    cookies_statu: Dict[str, bool] = {}

    def __init__(self, **data) -> None:
        self.public_cookies = data.get('public_cookies', [])
        self.cookies_statu = data.get('cookies_statu', {})
        self.cookies = {}
        data = data.get('cookies', {})
        for uid in data:
            self.cookies[uid] = CookieInfo(owner=data[uid]['owner'], guild=data[uid]['guild'],
                                           cookie=data[uid]['cookie'])

    def save(self):
        cookie_info = {}
        for uid in self.cookies:
            cookie_info[uid] = {'owner': self.cookies[uid].owner, 'guild': self.cookies[uid].guild,
                                'cookie': self.cookies[uid].cookie}
        data = {
            'public_cookies': self.public_cookies,
            'cookies': cookie_info,
            'cookies_statu': self.cookies_statu
        }
        with open('cookies.yml', 'w', encoding='utf-8') as f:
            yaml.round_trip_dump(data, f)

    @classmethod
    def load(cls) -> 'CookieData':
        if not os.path.exists('cookies.yml'):
            data = {
                'public_cookies': [],
                'cookies': {},
                'cookies_statu': {}
            }
            with open('cookies.yml', 'w', encoding='utf-8') as f:
                yaml.round_trip_dump(data, f)
                return cls(public_cookies=[], cookies={})
        else:
            with open('cookies.yml', 'r', encoding='utf-8') as f:
                data = yaml.round_trip_load(f)
            return cls(**data)

    def get_public_cookies(self):
        return self.public_cookies

    def get_user_cookies(self, user_id: str) -> dict[str, CookieInfo]:
        ret = {}
        for i in self.cookies:
            if self.cookies[i].owner == user_id:
                ret[i] = self.cookies[i]
        return ret

    def get_guild_cookies(self, guild_id: str):
        ret = {}
        for i in self.cookies:
            if self.cookies[i].guild == guild_id:
                ret[i] = self.cookies[i]
        return ret

    def get_cookie_by_uid(self, uid: str) -> CookieInfo:
        return self.cookies[uid] if uid in self.cookies else None

    def is_cookie_can_use(self, cookie: str) -> bool:
        return self.cookies_statu[cookie]

    def set_cookie_statu(self, cookie: str, statu: bool):
        self.cookies_statu[cookie] = statu
        self.save()

    def add_public_cookie(self, cookie: str):
        self.public_cookies.append(cookie)
        self.cookies_statu[cookie] = True
        self.save()

    def add_private_cookie(self, uid, guild_id: str, user_id: str, cookie: str):
        self.cookies[uid] = CookieInfo(owner=user_id, guild=guild_id, cookie=cookie)
        self.cookies_statu[cookie] = True
        self.save()

    def delete_user_cookies(self, user_id: str):
        for uid in list(self.cookies.keys()):
            if self.cookies[uid].owner == user_id:
                del self.cookies_statu[self.cookies[uid].cookie]
                del self.cookies[uid]
        self.save()


class STokenInfo:
    uid: str
    mys_id: str
    cookie: str
    stoken: str

    def __init__(self, uid, mys_id, cookie, stoken) -> None:
        self.uid = uid
        self.mys_id = mys_id
        self.cookie = cookie
        self.stoken = stoken


class STokenData:
    stoken: Dict[str, STokenInfo] = {}

    def __init__(self, **data) -> None:
        stoken = data.get('stoken', {})
        self.stoken = {}
        for user_id in stoken:
            self.stoken[user_id] = STokenInfo(stoken[user_id]['uid'], stoken[user_id]['mys_id'], stoken[user_id]['cookie'], stoken[user_id]['stoken'])

    def save(self):
        stoken = {}
        for user_id in self.stoken:
            stoken[user_id] = {
                'uid': self.stoken[user_id].uid,
                'mys_id': self.stoken[user_id].mys_id,
                'cookie': self.stoken[user_id].cookie,
                'stoken': self.stoken[user_id].stoken
            }
        data = {'stoken': stoken}
        with open('stoken.yml', 'w', encoding='utf-8') as f:
            yaml.round_trip_dump(data, f)

    @classmethod
    def load(cls):
        if not os.path.exists('stoken.yml'):
            data = {
                'stoken': {}
            }
            with open('stoken.yml', 'w', encoding='utf-8') as f:
                yaml.round_trip_dump(data, f)
            return cls(stoken={})
        else:
            with open('stoken.yml', 'r', encoding='utf-8') as f:
                data = yaml.round_trip_load(f)
            return cls(**data)

    def add_private_stoken(self, user_id, uid, mys_id, cookie, stoken):
        self.stoken[user_id] = STokenInfo(uid, mys_id, cookie, stoken)
        self.save()

    def get_private_stoken(self, user_id):
        return self.stoken[user_id] if user_id in self.stoken else None


cookie_data = CookieData.load()
stoken_data = STokenData.load()
