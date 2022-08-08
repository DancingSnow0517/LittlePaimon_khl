import time
from typing import TYPE_CHECKING

from khl import Message, MessageTypes
from littlepaimon_utils.files import load_json_from_url

from paimon_wiki.abyss_rate_draw import draw_rate_rank, draw_teams_rate
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

    @bot.my_regex(
        name='daily_material',
        regex=r'(?P<day>今日|今天|现在|周[一二三四五六日]|明日|明天|后日|后天)材料 \(met\)(?P<uid>\d+)\(met\)\s',
        usage='!![今日|周x]材料', introduce='查看可刷取的素材表', group=[CommandGroups.WIKI]
    )
    async def daily_material(msg: Message, day: str, _: str):
        if day in ['今日', '今天', '现在']:
            week = time.strftime('%w')
        elif day in ['明日', '明天']:
            week = str((int(time.strftime('%w')) + 1) % 7)
        elif day in ['后日', '后天']:
            week = str((int(time.strftime('%w')) + 2) % 7)
        elif day in ['周一', '周四']:
            week = '1'
        elif day in ['周二', '周五']:
            week = '2'
        elif day in ['周三', '周六']:
            week = '3'
        else:
            week = '0'
        if week == "0":
            await msg.reply('周日所有材料都可以刷哦!')
            return
        elif week in ['1', '4']:
            url = 'LittlePaimon/DailyMaterials/周一周四.jpg'
        elif week in ['2', '5']:
            url = 'LittlePaimon/DailyMaterials/周二周五.jpg'
        else:
            url = 'LittlePaimon/DailyMaterials/周三周六.jpg'
        await msg.reply(await MessageBuilder.static_image(bot, url), type=MessageTypes.IMG)

    @bot.my_command(name='abyss_rate', aliases=['深渊登场率', '深境螺旋登场率', '深渊登场率排行', '深渊排行'],
                    usage='!!深渊登场率', introduce='查看本期深渊的角色登场率', group=[CommandGroups.WIKI])
    async def abyss_rate(msg: Message):
        abyss_img = await draw_rate_rank()
        abyss_img.save('Temp/abyss_rate.png')
        await msg.reply(await bot.create_asset('Temp/abyss_rate.png'), type=MessageTypes.IMG)

    @bot.my_regex(name='abyss_team',
                  regex=r'(?P<type>深渊|深境螺旋)(?P<floor>上半|下半)出场率 \(met\)(?P<uid>\d+)\(met\)\s',
                  usage='',
                  introduce='', group=[CommandGroups.WIKI])
    async def abyss_team(msg: Message, _, floor: str, uid: str):
        abyss_img = await draw_teams_rate(floor)
        abyss_img.save('Temp/abyss_team.png')
        await msg.reply(await bot.create_asset('Temp/abyss_team.png'), type=MessageTypes.IMG)
