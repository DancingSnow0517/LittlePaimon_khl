from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import LittlePaimonBot


async def on_startup(bot: 'LittlePaimonBot'):
    ...
