import json
import logging
import random
from typing import List, TYPE_CHECKING

from khl import Message, MessageTypes
from khl.command import Rule
from khl_card.card import Card
from khl_card.modules import *
from khl_card.types import ThemeTypes

from utils import requests
from utils.message_util import MessageBuilder

if TYPE_CHECKING:
    from main import LittlePaimonBot

voice_list: dict = {}

log = logging.getLogger(__name__)


def create_matcher(bot: 'LittlePaimonBot', chat_word: str, pattern: str, cooldown: int, pro: float,
                   responses: List[str]):
    @bot.command(name=chat_word, regex=pattern, prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def handler(msg: Message, *args):
        response = random.choice(responses)
        if response.endswith('.mp3'):
            url = await MessageBuilder.static_record(bot, f'LittlePaimon/voice/{response}')
            card = Card(Audio(url, '', ''), theme=ThemeTypes.NONE)
            await msg.reply([card.build()])
        elif response.endswith(('png', '.jpg', '.image', '.gif')):
            url = await MessageBuilder.static_image(bot, f'LittlePaimon/voice/{response}')
            if url is not None:
                await msg.reply(url, type=MessageTypes.IMG)
        elif response.endswith(('mp4', '.avi')):
            ...
        else:
            await msg.reply(response)


async def on_startup(bot: 'LittlePaimonBot'):
    global voice_list
    data = await requests.get('https://static.cherishmoon.fun/LittlePaimon/voice/voice_list.json')
    if not isinstance(data, dict):
        raise Exception('派蒙语音更新失败')
    with open(bot.config.data_path + '/voice_list.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    voice_list = data
    for k, v in voice_list.items():
        create_matcher(bot, k, v['pattern'], v['cooldown'], v['pro'], v['files'])
