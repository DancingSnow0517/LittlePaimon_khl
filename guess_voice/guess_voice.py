import asyncio
import json
import random
import time
from pathlib import Path
from typing import TYPE_CHECKING, Literal, List, Dict, Tuple

from khl import Message, Channel, User, MessageTypes
from khl_card.accessory import *
from khl_card.card import Card
from khl_card.modules import Header, Countdown, Audio, Section
from khl_card.types import ThemeTypes
from littlepaimon_utils.files import load_json

from . import download_data

if TYPE_CHECKING:
    from main import LittlePaimonBot

guess_games: Dict[str, 'GuessVoice'] = {}
voice_data: dict

languages = Literal['中', '日', '英', '韩']

char_alias = load_json(Path() / 'utils' / 'json_data' / 'alias.json')

# 以防同时回答
guess_lock = asyncio.Lock()


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
    global guess_games
    await update(bot.config.data_path)

    @bot.my_command(name='update_voice', aliases=['更新原神语音资源'], usage='更新原神语音资源',
                    introduce='更新原神猜语言游戏的语音资源')
    async def update_voice(msg: Message):
        await update(bot.config.data_path)
        await msg.reply('游戏语音资源更新成功')

    @bot.my_command(name='guess_game', aliases=['原神猜语音'], usage='原神猜语音 [游戏时间] [语言]', introduce='开始原神猜语音游戏')
    async def guess_game(msg: Message, *args: str):
        global guess_games
        if msg.ctx.channel.id in guess_games:
            game = guess_games.get(msg.ctx.channel.id)
        else:
            game = GuessVoice(bot, msg)
            guess_games[msg.ctx.channel.id] = game
        if len(args) == 0:
            game_time = 120
            lang = '中'
        else:
            if args[0].isdigit():
                game_time = int(args[0])
            else:
                await msg.reply('`游戏时间` 必须为数字，单位秒', type=MessageTypes.KMD)
                return
            if len(args) == 1:
                lang = '中'
            elif args[1] in ['中', '日', '英', '韩']:
                lang = args[1]
            else:
                await msg.reply('`语言` 可以为 `中`, `日`, `英`, `韩`', type=MessageTypes.KMD)
        await game.start(game_time, lang)

    role_map = {}
    for i in char_alias['roles']:
        t = char_alias['roles'][i]
        for n in t:
            role_map[n] = t[0]

    @bot.command(name='guess', prefixes=[''], aliases=list(role_map.keys()))
    async def guess(msg: Message):
        await guess_lock.acquire()
        game = guess_games.get(msg.ctx.channel.id, None)
        if game is None:
            guess_lock.release()
            return

        if game.statu:
            char = role_map[msg.content]
            if char == '空' or char == '荧':
                char = '旅行者'
            if char == game.info.char:
                await msg.reply('恭喜你，答对了')
                await game.add_score(msg.author)
                await game.next()
        guess_lock.release()


class GuessInfo:

    def __init__(self, url: str, char: str, language: str, text: str) -> None:
        self.url = url
        self.char = char
        self.language = language
        self.text = text

    async def send(self, channel: Channel, game: 'GuessVoice'):
        card = Card(Audio(self.url, f'第 {game.count} 题', ''), theme=ThemeTypes.NONE)
        await channel.send([card.build()])
        print(self)

    def __str__(self) -> str:
        return f"当前角色: {self.char}"


class GuessVoice:
    bot: 'LittlePaimonBot'
    statu: bool = False

    language: str = '中'
    time: int = 30
    count: int = 0

    info: GuessInfo
    score: Dict[str, int] = {}
    channel: Channel

    def __init__(self, bot: 'LittlePaimonBot', msg: Message) -> None:
        self.bot = bot
        self.channel = msg.ctx.channel

    async def start(self, game_time: int = 30, language: languages = '中') -> None:
        if self.statu:
            await self.channel.send('原神猜语音游戏已经开始了')
        else:
            await self.channel.send(f'正在开始原神猜语音游戏\n时间: **{game_time}** s 语言: **{language}**\n直接在频道输入角色名字视为答题', type=MessageTypes.KMD)
            await self.channel.send([Card(Header('游戏倒计时：'), Countdown(int(time.time() * 1000 + game_time * 1000), mode='second', starttime=int(time.time() * 1000))).build()])
            self.statu = True
            self.time = game_time
            self.language = language
            self.score = {}
            self.count = 0
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
            Section(
                Paragraph(3, [Kmarkdown('\n'.join(ranks)), Kmarkdown('\n'.join(users)), Kmarkdown('\n'.join(scores))]))
        )
