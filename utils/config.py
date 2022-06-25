import os.path

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
