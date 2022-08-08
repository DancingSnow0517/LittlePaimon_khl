from typing import TYPE_CHECKING

from khl import Message, MessageTypes
from littlepaimon_utils.files import load_json_from_url

from utils.alias_handler import get_match_alias
from utils.api import CommandGroups
from utils.message_util import MessageBuilder

if TYPE_CHECKING:
    from bot import LittlePaimonBot


async def on_startup(bot: 'LittlePaimonBot'):
    @bot.my_command(name='attribute', aliases=['参考面板'], usage='!!参考面板 [角色]',
                    introduce='查看该角色的小毕业参考面板', group=[CommandGroups.WIKI])
    async def attribute(msg: Message, char: str):
        realname = get_match_alias(char)
        if realname:
            blue = await load_json_from_url('https://static.cherishmoon.fun/LittlePaimon/blue/blue.json')
            if realname in blue.keys():
                img = await MessageBuilder.static_image(bot, url=f'LittlePaimon/blue/{blue[realname][0]}.jpg', crop=(
                    0, int(blue[realname][1][0]), 1080, int(blue[realname][1][1])))
                await msg.reply(img, type=MessageTypes.IMG)
            else:
                await msg.reply(f'没有找到 {char} 的参考面板')
        else:
            await msg.reply(f'没有找到 {char} 的参考面板')

    @bot.my_regex(name='daily_material', regex=r'(?<=!!|！！)(?P<day>今日|周[一二三四五六日])材料',
                  usage='!![今日|周x]材料', introduce='查看可刷取的素材表', group=[CommandGroups.WIKI])
    async def daily_material(msg: Message, day: str):
        ...

    @bot.my_command(name='syrate', aliases=['深渊登场率', '深境螺旋登场率', '深渊登场率排行', '深渊排行'],
                    usage='!!深渊登场率', introduce='查看本期深渊的角色登场率', group=[CommandGroups.WIKI])
    async def syrate(msg: Message):
        ...

    @bot.my_regex(name='abyss_team', regex=r'(?<=!!|！！)(?P<type>深渊|深境螺旋)(?P<floor>上半|下半)出场率', usage='',
                  introduce='', group=[CommandGroups.WIKI])
    async def abyss_team(msg: Message, _, floor: str):
        ...
