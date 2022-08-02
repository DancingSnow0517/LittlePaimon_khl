import datetime
import logging
import random
from asyncio import sleep
from typing import TYPE_CHECKING, Dict, List

from khl import Message, MessageTypes, EventTypes, Event
from khl_card import Card, ThemeTypes
from khl_card.accessory import Image, Kmarkdown, Button, PlainText
from khl_card.modules import Container, Section, Header, ActionGroup

from paimon_info.draw_abyss_info import draw_abyss_card
from paimon_info.draw_daily_note import draw_daily_note_card
from paimon_info.draw_month_info import draw_monthinfo_card
from paimon_info.draw_player_card import draw_player_card, draw_all_chara_card
from paimon_info.draw_role_card import draw_role_card
from paimon_info.get_coin import MihoyoBBSCoin
from paimon_info.get_data import get_abyss_data, get_daily_note_data, get_monthinfo_data, get_player_card_data, \
    get_chara_detail_data, get_sign_list, get_sign_info, sign, get_enka_data, addStoken
from utils.alias_handler import get_match_alias
from utils.api import CommandGroups
from utils.config import cookie_data, stoken_data
from utils.enka_util import PlayerInfo

if TYPE_CHECKING:
    from bot import LittlePaimonBot

log = logging.getLogger(__name__)

wait_to_rm: Dict[str, bool] = {}

cookie_error_msg = '这个cookie无效哦，请旅行者确认是否正确\n1.ck要登录mys帐号后获取,' \
                   '且不能退出登录\n\n获取cookie的教程：\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1\n '

is_reminded: List[str] = []


