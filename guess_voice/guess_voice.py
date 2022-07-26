import asyncio
import json
import random
from pathlib import Path
from typing import TYPE_CHECKING, Literal, List, Dict, Tuple

from khl import Message, Channel, User
from khl.command import Rule
from khl_card.accessory import *
from khl_card.card import Card
from khl_card.modules import *
from khl_card.types import ThemeTypes

from . import download_data

if TYPE_CHECKING:
    from main import LittlePaimonBot

guess_main: 'GuessVoice'
voice_data: dict


# 获取原神语音
async def update(data_path) -> dict:
    """
    下载原神语音，并返回数据
    :param data_path: 数据路径
    :return: 获得到的数据
    """
    global voice_data
    voice_data = await download_data.update_voice_data(data_path)
    with open(data_path + '/voice_data.json', 'w', encoding='utf-8') as f:
        json.dump(voice_data, f, ensure_ascii=False, indent=4)
    return voice_data


# 当 bot 启动后
async def on_startup(bot: 'LittlePaimonBot'):
    global guess_main
    await update(bot.config.data_path)

    # 初始化游戏
    guess_main = GuessVoice(bot)

    @bot.command(name='update_voice', aliases=['更新原神语音资源'], prefixes=[''], rules=[Rule.is_bot_mentioned(bot)])
    async def update_voice(_: Message):
        await update(bot.config.data_path)

    @bot.command(name='guess_game', aliases=['原神猜语音'], prefixes=['!', '！'])
    async def guess_game(msg: Message):
        await guess_main.start(msg, 120)

    @bot.command(name='guess', prefixes=[''], aliases=[i for i in voice_data])
    async def guess(msg: Message):
        print(guess_main.statu)
        print(msg.content)
        print(guess_main.info.char)
        if guess_main.statu:
            char = msg.content
            if char == guess_main.info.char:
                await msg.reply('恭喜你，答对了')
                await guess_main.add_score(msg.author)
                await guess_main.next()


class GuessInfo:

    def __init__(self, url: str, char: str, language: str, text: str) -> None:
        self.url = url
        self.char = char
        self.language = language
        self.text = text

    async def send(self, channel: Channel, game: 'GuessVoice'):
        card = Card(Audio(self.url, f'第 {game.count} 题', ''), theme=ThemeTypes.NONE)
        print(card.build())
        await channel.send([card.build()])

    def __str__(self) -> str:
        return f"{self.char}: {self.text}"


class GuessVoice:
    bot: 'LittlePaimonBot'
    statu: bool = False

    language: str = '中'
    time: int = 30
    count: int = 0

    info: GuessInfo
    score: Dict[str, int] = {}
    channel: Channel

    def __init__(self, bot: 'LittlePaimonBot', language: Literal['中', '日', '英', '韩'] = '中') -> None:
        self.bot = bot
        self.language = language

    async def start(self, msg: Message, time: int = 30) -> None:
        if self.statu:
            await msg.reply('原神猜语音游戏已经开始了')
        else:
            await msg.reply('正在开始原神猜语音游戏')
            self.channel = msg.ctx.channel
            self.statu = True
            self.time = time
            self.score = {}
            self.count = 1
            self.info = await self.get_random_voice()
            await self.info.send(self.channel, self)

            await asyncio.sleep(self.time)

            await self.stop()

    async def stop(self):
        if self.statu:
            await self.channel.send('游戏结束！')
            await self.channel.send([self.get_rank_card().build()])
            self.statu = False
        else:
            await self.channel.send('游戏都还没开始')

    async def next(self):
        self.info = await self.get_random_voice()
        await self.info.send(self.channel, self)

    async def get_random_voice(self) -> GuessInfo:
        voice_path = Path(self.bot.config.data_path) / 'voices'
        char = random.sample(voice_data.keys(), 1)[0]
        voice = random.randint(1, len(voice_data[char]))
        # chars = os.listdir(voice_path)  # type: List[str]
        # char = random.choice(chars)
        # voices = os.listdir(voice_path / char / self.language)  # type: List[str]
        # voice = random.choice(voices)
        try:
            url = await self.bot.create_asset((voice_path / char / self.language / (str(voice) + '.mp3')).__str__())
        except FileNotFoundError:
            return await self.get_random_voice()
        self.count += 1
        return GuessInfo(url, char, self.language, str(voice) + '.mp3')

    async def add_score(self, user: User):
        name = user.nickname
        if name in self.score:
            self.score[name] += 1
        else:
            self.score[name] = 1

    def get_rank_card(self) -> Card:
        ranks: List[str] = ['**排名**']
        users: List[str] = ['**玩家**']
        scores: List[str] = ['**分数**']
        sorted_data = sorted(self.score.items(), key=lambda kv: kv[1], reverse=True)  # type: List[Tuple[str, int]]
        counter = 0
        for i in sorted_data:
            counter += 1
            ranks.append('#' + str(counter))
            users.append(i[0])
            scores.append(str(i[1]))

        return Card(
            Header('原神猜语音 排名：'),
            Section(Paragraph(3, [Kmarkdown('\n'.join(ranks)), Kmarkdown('\n'.join(users)), Kmarkdown('\n'.join(scores))]))
        )
