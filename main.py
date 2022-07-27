import asyncio
import hashlib
import logging
import os.path
import sys
from pathlib import Path
from typing import List, Dict

from khl import Bot, Message
from khl.command import Rule
from khl_card import Card

from khl_card.accessory import PlainText, _BaseText, Kmarkdown
from khl_card.modules import Section

from utils.api import CommandInfo
from utils.config import Config
from paimon_chat import paimon_chat
from guess_voice import guess_voice
from paimon_gacha import paimon_gacha
from paimon_cloud_genshin import paimon_cloud_genshin
from paimon_info import paimon_info
from utils.files import load_json, download

resource_list = load_json(path=Path(__file__).parent / 'resources' / 'resource_list.json')
resource_path = Path().cwd() / 'resources' / 'LittlePaimon'

log = logging.getLogger(__name__)


class LittlePaimonBot(Bot):
    help_messages: Dict[str, CommandInfo] = {}

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
        await paimon_info.on_startup(self)

    def my_command(self, name: str = '', *, aliases: List[str] = (), usage: _BaseText = PlainText('暂无使用帮助'),
                   introduce: _BaseText = PlainText('暂无命令介绍')):
        self.help_messages[name] = CommandInfo(name=name, aliases=aliases, usage=usage, introduce=introduce)
        return self.command(name=name, aliases=aliases, prefixes=[''], rules=[Rule.is_bot_mentioned(self)])


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

    @bot.my_command(name='help', aliases=['帮助'], introduce=Kmarkdown('显示帮助信息'))
    async def print_help_message(msg: Message, *_):
        bot_id = bot.me.id
        cards = [info.build_card().build() for info in bot.help_messages.values()]
        cards.insert(0, Card(Section(Kmarkdown(f'**小派蒙的命令大全！**\n所有的命令末尾都要 (met){bot_id}(met) 哦！'))).build())
        await msg.reply(cards)

    bot.run()


if __name__ == '__main__':
    sys.exit(main())