async def on_startup(bot: 'LittlePaimonBot'):
    @bot.task.add_interval(hours=1, timezone='Asia/Shanghai')
    async def auto_note():
        global is_reminded
        for uid in cookie_data.cookies:
            if uid in is_reminded:
                continue
            info = cookie_data.get_cookie_by_uid(uid)
            data = await get_daily_note_data(info.owner, uid)
            if not isinstance(data, str):
                if data['data']['current_resin'] >= 140:
                    user = await bot.fetch_user(info.owner)
                    await user.send('树脂快要溢出了~~~' if data['data']['current_resin'] < 160 else '树脂溢出了~~~')
                    img = await draw_daily_note_card(data, uid)
                    if isinstance(img, str):
                        await user.send(img)
                        return
                    img.save('Temp/note.png')
                    await user.send(await bot.create_asset('Temp/note.png'), type=MessageTypes.IMG)
                    is_reminded.append(uid)

    @bot.task.add_cron(hour=6, timezone='Asia/Shanghai')
    async def auto_sign():
        global is_reminded
        is_reminded.clear()
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

    @bot.task.add_cron(hour=0, timezone='Asia/Shanghai')
    async def auto_get_coin():
        stokens = stoken_data.get_all_stoken()
        for user_id in stokens:
            user = await bot.fetch_user(user_id)
            stoken = stokens[user_id].stoken
            get_coin_task = MihoyoBBSCoin(stoken)
            data = await get_coin_task.task_run()
            await user.send("米游币获取完成\n" + data)

    @bot.my_command(name='sy', aliases=['深渊信息', '深境螺旋信息'], introduce='查看深渊战绩信息',
                    usage='!!深渊信息 [uid] [层数]', group=[CommandGroups.INFO])
    async def sy(msg: Message, uid: str = None, *floor: str):
        images = []
        if uid is None:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
        if len(floor) == 0:
            await msg.reply('请给要查询的层数给小派蒙哦~')
            return
        true_floor = [int(f) for f in floor if f.isdigit() and (9 <= int(f) <= 12)]
        true_floor.sort()
        data = await get_abyss_data(msg.author.id, uid)
        if data is None:
            await msg.reply('深渊数据获取失败')
            return
        elif isinstance(data, str):
            await msg.reply(data)
            return
        else:
            abyss_img = await draw_abyss_card(data, uid, floor_num=true_floor)
            if isinstance(abyss_img, str):
                await msg.reply(abyss_img)
                return
            abyss_img.save('Temp/abyss.png')
            images.append(await bot.create_asset('Temp/abyss.png'))
        await msg.reply([Card(Container(*[Image(src=url) for url in images])).build()])

    @bot.my_command(name='ssbq', aliases=['实时便笺', '实时便签', '当前树脂'], introduce='查看当前的体力信息',
                    usage='!!实时便笺 [uid]', group=[CommandGroups.INFO])
    async def ssbq(msg: Message, uid: str = None):
        if uid is None:
            await msg.reply('请输入要查询的uid')
            return
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

    @bot.my_command(name='myzj', aliases=['札记信息', '每月札记'], introduce='查看每月札记', usage='!!札记信息 [uid] [月份]', group=[CommandGroups.INFO])
    async def myzj(msg: Message, uid: str = None, month: str = datetime.datetime.now().month):
        if uid is None:
            await msg.reply('请输入要查询的uid')
            return
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

    @bot.my_command(name='ys', aliases=['原神卡片', '个人卡片'], introduce='查看原神个人卡片(宝箱、探索度等)',
                    usage='!!原神卡片 [uid]', group=[CommandGroups.INFO])
    async def ys(msg: Message, uid: str = None):
        if uid is None:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
        data = await get_player_card_data(msg.author.id, uid)
        if data is None:
            await msg.reply('原神卡片数据获取失败')
        else:
            chara_data = await get_chara_detail_data(msg.author.id, uid)
            if isinstance(chara_data, str):
                await msg.reply(chara_data)
                return
            player_card = await draw_player_card(data, chara_data, uid, msg.author.nickname)
            if isinstance(player_card, str):
                await msg.reply(player_card)
                return
            player_card.save('Temp/player_card.png')
            await msg.reply(await bot.create_asset('Temp/player_card.png'), type=MessageTypes.IMG)

    @bot.my_command(name='ysa', aliases=['角色背包'], introduce='查看原神公开角色的简略信息', usage='!!角色背包 [uid]', group=[CommandGroups.INFO])
    async def ysa(msg: Message, uid: str = None):
        if uid is None:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
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

    @bot.my_command(name='ysc', aliases=['角色卡片'], usage='暂未实现', introduce='查看原神指定角色的简略信息', group=[CommandGroups.INFO])
    async def ysc(msg: Message):
        ...

    @bot.my_command(name='ysb', aliases=['原神绑定', '绑定cookie'], usage='!!原神绑定 [uid] [cookie]', group=[CommandGroups.INFO])
    async def ysb(msg: Message, uid: str = None, *cookie):
        if uid is None or len(cookie) == 0:
            card = Card(
                Section(Kmarkdown('缺少参数 uid 和 cookie')),
                Section(Kmarkdown('获取 `cookie` 教程: '), accessory=Button(
                    Kmarkdown('访问'), value='https://gitee.com/ultradream/Genshin-Tools', click='link'
                ))
            )
            await msg.reply([card.build()])
            return
        cookie = ' '.join(cookie)
        cookie_data.add_private_cookie(uid, msg.ctx.guild.id, msg.author.id, cookie)
        await msg.delete()
        await msg.ctx.channel.send(f'cookie 添加成功 (met){msg.author.id}(met)')

    @bot.my_command(name='mys_sign', aliases=['mys签到', '米游社签到'], introduce='米游社签到', usage='!!米游社签到 [uid]', group=[CommandGroups.SIGN])
    async def mys_sign(msg: Message, uid: str = None):
        if uid is None:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
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

    @bot.my_admin_command(name='mys_sign_all', aliases=['全部重签'], introduce='米游社的每日签到重签',
                          usage='!!全部重签', group=[CommandGroups.SIGN])
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

    @bot.my_admin_command(name='update_all', aliases=['更新全部玩家'], introduce='更新所有人的信息',
                          usage='!!更新全部玩家', group=[CommandGroups.INFO])
    async def update_all(msg: Message, _):
        res = await all_update()
        await msg.reply(res)

    @bot.my_admin_command(name='add_public_ck', aliases=['添加公共cookie', '添加公共ck'], introduce='添加公共cookie',
                          usage='!!添加公共cookie [cookie]', group=[CommandGroups.INFO])
    async def add_public_ck(msg: Message, *args):
        if len(args) == 1:
            await msg.reply('小派蒙要你的 cookie 哦')
            return
        cookie = ' '.join(args[:-1])
        cookie_data.add_public_cookie(cookie)
        await msg.delete()
        await msg.ctx.channel.send('公共 cookie 添加成功！')

    @bot.my_command(name='delete_ck', aliases=['删除ck', '删除cookie'], introduce='删除你的所有cookie',
                    usage='!!删除cookie', group=[CommandGroups.INFO])
    async def delete_ck(msg: Message):
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

    @bot.my_command(name='update_info', aliases=['更新角色信息', '更新角色面板', '更新玩家信息'],
                    introduce='更新角色信息', usage='!!更新角色信息 [UID]', group=[CommandGroups.INFO])
    async def update_info(msg: Message, uid: str = None):
        if uid is None:
            await msg.reply('请给你的 UID 给小派蒙哦~')
            return
        await msg.reply('派蒙开始更新信息~请稍等哦~')
        enka_data = await get_enka_data(uid)
        if not enka_data:
            if uid[0] == '5':
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

    @bot.my_command(name='role_info', aliases=['角色面板', '角色详情', '角色信息', 'ysd'],
                    introduce='查看指定角色的详细面板信息',
                    usage='!!角色面板 [UID] [角色]', group=[CommandGroups.INFO])
    async def role_info(msg: Message, uid: str = None, char: str = None):
        if uid is None or char is None:
            await msg.reply('请给你的uid和要查询的角色给小派蒙哦~')
            return
        if char in ('a', '全部', '所有', '查看', 'all'):
            role = 'all'
        else:
            match_alias = get_match_alias(char, 'roles', True)
            if match_alias:
                role = match_alias if isinstance(match_alias, str) else tuple(match_alias.keys())[0]
            else:
                await msg.reply(f'哪有名为{char}的角色啊，别拿派蒙开玩笑!')
                return
        player_info = PlayerInfo(uid)
        roles_list = player_info.get_roles_list()
        if role == 'all':
            if not roles_list:
                await msg.reply('你在派蒙这里没有角色面板信息哦，先用 更新角色信息 命令获取吧~', at_sender=True)
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

    @bot.my_command(name='get_mys_coin', aliases=['myb获取', '米游币获取', '获取米游币'],
                    introduce='进行一次获取米游币的操作', usage='!!米游币获取 [UID]', group=[CommandGroups.SIGN])
    async def get_mys_coin(msg: Message):
        stoken_info = stoken_data.get_private_stoken(msg.author.id)
        if stoken_info is None:
            await msg.reply('请旅行者先添加 cookie 和 stoken 哦')
            return
        stoken = stoken_info.stoken
        await msg.reply('开始执行米游社获取，请稍等哦~')
        get_coin_task = MihoyoBBSCoin(stoken)
        data = await get_coin_task.task_run()
        await msg.reply("米游币获取完成\n" + data)

    @bot.my_command(name='add_stoken', aliases=['添加stoken'], introduce='绑定你的stoken，来支持米游币相关的操作',
                    usage='!!添加stoken [stoken]', group=[CommandGroups.INFO])
    async def add_stoken(msg: Message, *args):
        if len(args) == 0:
            await msg.reply([
                Card(
                    Section(Kmarkdown('缺少参数 `stoken`')),
                    Section(Kmarkdown('获取 `stoken` 教程'),
                            accessory=Button(Kmarkdown('访问'), value='https://docs.qq.com/doc/DQ3JLWk1vQVllZ2Z1',
                                             click='link'))).build()])
            return
        stoken = ' '.join(args)
        cookie_info = cookie_data.get_user_cookies(msg.author.id)
        if len(cookie_info) == 0:
            return
        uid = list(cookie_info.keys())[0]
        stoken, mys_id, stoken_info, m = await addStoken(stoken, uid)

        if not stoken_info and not mys_id:
            await msg.reply(m)
        if not stoken_info or stoken_info['retcode'] != 0:
            await msg.reply(cookie_error_msg)
        else:
            if uid:
                stoken_data.add_private_stoken(msg.author.id, uid=uid, mys_id=mys_id, cookie='', stoken=stoken)
                await msg.reply('stoken绑定成功啦!')

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
