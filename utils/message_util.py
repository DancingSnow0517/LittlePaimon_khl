import pathlib
import time
from io import BytesIO
from typing import Optional, TYPE_CHECKING

from PIL import Image

from utils import requests

if TYPE_CHECKING:
    from main import LittlePaimonBot


class MessageBuilder:

    @staticmethod
    async def static_image(bot: 'LittlePaimonBot', url: str, quality: Optional[int] = 100,
                           is_check_time: Optional[bool] = True,
                           check_time_day: Optional[int] = 3) -> Optional[str]:
        """
        从url下载图片，并预处理并构造成 KHL_Message ，如果url的图片已存在本地，则直接读取本地图片
        :param bot: 开黑啦机器人
        :param url: 图片 url
        :param quality: 预处理图片质量
        :param is_check_time: 是否检查本地图片最后修改时间
        :param check_time_day: 检查本地图片最后修改时间的天数，超过该天数则重新下载图片
        :return: 开黑啦图片 url
        """
        path = pathlib.Path(f'{bot.config.data_path}/{url}')
        if path.exists() and (
                not is_check_time or (is_check_time and not check_time(path.stat().st_mtime, check_time_day))):
            image = Image.open(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            image = await requests.get_image(url='https://static.cherishmoon.fun/' + url, save_path=path)
            if image is None:
                return None
        bio = BytesIO()
        image.save(bio, format='JPEG' if image.mode == 'RGB' else 'PNG', quality=quality)
        return await bot.create_asset(bio)

    @staticmethod
    async def static_record(bot: 'LittlePaimonBot', url: str):
        """
        从url中下载音频文件，并构造成 KHL_Message，如果本地已有该音频文件，则直接读取本地文件
        :param bot: 开黑啦机器人
        :param url: 音频 url
        :return: 开黑啦音频 url
        """
        path = pathlib.Path(f'{bot.config.data_path}/{url}')
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(await requests.get_voice('https://static.cherishmoon.fun/' + url))
        return await bot.create_asset(f'{bot.config.data_path}/{url}')


def check_time(time_stamp, day=1) -> bool:
    return (time.time() - time_stamp) / 86400 > day
