import asyncio
import hashlib
import logging
import os.path
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union, Pattern

from khl import Bot, Message
from khl.command import Rule
from khl_card import Card
from khl_card.accessory import Kmarkdown
from khl_card.modules import Section, Context
from littlepaimon_utils.aiorequests import post
from littlepaimon_utils.files import load_json, download

from guess_voice import guess_voice
from paimon_calendar import paimon_calendar
from paimon_chat import paimon_chat
from paimon_cloud_genshin import paimon_cloud_genshin
from paimon_gacha import paimon_gacha
from paimon_info import paimon_info
from utils.api import CommandInfo, MyRules
from utils.config import config

resource_list = load_json(path=Path(__file__).parent / 'resources' / 'resource_list.json')
resource_path = Path().cwd() / 'resources' / 'LittlePaimon'

log = logging.getLogger(__name__)

VERSION = '1.0.0'


class LittlePaimonBot(Bot):
    help_messages: Dict[str, CommandInfo] = {}

    def __init__(self):
        self.config = config
        super().__init__(self.config.token)
        logging.basicConfig(level=self.config.log_level,
                            format='[%(asctime)s] [%(module)s] [%(threadName)s/%(levelname)s]: %(message)s')

    def search_command(self, name: str) -> Optional[CommandInfo]:
        if name in self.help_messages:
            return self.help_messages[name]
        else:
            for info in self.help_messages.values():
                if name in info.aliases:
                    return info
        return None

    async def start(self):
        # 检查数据文件夹是否存在
        if not os.path.exists(self.config.data_path):
            os.mkdir(self.config.data_path)
        elif not os.path.isdir(self.config.data_path):
            raise Exception(f'{self.config.data_path} 不是一个文件夹')
        await self.on_startup()
        await super().start()

    async def on_startup(self):
        await check_online()
        await download_resources()

        await paimon_chat.on_startup(self)
        await guess_voice.on_startup(self)
        await paimon_gacha.on_startup(self)
        await paimon_cloud_genshin.on_startup(self)
        await paimon_info.on_startup(self)
        await paimon_calendar.on_startup(self)

    def my_command(self, name: str = '', *, aliases: List[str] = (), usage: str = '暂无使用帮助', introduce: str = '暂无命令介绍',
                   rules=()):
        self.help_messages[name] = CommandInfo(name=name, aliases=aliases, usage=usage, introduce=introduce)
        return self.command(name=name, aliases=aliases, prefixes=[''],
                            rules=[Rule.is_bot_mentioned(self)] + list(rules))

    def my_admin_command(self, name: str = '', *, aliases: List[str] = (), usage: str = '暂无使用帮助',
                         introduce: str = '暂无命令介绍', rules=()):
        return self.my_command(name=name + '(仅限管理员)', aliases=aliases, usage=usage, introduce=introduce,
                               rules=[MyRules.is_admin()] + list(rules))

    def my_regex(self, name: str = '', *, regex: Union[str, Pattern], usage: str = '暂无使用帮助', introduce: str = '暂无命令介绍',
                 rules=()):
        self.help_messages[name] = CommandInfo(name=name, aliases=None, usage=usage, introduce=introduce)
        return self.command(name=name, regex=regex, prefixes=[''], rules=[Rule.is_bot_mentioned(self)] + list(rules))


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

    @bot.my_command(name='help', aliases=['帮助'], introduce='显示所有帮助信息或具体命令的帮助信息',
                    usage='帮助 [命令] e.帮助 help (显示帮助命令的帮助信息)')
    async def print_help_message(msg: Message, *args: str):
        bot_id = bot.me.id
        if len(args) == 1:
            card = Card(Section(Kmarkdown(f'**小派蒙的命令大全！**\n所有的命令末尾都要 (met){bot_id}(met) 哦！')),
                        *[info.build_kmd() for info in bot.help_messages.values()])
        else:
            info = bot.search_command(args[0])
            if info is not None:
                card = Card(info.build_kmd())
            else:
                card = Card(Section(Kmarkdown(f'未找到命令 {args[0]}')))
        card.append(Context(Kmarkdown(f'当前小派蒙版本: {VERSION}')))
        await msg.reply([card.build()])

    # 预留 botmarket 的在线检测
    bot.task.add_interval(minutes=30, timezone='Asia/Shanghai')(check_online)

    bot.run()


async def check_online():
    res = await post('http://bot.gekj.net/api/v1/online.bot', headers={'uuid': config.botmarket_uuid})
    log.info(res.json()['msg'])


if __name__ == '__main__':
    sys.exit(main())
