import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from khl import Message
from khl_card import NamedColor
from khl_card.accessory import Image, Kmarkdown
from khl_card.card import Card
from khl_card.modules import Container, Header, Section, Divider

from paimon_gacha.gacha_info import save_user_info, init_user_info, user_info
from paimon_gacha.gacha_res import more_ten
from utils import requests
from utils.api import CommandGroups

if TYPE_CHECKING:
    from bot import LittlePaimonBot

BASE_URL = 'https://webstatic.mihoyo.com/hk4e/gacha_info/cn_gf01/%s'
TEMP_PATH = Path() / 'Temp'


async def on_startup(bot: 'LittlePaimonBot'):
    # 检查数据文件夹是否存在
    TEMP_PATH.mkdir(parents=True, exist_ok=True)

    @bot.my_regex(name='gacha', regex=r'^抽(?P<num>\d*)十连(?P<pool>\S*) \(met\)(?P<uid>\d+)\(met\)\s$',
                  usage='抽[次数]十连[池子] e.抽5十连武器', introduce='小派蒙的模拟抽卡, 这个命令要 @小派蒙 哦~',
                  group=[CommandGroups.GAME])
    async def gacha(msg: Message, *args):
        print(args)
        user = msg.author
        num_str = args[0]
        if args[1] != '':
            pool = args[1]
        else:
            pool = '角色1'

        if num_str.isdigit():
            num = int(num_str)
            if num > 9:
                await msg.reply('最多只能同时 9 十连哦')
            elif num <= 0:
                await msg.reply('次数至少为 1 哦')
        else:
            num = 1
        gacha_type = gacha_type_by_name(pool)
        if gacha_type == 0:
            await msg.reply('卡池名称出错,请选择角色1|角色2|武器|常驻')
            return

        if isinstance(gacha_type, int):
            data = await gacha_info_list()
            gacha_data = \
                sorted(list(filter(lambda x: x['gacha_type'] == gacha_type, data)), key=lambda x: x['end_time'])[-1]
            gacha_id = gacha_data['gacha_id']
            gacha_data = await gacha_info(gacha_id)
        else:
            gacha_data = globals()[gacha_type]
        img_list = await more_ten(user.id, gacha_data, num, user)
        save_user_info()
        await msg.reply([(await build_gacha_card(img_list, bot)).build()])

    @bot.my_command(name='show_log', aliases=['模拟抽卡记录', '查看模拟抽卡记录'],
                    introduce='查看在小派蒙这边的模拟抽卡记录', usage='!!模拟抽卡记录', group=[CommandGroups.GAME])
    async def show_log(msg: Message, show_type: str = None):
        res_card = Card(color=NamedColor.AQUA)
        uid = msg.author.id
        init_user_info(uid)
        if user_info[uid]['gacha_list']['wish_total'] == 0:
            await msg.reply('你此前并没有抽过卡哦')
            return
        if show_type == '角色' or show_type == '武器':
            res_card = get_rw_record(show_type, uid)
        else:
            data = user_info[uid]['gacha_list']
            res = '你的模拟抽卡记录如下:\n'
            res_card.append(Header('你的模拟抽卡记录如下:'))
            res += '你在本频道总共抽卡 %s 次\n其中五星共 %s 个,四星共 %s 个\n' % (
                user_info[uid]['gacha_list']['wish_total'], user_info[uid]['gacha_list']['wish_5'],
                user_info[uid]['gacha_list']['wish_4'])
            res_card.append(
                Section(Kmarkdown(f'你在本频道总共抽卡 **{user_info[uid]["gacha_list"]["wish_total"]}** 次')))
            res_card.append(Section(Kmarkdown(
                f'其中五星共 **{user_info[uid]["gacha_list"]["wish_5"]}** 个,四星共 **{user_info[uid]["gacha_list"]["wish_4"]}** 个')))
            res_card.append(Divider())
            try:
                t5 = '{:.2f}%'.format(data['wish_5'] / (
                        data['wish_total'] - data['gacha_5_role'] - data['gacha_5_weapon'] - data[
                    'gacha_5_permanent']) * 100)
            except:
                t5 = '0.00%'
            try:
                u5 = '{:.2f}%'.format(data['wish_5_up'] / data['wish_5'] * 100)
            except:
                u5 = '0.00%'
            try:
                t4 = '{:.2f}%'.format(data['wish_4'] / (
                        data['wish_total'] - data['gacha_4_role'] - data['gacha_4_weapon'] - data[
                    'gacha_4_permanent']) * 100)
            except:
                t4 = '0.00%'
            try:
                u4 = '{:.2f}%'.format(data['wish_4_up'] / data['wish_4'] * 100)
            except:
                u4 = '0.00%'
            dg_name = data['dg_name'] if data['dg_name'] != '' else '未定轨'
            res += '五星出货率为 %s  up率为 %s \n四星出货率为 %s  up率为 %s \n' % (t5, u5, t4, u4)
            res_card.append(Section(
                Kmarkdown(f'五星出货率为 **{t5}**, up率为 **{u5}** \n四星出货率为 **{t4}**, up率为 **{u4}**\n---')))
            res += '·|角色池|·\n目前 %s 抽未出五星  %s 抽未出四星\n下次五星是否up: %s \n' % (
                data['gacha_5_role'], data['gacha_4_role'], data['is_up_5_role'])
            res_card.append(Header('角色池'))
            res_card.append(Section(Kmarkdown(
                f'目前 **{data["gacha_5_role"]}** 抽未出五星, **{data["gacha_4_role"]}** 抽未出四星\n下次五星是否up: **{"是" if data["is_up_5_role"] else "否"}**')))
            res_card.append(Divider())
            res += '·|武器池|·\n目前 %s 抽未出五星  %s 抽未出四星\n下次五星是否up: %s \n' % (
                data['gacha_5_weapon'], data['gacha_4_weapon'], data['is_up_5_weapon'])
            res_card.append(Header('武器池'))
            res_card.append(Section(Kmarkdown(
                f'目前 **{data["gacha_5_weapon"]}** 抽未出五星, **{data["gacha_4_weapon"]}** 抽未出四星\n下次五星是否up: **{"是" if data["is_up_5_weapon"] else "否"}**')))
            res += '定轨武器为 %s ,能量值为 %s \n' % (dg_name, data['dg_time'])
            res_card.append(Section(Kmarkdown(f'定轨武器为 **{dg_name}** ,能量值为 **{data["dg_time"]}**')))
            res_card.append(Divider())
            res += '·|常驻池|·\n目前 %s 抽未出五星  %s 抽未出四星\n' % (
                data['gacha_5_permanent'], data['gacha_4_permanent'])
            res_card.append(Header('常驻池'))
            res_card.append(Section(Kmarkdown(
                f'目前 **{data["gacha_5_permanent"]}** 抽未出五星, **{data["gacha_4_permanent"]}** 抽未出四星')))

        await msg.reply([res_card.build()])

    @bot.my_command(name='delete_log', aliases=['删除模拟抽卡记录'], usage='!!删除模拟抽卡记录',
                    introduce='删除你在小派蒙这里模拟抽卡的记录', group=[CommandGroups.GAME])
    async def delete_log(msg: Message):
        uid = msg.author.id
        init_user_info(uid)
        try:
            del user_info[uid]
            save_user_info()
            await msg.reply('你的抽卡记录删除成功')
        except:
            await msg.reply('你的抽卡记录删除失败')

    @bot.my_command(name='choose_dg', aliases=['选择定轨'], usage='!!选择定轨 [武器]', introduce='选择模拟抽卡的定轨',
                    group=[CommandGroups.GAME])
    async def choose_dg(msg: Message, *args):
        uid = msg.author.id
        if len(args) == 1:
            dg_weapon = args[0]
            weapon_up_list = await get_dg_weapon()
            if dg_weapon not in weapon_up_list:
                await msg.reply(f'该武器无定轨，请输入全称[{weapon_up_list[0]}|{weapon_up_list[1]}]')
            else:
                if dg_weapon == user_info[uid]['gacha_list']['dg_name']:
                    await msg.reply('你当前已经定轨该武器，无需更改')
                else:
                    user_info[uid]['gacha_list']['dg_name'] = dg_weapon
                    user_info[uid]['gacha_list']['dg_time'] = 0
                    save_user_info()
                    await msg.reply(f'定轨成功，定轨能量值已重置，当前定轨武器为：{dg_weapon}')
        else:
            await msg.reply('缺少参数 武器')

    @bot.my_command(name='delete_dg', aliases=['删除定轨'], usage='!!删除定轨',
                    introduce='删除你在小派蒙这里模拟抽卡的定轨', group=[CommandGroups.GAME])
    async def delete_dg(msg: Message):
        uid = msg.author.id
        init_user_info(uid)
        if user_info[uid]['gacha_list']['dg_name'] == '':
            await msg.reply('你此前并没有定轨记录哦')
        else:
            user_info[uid]['gacha_list']['dg_name'] = ''
            user_info[uid]['gacha_list']['dg_time'] = 0
            save_user_info()
            await msg.reply('你的定轨记录删除成功')

    @bot.my_command(name='show_dg', aliases=['显示定轨'], usage='!!显示定轨',
                    introduce='查看你在小派蒙这里模拟抽卡的定轨', group=[CommandGroups.GAME])
    async def show_dg(msg: Message):
        uid = msg.author.id
        init_user_info(uid)
        weapon_up_list = await get_dg_weapon()
        dg_weapon = user_info[uid]['gacha_list']['dg_name']
        dg_time = user_info[uid]['gacha_list']['dg_time']
        if dg_weapon == '':
            await msg.reply(
                f'你当前未定轨武器，可定轨武器有 {weapon_up_list[0]}|{weapon_up_list[1]} ，请使用[选择定轨 武器全称]来进行定轨')
        else:
            await msg.reply(f'你当前定轨的武器为 {dg_weapon} ，能量值为 {dg_time}')


