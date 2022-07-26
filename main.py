import asyncio
import hashlib
import logging
import os.path
import sys
from pathlib import Path

from khl import Bot

from utils.config import Config
from paimon_chat import paimon_chat
from guess_voice import guess_voice
from paimon_gacha import paimon_gacha
from paimon_cloud_genshin import paimon_cloud_genshin
from utils.files import load_json, download

resource_list = load_json(path=Path(__file__).parent / 'resources' / 'resource_list.json')
resource_path = Path().cwd() / 'resources' / 'LittlePaimon'

log = logging.getLogger(__name__)


class LittlePaimonBot(Bot):

    def __init__(self):
        self.config = Config.load()
        super().__init__(self.config.token)
        logging.basicConfig(level=self.config.log_level,
                            format='[%(asctime)s] [%(module)s] [%(threadName)s/%(levelname)s]: %(message)s')

    async def start(self):
        # 检查数据文件夹是否存在
        if not os.path.exists(self.config.data_path):
            os.mkdir(self.config.data_path)
        elif not os.path.isdir(self.config.data_path):
            raise Exception(f'{self.config.data_path} 不是一个文件夹')
        await self.on_startup()
        await super().start()

    async def on_startup(self):
        await download_resources()

        await paimon_chat.on_startup(self)
        await guess_voice.on_startup(self)
        await paimon_gacha.on_startup(self)
        await paimon_cloud_genshin.on_startup(self)


async def download_resources():
    log.info('正在检查资源完整性......')
    for resource in resource_list:
        res_path = resource_path / resource['path'].replace('LittlePaimon/', '')
        download_url = 'http://genshin.cherishmoon.fun/res/' + resource['path'].replace('LittlePaimon/', '')
        if res_path.exists():
            if hashlib.md5(res_path.read_bytes()).hexdigest() == resource['hash'] or not resource['lock']:
                continue
            else:
                res_path.unlink()
        try:
            await download(download_url, res_path)
            await asyncio.sleep(0.3)
        except Exception as e:
            log.warning(resource['path'].split('/')[-1] + 'download failed: ' + str(e))


def main():
    bot = LittlePaimonBot()
    bot.run()
    ...


if __name__ == '__main__':
    sys.exit(main())
