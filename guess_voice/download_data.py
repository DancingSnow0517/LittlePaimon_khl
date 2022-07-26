import logging
import os
from pathlib import Path
from typing import Dict, List, Union

from aiohttp import InvalidURL
from bs4 import BeautifulSoup

from utils import requests

BASE_URL = 'https://wiki.biligame.com/ys/'
API = {'character_list': '角色', 'voice': '%s语音'}

languages = ['中', '日', '英']

log = logging.getLogger(__name__)


async def get_character_list():
    html = await requests.get(BASE_URL + API['character_list'])
    soup = BeautifulSoup(html, 'lxml')
    char_list = soup.find(attrs={
        'class': 'resp-tab-content',
        'style': 'display:block;'
    })
    char_list1 = char_list.find_all(attrs={'class': 'g C5星'})
    res = list(set(map(lambda x: x.find('div', class_='L').text, char_list1)))
    char_list2 = char_list.find_all(attrs={'class': 'g C5'})
    res.extend(list(set(map(lambda x: x.find('div', class_='L').text, char_list2))))
    char_list3 = char_list.find_all(attrs={'class': 'g C4星'})
    res.extend(list(set(map(lambda x: x.find('div', class_='L').text, char_list3))))
    res.sort()
    return res


async def get_voice_info(character_name: str):
    log.info('获取数据: %s' % character_name)
    html = await requests.get(url=(BASE_URL + API['voice'] % character_name))
    soup = BeautifulSoup(html, 'lxml')
    if soup.find(text='本页面目前没有内容。您可以在其他页面中'):
        return None
    voice_list = soup.find_all(attrs={'class': 'visible-md'})[2:]
    info_list = []
    for item in voice_list:
        item_tab = item.find_all(attrs={'class': ''})[1:]
        if isinstance(item_tab[1].next, str):
            return info_list
        info_list.append({
            'title': item_tab[0].text,
            'text': item_tab[5].text,
            '中': item_tab[1].next.attrs.get('data-src', ''),
            '日': item_tab[2].next.attrs.get('data-src', ''),
            '英': item_tab[3].next.attrs.get('data-src', ''),
            '韩': item_tab[4].next.attrs.get('data-src', ''),
        })
    return info_list


async def download(url, path):
    voice = await requests.get_voice(url)
    if voice is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_bytes(voice)
    except FileNotFoundError:
        return


async def update_voice_data(data_path: Union) -> Dict[str, List[Dict[str, str]]]:
    data_path = Path(data_path)
    voice_data: Dict[str, List[Dict[str, str]]] = {}
    char_list = await get_character_list()
    for char in char_list:
        info = await get_voice_info(char)
        if not info:
            continue
        voice_data[char] = info
        counter = 0
        for voice in info:
            counter += 1
            for language in languages:
                voice_url = voice[language]
                path = data_path / 'voices' / char / language
                path.parent.mkdir(parents=True, exist_ok=True)
                out_path = path / (str(counter) + '.ogg')
                mp3_path = path / (str(counter) + '.mp3')
                if not mp3_path.exists():
                    try:
                        await download(voice_url, out_path)
                        ogg_to_mp3(out_path, mp3_path)
                    except InvalidURL as _:
                        ...

    return voice_data


def ogg_to_mp3(ogg: Path, mp3: Path):
    os.system(f'ffmpeg -i {ogg} -acodec libmp3lame {mp3} -loglevel quiet')
    os.remove(ogg)
