from typing import TYPE_CHECKING

from khl import Message

if TYPE_CHECKING:
    from main import LittlePaimonBot


async def on_startup(bot: 'LittlePaimonBot'):

    @bot.my_command(name='sy', aliases=['深渊信息', '深境螺旋信息'])
    async def sy(msg: Message):
        ...

    @bot.my_command(name='ssbq', aliases=['实时便笺', '实时便签', '当前树脂'])
    async def ssbq(msg: Message):
        ...

    @bot.my_command(name='myzj', aliases=['札记信息', '每月札记'])
    async def myzj(msg: Message):
        ...

    @bot.my_command(name='ys', aliases=['原神卡片', '个人卡片'])
    async def ys(msg: Message):
        ...

    @bot.my_command(name='ysa', aliases=['角色背包'])
    async def ysa(msg: Message):
        ...

    @bot.my_command(name='ysc', aliases=['角色卡片'])
    async def ysc(msg: Message):
        ...

    @bot.my_command(name='ysb', aliases=['原神绑定', '绑定cookie'])
    async def ysb(msg: Message):
        ...

    @bot.my_command(name='mys_sign', aliases=['mys签到', '米游社签到'])
    async def mys_sign(msg: Message):
        ...
    ...
