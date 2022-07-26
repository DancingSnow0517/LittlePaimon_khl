import json
from pathlib import Path
from typing import Union

import httpx
import tqdm.asyncio


def load_json(path: Union[Path, str], encoding: str = 'utf-8') -> dict:
    """
    说明：
        读取本地json文件，返回json字典。
    参数：
        :param path: 文件路径
        :param encoding: 编码，默认为utf-8
        :return: json字典
    """
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        save_json({}, path, encoding)
    return json.load(path.open('r', encoding=encoding))


def save_json(data: dict, path: Union[Path, str] = None, encoding: str = 'utf-8'):
    """
    保存json文件
    :param data: json数据
    :param path: 保存路径
    :param encoding: 编码
    """
    if isinstance(path, str):
        path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, path.open('w', encoding=encoding), ensure_ascii=False, indent=4)


async def download(url: str, save_path: Path):
    """
    下载文件(带进度条)
    :param url: url
    :param save_path: 保存路径
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient().stream(method='GET', url=url, follow_redirects=True) as datas:
        size = int(datas.headers['Content-Length'])
        f = save_path.open('wb')
        async for chunk in tqdm.asyncio.tqdm(iterable=datas.aiter_bytes(1),
                                             desc=url.split('/')[-1],
                                             unit='iB',
                                             unit_scale=True,
                                             unit_divisor=1024,
                                             total=size,
                                             colour='green'):
            f.write(chunk)
        f.close()
