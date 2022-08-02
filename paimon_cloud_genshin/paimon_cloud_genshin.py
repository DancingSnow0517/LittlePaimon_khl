import json
import logging
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Dict

from khl import Message, EventTypes, Event
from khl_card.accessory import Button, PlainText, Kmarkdown
from khl_card.card import Card
from khl_card.modules import ActionGroup, Header, Section
from khl_card.types import ThemeTypes
from littlepaimon_utils.files import load_json, save_json

from paimon_cloud_genshin.data_source import get_Info, check_token, get_Notification
from utils.api import CommandGroups

if TYPE_CHECKING:
    from bot import LittlePaimonBot

uu = str(uuid.uuid4())

log = logging.getLogger(__name__)

wait_to_rm: Dict[str, bool] = {}


async def on_startup(bot: 'LittlePaimonBot'):
    @bot.task.add_cron(hour=6, timezone='Asia/Shanghai')
    async def auto_sign_cgn():
        data = load_json(Path() / 'data' / 'LittlePaimon' / 'CloudGenshin.json')

        for user in data:
            token = data[user]['token']
            uuid = data[user]['uuid']

            if await check_token(uuid, token):
                """ 获取免费时间 """
                d2 = await get_Info(uuid, token)
                """ 解析签到返回信息 """
                if d2['data']['free_time']['free_time'] == data[user]['limit']:
                    await (await bot.fetch_user(user)).send('免费签到时长已达上限,无法继续签到')
                else:
                    """ 取云原神签到信息 """
                    d1 = await get_Notification(uuid, token)
                    if not list(d1['data']['list']):
                        log.info(f'UID{data[user]["uid"]} 已经签到云原神')
                    else:
                        signInfo = json.loads(d1['data']['list'][0]['msg'])
                        if signInfo:
                            await (await bot.fetch_user(user)).send(
                                f'签到成功~ {signInfo["msg"]}: {signInfo["num"]}分钟')
                        else:
                            return
            else:
                await (await bot.fetch_user(user)).send('token已过期,请重新自行抓包并重新绑定')

    @bot.my_command(name='cloud_ys', aliases=['云原神', 'yys'], usage='使用 `!!云原神` 查看具体使用方法',
                    introduce='云原神相关命令', group=[CommandGroups.CLOUD_GENSHIN])
    async def cloud_ys(msg: Message, *args):
        user_id = msg.author.id
        data = load_json(Path() / 'data' / 'LittlePaimon' / 'CloudGenshin.json')

        if len(args) == 0:
            card = Card(
                Header(f'亲爱的旅行者: {user_id}'),
                Section(Kmarkdown('**本命令的食用方法：**')),
                Section(Kmarkdown('**云原神|yys** [绑定] 绑定云原神的 `token` 到你的 `kook` 账户上 ')),
                Section(Kmarkdown('**云原神|yys** [信息] 查询云原神账户信息')),
                Section(Kmarkdown('有关如何抓取 `token` 的方法:'),
                        accessory=Button(text=PlainText('访问'), value='https://blog.ethreal.cn/archives/yysgettoken',
                                         click='link'))
            )
            message = f'亲爱的旅行者: {user_id}\n\n' \
                      '本插件食用方法:\n' \
                      '<云原神/yys> [绑定/bind] 绑定云原神token\n' \
                      '<云原神/yys> [信息/info] 查询云原神账户信息\n\n' \
                      '<yys[解绑/解除绑定/del]> 解绑token并取消自动签到\n\n' \
                      '有关如何抓取token的方法:\n' \
                      '请前往 https://blog.ethreal.cn/archives/yysgettoken 查阅'
            await msg.reply([card.build()])
        elif args[0] in ['绑定', 'bind']:
            token = " ".join(args[1:-1])

            data[user_id] = {
                'uid': user_id,
                'uuid': uu,
                'limit': 600,
                'isFullTime': False,
                'token': token
            }

            save_json(data=data, path=Path() / 'data' / 'LittlePaimon' / 'CloudGenshin.json')
            await msg.reply(f'[UID:{user_id}]已绑定token, 将在每天6点为你自动签到!')
        elif args[0] in ['信息', 'info']:
            if user_id not in data:
                await msg.reply('你还没有在小派蒙这里绑定云原神token')
                return
            token = data[user_id]['token']
            user_id = data[user_id]['uid']
            uuid = data[user_id]['uuid']

            result = await get_Info(uuid, token)

            print(result)

            """ 米云币 """
            coins = result['data']['coin']['coin_num']
            """ 免费时间 """
            free_time = result['data']['free_time']['free_time']
            """ 畅玩卡 """
            card = result['data']['play_card']['short_msg']

            message = '======== UID: {0} ========\n' \
                      '剩余米云币: {1}\n' \
                      '剩余免费时间: {2}分钟\n' \
                      '畅玩卡状态: {3}'.format(user_id, coins, free_time, card)
            await msg.reply(message)

    @bot.my_command(name='rm_cloud_ys', aliases=['云原神解绑', 'yys解绑', 'yys解除绑定', 'yysdel'],
                    usage='!!云原神解绑', introduce='解除你的云原神与kook的绑定', group=[CommandGroups.CLOUD_GENSHIN])
    async def rm_cloud_ys(msg: Message):
        card = Card(
            Header('是否要解绑token并取消自动签到？'),
            ActionGroup(
                Button(PlainText('YES'), click='return-val', value='rm_cloud_ys_yes', theme='danger'),
                Button(PlainText('NO'), click='return-val', value='rm_cloud_ys_no', theme='success')
            ),
            theme=ThemeTypes.DANGER
        )
        wait_to_rm[msg.author.id] = True
        await msg.reply([card.build()])

    @bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
    async def choice(_: 'LittlePaimonBot', event: Event):
        value = event.body['value']
        user_id = event.body['user_id']
        if user_id not in wait_to_rm:
            return
        if wait_to_rm[user_id]:
            if value == 'rm_cloud_ys_yes':
                wait_to_rm[user_id] = False
                data = load_json(Path() / 'data' / 'LittlePaimon' / 'CloudGenshin.json')
                if user_id not in data:
                    await (await bot.fetch_user(user_id)).send('你还没有在小派蒙这里绑定云原神token')
                    return
                del data[user_id]
                save_json(data, Path() / 'data' / 'LittlePaimon' / 'CloudGenshin.json')
                await (await bot.fetch_user(user_id)).send('token已解绑并取消自动签到~')
            elif value == 'rm_cloud_ys_no':
                wait_to_rm[user_id] = False
            else:
                wait_to_rm[user_id] = False
