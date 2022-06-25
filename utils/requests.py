import json
from io import BytesIO
from json import JSONDecodeError
from pathlib import Path

import aiohttp

from typing import Union, Optional, Dict

from yarl import URL

from PIL import Image


async def req(method: str, url: Union[str, URL], **kwargs) -> Union[str, dict, None]:
    async with aiohttp.ClientSession() as client:
        try:
            async with client.request(method, url, **kwargs) as response:
                data = await response.text()
                try:
                    return json.loads(data)
                except JSONDecodeError:
                    return data
        except TimeoutError as e:
            return None


async def get(url: Union[str, URL], **kwargs) -> Union[str, dict, None]:
    return await req('GET', url, **kwargs)


async def post(url: Union[str, URL], **kwargs) -> Union[str, dict, None]:
    return await req('POST', url, **kwargs)


async def get_image(url: str, *, headers: Optional[Dict[str, str]] = None,
                    save_path: Optional[Union[str, Path]] = None):
    if save_path and Path(save_path).exists():
        image = Image.open(save_path)
    else:
        async with aiohttp.ClientSession() as client:
            try:
                async with client.get(url) as response:
                    res = await response.read()
                    image = Image.open(BytesIO(res))
            except:
                return None
    if save_path and not Path(save_path).exists():
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(save_path)
    return image


async def get_voice(url: str) -> Optional[bytes]:
    async with aiohttp.ClientSession() as client:
        try:
            async with client.get(url) as response:
                return await response.content.read()
        except TimeoutError:
            return None
