import datetime
import logging
import random
from asyncio import sleep
from typing import TYPE_CHECKING, Dict

from khl import Message, MessageTypes, EventTypes, Event
from khl_card import Card, ThemeTypes
from khl_card.accessory import Image, Kmarkdown, Button, PlainText
from khl_card.modules import Container, Section, Header, ActionGroup

from paimon_info.draw_abyss_info import draw_abyss_card
from paimon_info.draw_daily_note import draw_daily_note_card
from paimon_info.draw_month_info import draw_monthinfo_card
from paimon_info.draw_player_card import draw_player_card, draw_all_chara_card
from paimon_info.draw_role_card import draw_role_card
from paimon_info.get_data import get_abyss_data, get_daily_note_data, get_monthinfo_data, get_player_card_data, \
    get_chara_detail_data, get_sign_list, get_sign_info, sign, get_enka_data
from utils.alias_handler import get_match_alias
from utils.config import cookie_data
from utils.enka_util import PlayerInfo

if TYPE_CHECKING:
    from main import LittlePaimonBot

log = logging.getLogger(__name__)

wait_to_rm: Dict[str, bool] = {}


async def on_startup(bot: 'LittlePaimonBot'):
    @bot.task.add_interval(hours=1, timezone='Asia/Shanghai')
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

    @bot.task.add_cron(hour=6, timezone='Asia/Shanghai')
    async def auto_sign():
        sign_list = await get_sign_list()
        cookies = cookie_data.cookies
        for uid in cookies:
            user = await bot.fetch_user(cookies[uid].owner)
            sign_info = await get_sign_info(cookies[uid].owner, uid)
            if isinstance(sign_info, str):
                await user.send('=====小派蒙的自动签到=====\n' + sign_info)
            elif sign_info['data']['is_sign']:
                sign_day = sign_info['data']['total_sign_day'] - 1
                await user.send(
                    f'=====小派蒙的自动签到=====\n你今天已经签过到了哦, 获得的奖励为:\n{sign_list["data"]["awards"][sign_day]["name"]} * {sign_list["data"]["awards"][sign_day]["cnt"]}')
            else:
                sign_day = sign_info['data']['total_sign_day']
                sign_action = await sign(cookies[uid].owner, uid)
                if isinstance(sign_action, str):
                    await user.send('=====小派蒙的自动签到=====\n' + sign_action)
                else:
                    await user.send(
                        f'=====小派蒙的自动签到=====\n签到成功, 获得的奖励为:\n{sign_list["data"]["awards"][sign_day]["name"]} * {sign_list["data"]["awards"][sign_day]["cnt"]}')

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
            card = Card(Section(Kmarkdown('缺少参数 uid 和 cookie')), Section(Kmarkdown('获取 `cookie` 教程: '),
                                                                         accessory=Button(Kmarkdown('访问'),
                                                                                          value='https://gitee.com/ultradream/Genshin-Tools',
                                                                                          click='link')))
            await msg.reply([card.build()])
            return
        uid = args[0]
        cookie = ' '.join(args[1:-1])
        cookie_data.add_private_cookie(uid, msg.ctx.guild.id, msg.author.id, cookie)
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
                f'你今天已经签过到了哦, 获得的奖励为:\n{sign_list["data"]["awards"][sign_day]["name"]} * {sign_list["data"]["awards"][sign_day]["cnt"]}')
        else:
            sign_day = sign_info['data']['total_sign_day']
            sign_action = await sign(msg.author.id, uid)
            if isinstance(sign_action, str):
                await msg.reply(sign_action)
            else:
                await msg.reply(
                    f'签到成功, 获得的奖励为:\n{sign_list["data"]["awards"][sign_day]["name"]} * {sign_list["data"]["awards"][sign_day]["cnt"]}')

    @bot.my_admin_command(name='mys_sign_all', aliases=['全部重签'])
    async def mys_sign_all(msg: Message, _):
        await msg.ctx.guild.load()
        await msg.reply('正在给服务器所有人进行重新签到')
        cookies = cookie_data.get_guild_cookies(msg.ctx.guild.id)
        sign_list = await get_sign_list()
        for uid in cookies:
            user = await bot.fetch_user(cookies[uid].owner)
            sign_info = await get_sign_info(cookies[uid].owner, uid)
            if isinstance(sign_info, str):
                await user.send(f'=====服务器 {msg.ctx.guild.name} 的管理员的手动全部重签=====\n' + sign_info)
            elif sign_info['data']['is_sign']:
                sign_day = sign_info['data']['total_sign_day'] - 1
                await user.send(
                    f'=====服务器 {msg.ctx.guild.name} 的管理员的手动全部重签=====\n你今天已经签过到了哦, 获得的奖励为:\n{sign_list["data"]["awards"][sign_day]["name"]} * {sign_list["data"]["awards"][sign_day]["cnt"]}')
            else:
                sign_day = sign_info['data']['total_sign_day']
                sign_action = await sign(cookies[uid].owner, uid)
                if isinstance(sign_action, str):
                    await user.send('=====服务器 {msg.ctx.guild.name} 的管理员的手动全部重签=====\n' + sign_action)
                else:
                    await user.send(
                        f'=====服务器 {msg.ctx.guild.name} 的管理员的手动全部重签=====\n签到成功, 获得的奖励为:\n{sign_list["data"]["awards"][sign_day]["name"]} * {sign_list["data"]["awards"][sign_day]["cnt"]}')

    @bot.my_admin_command(name='update_all', aliases=['更新全部玩家'])
    async def update_all(msg: Message, _):
        res = await all_update()
        await msg.reply(res)

    @bot.my_admin_command(name='add_public_ck', aliases=['添加公共cookie', '添加公共ck'])
    async def add_public_ck(msg: Message, *args):
        if len(args) == 1:
            await msg.reply('小派蒙要你的 cookie 哦')
            return
        cookie = ' '.join(args[:-1])
        cookie_data.add_public_cookie(cookie)
        await msg.delete()
        await msg.ctx.channel.send('公共 cookie 添加成功！')

    @bot.my_command(name='delete_ck', aliases=['删除ck', '删除cookie'])
    async def delete_ck(msg: Message, _):
        card = Card(
            Header('是否要删除所有 cookies？'),
            ActionGroup(
                Button(PlainText('YES'), click='return-val', value='delete_ck_yes', theme='danger'),
                Button(PlainText('NO'), click='return-val', value='delete_ck_no', theme='success')
            ),
            theme=ThemeTypes.DANGER
        )
        wait_to_rm[msg.author.id] = True
        await msg.reply([card.build()])

    @bot.my_command(name='update_info', aliases=['更新角色信息', '更新角色面板', '更新玩家信息'])
    async def update_info(msg: Message, *args):
        if len(args) == 1:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
        uid = args[0]
        await msg.reply('派蒙开始更新信息~请稍等哦~')
        enka_data = await get_enka_data(uid)
        if not enka_data:
            if uid[0] == '5' or uid[0] == '2':
                await msg.reply('暂不支持B服账号哦~请等待开发者更新吧~')
                return
            else:
                await msg.reply('派蒙没有查到该uid的信息哦~')
                return
        player_info = PlayerInfo(uid)
        player_info.set_player(enka_data['playerInfo'])
        if 'avatarInfoList' not in enka_data:
            player_info.save()
            await msg.reply('你未在游戏中打开角色展柜，派蒙查不到~请打开5分钟后再试~')
        else:
            for role in enka_data['avatarInfoList']:
                player_info.set_role(role)
            player_info.save()
            role_list = list(player_info.get_update_roles_list().keys())
            await msg.reply(f'uid{uid}更新完成~本次更新的角色有：\n' + ' '.join(role_list))

    @bot.my_command(name='role_info', aliases=['角色面板', '角色详情', '角色信息', 'ysd'], introduce='查看指定角色的详细面板信息')
    async def role_info(msg: Message, *args):
        if len(args) <= 2:
            await msg.reply('请给你的UID和要查看的角色给小派蒙哦~')
            return
        uid = args[0]
        if args[1] in ('a', '全部', '所有', '查看', 'all'):
            role = 'all'
        else:
            match_alias = get_match_alias(args[1], 'roles', True)
            if match_alias:
                role = match_alias if isinstance(match_alias, str) else tuple(match_alias.keys())[0]
            else:
                await msg.reply(f'哪有名为{args[1]}的角色啊，别拿派蒙开玩笑!')
                return
        player_info = PlayerInfo(uid)
        roles_list = player_info.get_roles_list()
        if role == 'all':
            if not roles_list:
                await role_info.finish('你在派蒙这里没有角色面板信息哦，先用 更新角色信息 命令获取吧~', at_sender=True)
            res = '目前已获取的角色面板有：\n'
            for r in roles_list:
                res += r
                res += ' ' if (roles_list.index(r) + 1) % 4 else '\n'
            await msg.reply(res)
            return
        if role not in roles_list:
            await msg.reply(f'派蒙还没有你{role}的信息哦，先用 更新角色信息 命令更新吧~')
            return
        else:
            role_data = player_info.get_roles_info(role)
            img = await draw_role_card(uid, role_data)
            img.save('Temp/role_card.png')
            await msg.reply(await bot.create_asset('Temp/role_card.png'), type=MessageTypes.IMG)

    @bot.my_command(name='get_mys_coin', aliases=['myb获取', '米游币获取', '获取米游币'])
    async def get_mys_coin(msg: Message):
        ...

    @bot.my_command(name='get_mys_coin_auto', aliases=['myb自动获取', '米游币自动获取', '自动获取米游币'], introduce='自动获取米游币')
    async def get_mys_coin_auto(msg: Message):
        ...

    @bot.my_command(name='add_stoken', aliases=['添加stoken'])
    async def add_stoken(msg: Message):
        ...

    @bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
    async def choice(_: 'LittlePaimonBot', event: Event):
        value = event.body['value']
        user_id = event.body['user_id']
        if user_id not in wait_to_rm:
            return
        if wait_to_rm[user_id]:
            if value == 'delete_ck_yes':
                cookie_data.delete_user_cookies(user_id)
            wait_to_rm[user_id] = False


async def all_update():
    uid_list = cookie_data.cookies
    log.info('派蒙开始更新用户角色信息，共 {} 个用户'.format(len(uid_list)))
    failed_time = 0
    for uid in uid_list:
        try:
            data = await get_enka_data(uid)
            if data:
                player_info = PlayerInfo(uid)
                player_info.set_player(data['playerInfo'])
                if 'avatarInfoList' in data:
                    for role in data['avatarInfoList']:
                        player_info.set_role(role)
                player_info.save()
                log.info(f'---派蒙更新{uid}的角色信息成功---')
            await sleep(random.randint(8, 15))
        except Exception:
            failed_time += 1
            if failed_time > 5:
                break
    return '玩家信息uid更新共 {} 个，更新完成'.format(len(uid_list))
