from pathlib import Path
from typing import TYPE_CHECKING

from khl import Message, MessageTypes

from paimon_calendar.generate import generate_day_schedule

if TYPE_CHECKING:
    from main import LittlePaimonBot


async def on_startup(bot: 'LittlePaimonBot'):
    @bot.my_command(name='calendar')
    async def calendar(msg: Message, _):
        server = 'cn'
        im = await generate_day_schedule(server)
        (Path() / 'Temp' / 'calendar.png').write_bytes(im)
        await msg.reply(await bot.create_asset('Temp/calendar.png'), type=MessageTypes.IMG)
