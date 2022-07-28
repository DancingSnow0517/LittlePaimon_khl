from typing import TYPE_CHECKING

from khl import Message, MessageTypes
from khl_card import Card
from khl_card.modules import Container
from khl_card.accessory import Image

from paimon_info.draw_abyss_info import draw_abyss_card
from paimon_info.draw_daily_note import draw_daily_note_card
from paimon_info.get_data import get_abyss_data, get_daily_note_data
from utils.config import cookie_data

if TYPE_CHECKING:
    from main import LittlePaimonBot


async def on_startup(bot: 'LittlePaimonBot'):

    @bot.task.add_interval(hours=1)
    async def auto_note():
        ...

    @bot.my_command(name='sy', aliases=['深渊信息', '深境螺旋信息'], introduce='查看深渊战绩信息', usage='sy [uid] [层数]')
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
            if isinstance(abyss_img, str):
                await msg.reply(abyss_img)
                return
            abyss_img.save('Temp/abyss.png')
            images.append(await bot.create_asset('Temp/abyss.png'))
        await msg.reply([Card(Container(*[Image(src=url)for url in images])).build()])

    @bot.my_command(name='ssbq', aliases=['实时便笺', '实时便签', '当前树脂'])
    async def ssbq(msg: Message, *args):
        if len(args) == 1:
            await msg.reply('请输入要查询的uid')
        uid = args[0]
        data = await get_daily_note_data(msg.author.id, uid)
        if isinstance(data, str):
            await msg.reply(data)
        else:
            img = await draw_daily_note_card(data, uid)
            if isinstance(img, str):
                await msg.reply(img)
                return
            img.save('Temp/note.png')
            await msg.reply(await bot.create_asset('Temp/note.png'), type=MessageTypes.IMG)

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

    @bot.my_command(name='ysb', aliases=['原神绑定', '绑定cookie'], usage='原神绑定 [uid] [cookie]')
    async def ysb(msg: Message, *args):
        if len(args) <= 2:
            await msg.reply('请输入你的 uid 和 cookie')
            return
        uid = args[0]
        cookie = ' '.join(args[1:-1])
        cookie_data.add_private_cookie(uid, msg.author.id, cookie)
        await msg.delete()
        await msg.ctx.channel.send(f'cookie 添加成功 (met){msg.author.id}(met)')

    @bot.my_command(name='mys_sign', aliases=['mys签到', '米游社签到'])
    async def mys_sign(msg: Message):
        ...

    ...
