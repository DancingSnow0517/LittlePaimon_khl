from pathlib import Path
from typing import TYPE_CHECKING

from khl import Message, MessageTypes

from paimon_calendar.generate import generate_day_schedule
from utils.api import CommandGroups

if TYPE_CHECKING:
    from bot import LittlePaimonBot


async def on_startup(bot: 'LittlePaimonBot'):
    @bot.my_command(name='calendar', aliases=['原神日历', '原神日程', 'ysrl', 'ysrc'], introduce='查看原神活动日历',
                    usage='!!原神日历', group=[CommandGroups.INFO])
    async def calendar(msg: Message):
        server = 'cn'
        im = await generate_day_schedule(server)
        (Path() / 'Temp' / 'calendar.png').write_bytes(im)
        await msg.reply(await bot.create_asset('Temp/calendar.png'), type=MessageTypes.IMG)
