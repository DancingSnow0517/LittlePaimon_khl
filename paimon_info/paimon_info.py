from typing import TYPE_CHECKING

from khl import Message
from khl.command import Rule

if TYPE_CHECKING:
    from main import LittlePaimonBot


async def on_startup(bot: 'LittlePaimonBot'):

    @bot.my_command(name='sy', aliases=['深渊信息', '深境螺旋信息'])
    async def sy(msg: Message):
        ...

    @bot.command(name='ssbq', aliases=['实时便笺', '实时便签', '当前树脂'], prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def ssbq(msg: Message):
        ...

    @bot.command(name='myzj', aliases=['札记信息', '每月札记'], prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def myzj(msg: Message):
        ...

    @bot.command(name='ys', aliases=['原神卡片', '个人卡片'], prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def ys(msg: Message):
        ...

    @bot.command(name='ysa', aliases=['角色背包'], prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def ysa(msg: Message):
        ...

    @bot.command(name='ysc', aliases=['角色卡片'], prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def ysc(msg: Message):
        ...

    @bot.command(name='ysb', aliases=['原神绑定', '绑定cookie'], prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def ysb(msg: Message):
        ...

    @bot.command(name='mys_sign', aliases=['mys签到', '米游社签到'], prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def mys_sign(msg: Message):
        ...
    ...