def gacha_type_by_name(gacha_type):
    # if re.match(r'^角色1|限定1|角色2|限定2(?:池)$', gacha_type):
    #     return 301
    if re.match(r'^角色1|限定1(?:池)$', gacha_type):
        return 301
    if re.match(r'^角色2|限定2(?:池)$', gacha_type):
        return 400
    if re.match(r'^武器|武器池$', gacha_type):
        return 302
    if re.match(r'^常驻|普(?:池)$', gacha_type):
        return 200
    # if re.match(r'^新角色1|新限定1|新角色2|新限定2(?:池)$', gacha_type):
    #     return 'role_1_pool'
    if re.match(r'^彩蛋池?$', gacha_type):
        return 'all_star'
    # if re.match(r'^新角色1|新限定1(?:池)$', gacha_type):
    #     return 'role_1_pool'
    # if re.match(r'^新角色2|新限定2(?:池)$', gacha_type):
    #     return 'role_2_pool'
    if re.match(r'^新武器|新武器池$', gacha_type):
        return 'weapon_pool'
    return 0


def get_rw_record(msg, uid):
    card = Card(color=NamedColor.AQUA)
    if msg == '角色':
        if not len(user_info[uid]['role_list']):
            res = '你还没有角色'
            card.append(Section(Kmarkdown('你还没有角色')))
        else:
            res = '你所拥有的角色如下:\n'
            card.append(Header('你所拥有的角色如下:'))
            for role in user_info[uid]['role_list'].items():
                if len(role[1]['星级']) == 5:
                    res += '%s%s 数量: %s 出货: %s\n' % (role[1]['星级'], role[0], role[1]['数量'], role[1]['出货'])
                    card.append(Section(Kmarkdown(
                        f'{role[1]["星级"]}{role[0]} 数量: **{role[1]["数量"]}** 出货: **{role[1]["出货"]}**')))
                else:
                    res += '%s%s 数量: %s\n' % (role[1]['星级'], role[0], role[1]['数量'])
                    card.append(Section(Kmarkdown(f'{role[1]["星级"]}{role[0]} 数量: **{role[1]["数量"]}**')))
    else:
        if not len(user_info[uid]['weapon_list']):
            res = '你还没有武器'
            card.append(Section(Kmarkdown('你还没有武器')))
        else:
            res = '你所拥有的武器如下:\n'
            card.append(Header('你所拥有的武器如下:'))
            for wp in user_info[uid]['weapon_list'].items():
                if len(wp[1]['星级']) == 5:
                    res += '%s%s 数量: %s 出货: %s\n' % (wp[1]['星级'], wp[0], wp[1]['数量'], wp[1]['出货'])
                    card.append(
                        Section(Kmarkdown(f'{wp[1]["星级"]}{wp[0]} 数量: {wp[1]["数量"]} 出货: {wp[1]["出货"]}')))
                else:
                    res += '%s%s 数量: %s\n' % (wp[1]['星级'], wp[0], wp[1]['数量'])
                    card.append(Section(Kmarkdown(f'{wp[1]["星级"]}{wp[0]} 数量: {wp[1]["数量"]}')))
    return card


async def get_dg_weapon():
    weapon_up_list = []
    data = await gacha_info_list()
    f = lambda x: x['gacha_type'] == 302
    gacha_data = sorted(list(filter(f, data)), key=lambda x: x['end_time'])[-1]
    gacha_id = gacha_data['gacha_id']
    gacha_data = await gacha_info(gacha_id)
    for weapon in gacha_data['r5_up_items']:
        weapon_up_list.append(weapon['item_name'])
    return weapon_up_list


async def gacha_info_list():
    res = await requests.get(url=BASE_URL % 'gacha/list.json')
    return json.loads(res)['data']['list']


async def gacha_info(gacha_id):
    res = await requests.get(url=BASE_URL % gacha_id + '/zh-cn.json')
    return json.loads(res)


async def build_gacha_card(img_list, bot: 'LittlePaimonBot'):
    images = []
    for img in img_list:
        img.convert("RGBA")
        img.save(TEMP_PATH / 'gacha.png')
        url = await bot.create_asset((TEMP_PATH / 'gacha.png').__str__())
        images.append(Image(url))
    return Card(Container(*images))
