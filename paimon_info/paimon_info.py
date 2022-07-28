import datetime
from typing import TYPE_CHECKING

from khl import Message, MessageTypes
from khl_card import Card
from khl_card.accessory import Image, Kmarkdown, Button
from khl_card.modules import Container, Section

from paimon_info.draw_abyss_info import draw_abyss_card
from paimon_info.draw_daily_note import draw_daily_note_card
from paimon_info.draw_month_info import draw_monthinfo_card
from paimon_info.draw_player_card import draw_player_card, draw_all_chara_card
from paimon_info.get_data import get_abyss_data, get_daily_note_data, get_monthinfo_data, get_player_card_data, \
    get_chara_detail_data, get_sign_list, get_sign_info, sign
from utils.config import cookie_data

if TYPE_CHECKING:
    from main import LittlePaimonBot


async def on_startup(bot: 'LittlePaimonBot'):
    @bot.task.add_interval(hours=1)
    async def auto_note():
        for uid in cookie_data.cookies:
            info = cookie_data.get_cookie_by_uid(uid)
            data = await get_daily_note_data(info.owner, uid)
            if not isinstance(data, str):
                if data['current_resin'] >= 140:
                    user = await bot.fetch_user(info.owner)
                    await user.send('树脂快要溢出了~~~')
                    img = await draw_daily_note_card(data, uid)
                    if isinstance(img, str):
                        await user.send(img)
                        return
                    img.save('Temp/note.png')
                    await user.send(await bot.create_asset('Temp/note.png'), type=MessageTypes.IMG)

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
        await msg.reply([Card(Container(*[Image(src=url) for url in images])).build()])

    @bot.my_command(name='ssbq', aliases=['实时便笺', '实时便签', '当前树脂'], introduce='查看当前的体力信息', usage='ssbq [uid]')
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

    @bot.my_command(name='myzj', aliases=['札记信息', '每月札记'], introduce='查看每月札记', usage='myzj [uid] [月份]')
    async def myzj(msg: Message, *args):
        if len(args) != 3:
            await msg.reply('命令格式不正确')
            return
        uid = args[0]
        month = args[1]
        month_now = datetime.datetime.now().month
        if month_now == 1:
            month_list = ['11', '12', '1']
        elif month_now == 2:
            month_list = ['12', '1', '2']
        else:
            month_list = [str(month_now - 2), str(month_now - 1), str(month_now)]
        if month not in month_list:
            await msg.reply('只能获取最近 3 个月的札记')
            return
        data = await get_monthinfo_data(msg.author.id, uid, month)
        if isinstance(data, str):
            await msg.reply(data)
        else:
            month_img = await draw_monthinfo_card(data)
            if isinstance(month_img, str):
                await msg.reply(month_img)
                return
            month_img.save('Temp/month.png')
            await msg.reply(await bot.create_asset('Temp/month.png'), type=MessageTypes.IMG)

    @bot.my_command(name='ys', aliases=['原神卡片', '个人卡片'], introduce='查看原神个人卡片(宝箱、探索度等)', usage='ys [uid]')
    async def ys(msg: Message, *args):
        if len(args) == 1:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
        uid = args[0]
        data = await get_player_card_data(msg.author.id, uid)
        if data is None:
            await msg.reply('原神卡片数据获取失败')
        else:
            chara_data = await get_chara_detail_data(msg.author.id, uid)
            player_card = await draw_player_card(data, chara_data, uid, msg.author.nickname)
            if isinstance(player_card, str):
                await msg.reply(player_card)
                return
            player_card.save('Temp/player_card.png')
            await msg.reply(await bot.create_asset('Temp/player_card.png'), type=MessageTypes.IMG)

    @bot.my_command(name='ysa', aliases=['角色背包'], introduce='查看原神公开角色的简略信息', usage='ysa [uid]')
    async def ysa(msg: Message, *args):
        if len(args) == 1:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
        uid = args[0]
        chara_data = await get_chara_detail_data(msg.author.id, uid)
        if isinstance(chara_data, str):
            await msg.reply(chara_data)
            return
        char_card = await draw_all_chara_card(chara_data, uid)
        if isinstance(char_card, str):
            await msg.reply(char_card)
            return
        char_card.save('Temp/char_card.png')
        await msg.reply(await bot.create_asset('Temp/char_card.png'), type=MessageTypes.IMG)
        ...

    @bot.my_command(name='ysc', aliases=['角色卡片'], usage='暂未实现', introduce='查看原神指定角色的简略信息')
    async def ysc(msg: Message):
        ...

    @bot.my_command(name='ysb', aliases=['原神绑定', '绑定cookie'], usage='原神绑定 [uid] [cookie]')
    async def ysb(msg: Message, *args):
        if len(args) <= 2:
            card = Card(Section(Kmarkdown('缺少参数 uid 和 cookie')), Section(Kmarkdown('获取 `cookie` 教程: '), accessory=Button(Kmarkdown('访问'), value='https://gitee.com/ultradream/Genshin-Tools', click='link')))
            await msg.reply([card.build()])
            return
        uid = args[0]
        cookie = ' '.join(args[1:-1])
        cookie_data.add_private_cookie(uid, msg.author.id, cookie)
        await msg.delete()
        await msg.ctx.channel.send(f'cookie 添加成功 (met){msg.author.id}(met)')

    @bot.my_command(name='mys_sign', aliases=['mys签到', '米游社签到'], introduce='米游社签到', usage='mys_sign [uid]')
    async def mys_sign(msg: Message, *args):
        if len(args) == 1:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
        uid = args[0]
        sign_list = await get_sign_list()
        sign_info = await get_sign_info(msg.author.id, uid)
        if isinstance(sign_info, str):
            await msg.reply(sign_info)
        elif sign_info['data']['is_sign']:
            sign_day = sign_info['data']['total_sign_day'] - 1
            await msg.reply(
                f'你今天已经签过到了哦,获得的奖励为:\n{sign_list["data"]["awards"][sign_day]["name"]} * {sign_list["data"]["awards"][sign_day]["cnt"]}')
        else:
            sign_day = sign_info['data']['total_sign_day']
            sign_action = await sign(msg.author.id, uid)
            if isinstance(sign_action, str):
                await msg.reply(sign_action)
            else:
                await msg.reply(
                    f'签到成功,获得的奖励为:\n{sign_list["data"]["awards"][sign_day]["name"]} * {sign_list["data"]["awards"][sign_day]["cnt"]}')
