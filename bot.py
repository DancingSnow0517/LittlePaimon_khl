import asyncio
import hashlib
import logging
import os.path
from pathlib import Path
from typing import List, Dict, Optional, Union, Pattern

from khl import Bot, Message, EventTypes, Event, User, MessageTypes
from khl.command import Rule
from khl_card import Card
from khl_card.accessory import Kmarkdown, Button
from khl_card.modules import Section, Context, ActionGroup, Divider, Header, Invite
from littlepaimon_utils.aiorequests import post
from littlepaimon_utils.files import load_json, download

from guess_voice import guess_voice
from paimon_calendar import paimon_calendar
from paimon_chat import paimon_chat
from paimon_cloud_genshin import paimon_cloud_genshin
from paimon_gacha import paimon_gacha
from paimon_info import paimon_info
from utils.api import CommandInfo, MyRules, CommandGroups
from utils.config import config

resource_list = load_json(path=Path(__file__).parent / 'resources' / 'resource_list.json')
resource_path = Path().cwd() / 'resources' / 'LittlePaimon'

log = logging.getLogger(__name__)

VERSION = '1.1.0'


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

    def my_command(self, name: str = '', *, aliases: List[str] = (), usage: str = '暂无使用帮助',
                   introduce: str = '暂无命令介绍',
                   rules=(), group: List[CommandGroups] = ()):
        self.help_messages[name] = CommandInfo(name=name, aliases=aliases, usage=usage, introduce=introduce,
                                               group=group)
        return self.command(name=name, aliases=aliases, prefixes=['！！', '!!'],
                            rules=list(rules))

    def my_admin_command(self, name: str = '', *, aliases: List[str] = (), usage: str = '暂无使用帮助',
                         introduce: str = '暂无命令介绍', rules=(), group: List[CommandGroups] = ()):
        return self.my_command(name=name + '(仅限管理员)', aliases=aliases, usage=usage, introduce=introduce,
                               rules=[MyRules.is_admin()] + list(rules), group=group)

    def my_regex(self, name: str = '', *, regex: Union[str, Pattern], usage: str = '暂无使用帮助',
                 introduce: str = '暂无命令介绍',
                 rules=(), group: List[CommandGroups] = ()):
        self.help_messages[name] = CommandInfo(name=name, aliases=None, usage=usage, introduce=introduce, group=group)
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
                    usage='!!帮助 [命令] e.帮助 help (显示帮助命令的帮助信息)', group=[CommandGroups.INFO])
    async def print_help_message(msg: Message, command: str = None):
        if command is None:
            card = Card(
                Header('小派蒙的帮助信息'),
                Section(Kmarkdown(f'现在小派蒙所有命令只需要在前面添加`!!`\n不需要 (met){bot.me.id}(met) '
                                  f'了~\n部分命令还需要 (met){bot.me.id}(met), 会有特别标注')),
                Section(
                    Kmarkdown('命令中的 `[ ]` 不用加进去。\n例: `[UID]` 只需要将这个替换为你的 `UID`。`[cookie]` 同理')),
                ActionGroup(
                    *[group.build_button() for group in CommandGroups]
                ),
                Divider(),
                # Section(Kmarkdown('**快捷命令**')),
                # ActionGroup(
                #     Button(Kmarkdown('更新角色信息'), value='update_role_info', click='return-val'),
                #     Button(Kmarkdown('一键签到'), value='sign_all', click='return-val'),
                #     Button(Kmarkdown('实时便签'), value='note', click='return-val')
                # ),
                # Divider(),
                Section(Kmarkdown(f'在使用 (met){bot.me.id}(met) 过程中遇到的问题，可以来的官方频道询问')),
                Invite('s69UmB'),
                Section(Kmarkdown('有能力的可以支持下作者ヾ(≧▽≦*)o'),
                        accessory=Button(Kmarkdown('去发电'), value='https://afdian.net/@dancingsnow', click='link'))
            )
        else:
            info = bot.search_command(command)
            if info is not None:
                card = Card(info.build_kmd())
            else:
                card = Card(Section(Kmarkdown(f'未找到命令 {command}')))
        card.append(Context(Kmarkdown(f'当前小派蒙版本: {VERSION}')))
        await msg.reply([card.build()])

    @bot.command(name='old_help', aliases=['帮助'], prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def old_help(msg: Message, _):
        await msg.reply('小派蒙的命令系统更新啦~~ 现在使用 `!!帮助` 来查看帮助信息', type=MessageTypes.KMD)

    # 预留 botmarket 的在线检测
    bot.task.add_interval(minutes=30, timezone='Asia/Shanghai')(check_online)

    @bot.on_event(EventTypes.SELF_JOINED_GUILD)
    async def on_joined_guild(bot: LittlePaimonBot, event: Event):
        guild_id = event.body['guild_id']
        guild = await bot.fetch_guild(guild_id)
        log.info(f'小派蒙加入服务器 {guild.name}, id: {guild.id}')

    @bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
    async def on_help_button_click(bot: LittlePaimonBot, event: Event):
        value: str = event.body['value']
        user_id: str = event.body['user_id']
        channel_id: str = event.body['target_id']
        channel_type = event.body['channel_type']
        if value.startswith('command_group_'):
            target = await bot.fetch_public_channel(channel_id) if channel_type == 'GROUP' else await bot.fetch_user(
                user_id)
            g = None
            for g in CommandGroups:
                if g.name == value.replace('command_group_', ''):
                    group = g
                    break
            if g is None:
                return
            log.info(f'给 {user_id} 回复命令组 {group.value}')
            card = Card(
                Header(f'分组 {group.value} 的命令列表'),
                *[info.build_kmd() for info in bot.help_messages.values() if group in info.groups]
            )
            card.append(Context(Kmarkdown(f'当前小派蒙版本: {VERSION}')))
            if isinstance(target, User):
                await target.send([card.build()])
            else:
                await target.send([card.build()], temp_target_id=user_id)
            return

    bot.run()


async def check_online():
    res = await post('http://bot.gekj.net/api/v1/online.bot', headers={'uuid': config.botmarket_uuid})
    log.info(res.json()['msg'])
