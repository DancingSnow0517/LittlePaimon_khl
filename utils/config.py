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


class CookieData:
    public_cookies: List[str] = []
    cookies: Dict[str, List[str]] = {}
    cookies_statu: Dict[str, bool] = {}

    def __init__(self, **data) -> None:
        self.public_cookies = data.get('public_cookies', [])
        self.cookies = data.get('cookies', {})
        self.cookies_statu = data.get('cookies_statu', {})

    def save(self):
        data = {
            'public_cookies': self.public_cookies,
            'cookies': self.cookies,
            'cookies_statu': self.cookies_statu
        }
        with open('cookies.yml', 'w', encoding='utf-8') as f:
            yaml.round_trip_dump(data, f)

    @classmethod
    def load(cls) -> 'CookieData':
        if not os.path.exists('cookies.yml'):
            data = {
                'public_cookies': {},
                'cookies': [],
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

    def get_user_cookies(self, user_id: str):
        return self.cookies.get(user_id)

    def is_cookie_can_use(self, cookie: str) -> bool:
        return self.cookies_statu[cookie]

    def set_cookie_statu(self, cookie: str, statu: bool):
        self.cookies_statu[cookie] = statu
        self.save()

    def add_public_cookie(self, cookie: str):
        self.public_cookies.append(cookie)
        self.cookies_statu[cookie] = True
        self.save()

    def add_private_cookie(self, user_id: str, cookie: str):
        if user_id not in self.cookies:
            self.cookies[user_id] = []
        self.cookies[user_id].append(cookie)
        self.cookies_statu[cookie] = True
        self.save()


cookie_data = CookieData.load()
