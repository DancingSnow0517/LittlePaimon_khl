from typing import TYPE_CHECKING

from khl import Message
from khl_card import Card
from khl_card.modules import Container
from khl_card.accessory import Image

from paimon_info.draw_abyss_info import draw_abyss_card
from paimon_info.get_data import get_abyss_data
from utils.config import cookie_data

if TYPE_CHECKING:
    from main import LittlePaimonBot


async def on_startup(bot: 'LittlePaimonBot'):
    @bot.my_command(name='sy', aliases=['深渊信息', '深境螺旋信息'], introduce='查看深渊战绩信息')
    async def sy(msg: Message, *args: str):
        images = []
        if len(args) == 1:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
        else:
            uid = args[0]
        floor = args[1:-1]
        true_floor = [int(f) for f in floor if f.isdigit() and (9 <= int(f) <= 12)]
        true_floor.sort()
        data = await get_abyss_data(msg.author.id, uid)
        if data is None:
            await msg.reply('深渊数据获取失败')
            return
        else:
            abyss_img = await draw_abyss_card(data, uid, floor_num=true_floor)
            abyss_img.save('Temp/abyss.png')
            images.append(await bot.create_asset('Temp/abyss.png'))
        await msg.reply([Card(Container(*[Image(src=url)for url in images])).build()])

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
    async def ysb(msg: Message, *args):
        if len(args) == 1:
            await msg.reply('请输入你的 cookie')
            return
        cookie = ' '.join(args[0:-1])
        cookie_data.add_private_cookie(msg.author.id, cookie)
        await msg.delete()
        await msg.ctx.channel.send(f'cookie 添加成功 (met){msg.author.id}(met)')

    @bot.my_command(name='mys_sign', aliases=['mys签到', '米游社签到'])
    async def mys_sign(msg: Message):
        ...

    ...
