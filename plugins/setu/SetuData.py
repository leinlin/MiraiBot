import json
import asyncio
import aiohttp
import requests
import PIL.Image
import base64
import hashlib
from io import BytesIO
from pathlib import Path
from typing import List, Set
from datetime import datetime, timedelta
from pydantic import BaseModel, validator, ValidationError
from urllib.parse import urlparse
from mirai.logger import Event as EventLogger
from config import data_path, setu_apikey, setu_proxy, setu_r18

Path(data_path).mkdir(exist_ok=True)
SAVE_FILE = Path(data_path).joinpath('setu.json')

class SetuUrlData(BaseModel):
    regular: str

    @property
    def purl(self) -> str:
        return 'https://www.pixiv.net/artworks/{}'.format(Path(urlparse(self.regular).path).stem.split('_')[0])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.regular == other.regular
        else:
            return False

    def __hash__(self):
        return hash(self.regular)

    def save(self) -> None:
        """保存至文件"""
        SetuDatabase.save(self)

    async def get(self, check_size: bool = True) -> bytes:
        """从网络获取图像"""
        try:
            headers = {'Referer': 'https://www.pixiv.net/'} if 'i.pximg.net' in self.regular else {}
            async with aiohttp.request('GET', self.regular, headers=headers, timeout=aiohttp.ClientTimeout(10)) as resp:
                img_bytes: bytes = await resp.read()
            if check_size:
                img: PIL.Image.Image = PIL.Image.open(BytesIO(initial_bytes=img_bytes))
                #if img.size != (self.width, self.height):
                #    raise ValueError(f'Image Size Error: expected {(self.width, self.height)} but got {img.size}')
        except (asyncio.TimeoutError, ValueError) as e:
            raise e
        except PIL.UnidentifiedImageError:
            raise ValueError(f'Image load fail {str(img_bytes[:20])}...')
        return img_bytes

class SetuData(BaseModel):
    pid: int = None
    p: int = None
    uid: int = None
    title: str = None
    author: str = None
    urls: SetuUrlData = {}
    r18: bool = None
    width: int = None
    height: int = None
    tags: List[str] = []
    uploadDate: int = None
    ext: str = None

    @property
    def purl(self) -> str:
        return 'https://www.pixiv.net/artworks/{}'.format(Path(urlparse(self.urls.regular).path).stem.split('_')[0])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.pid == other.pid
        else:
            return False

    def __hash__(self):
        return hash(self.pid)

    def save(self) -> None:
        """保存至文件"""
        SetuDatabase.save(self)

    async def get(self, check_size: bool = True) -> bytes:
        """从网络获取图像"""
        try:
            
            EventLogger.info(f"url:{self.urls.regular}")
            headers = {'Referer': 'https://www.pixiv.net/'} if 'i.pximg.net' in self.urls.regular else {}
            async with aiohttp.request('GET', self.urls.regular, headers=headers, timeout=aiohttp.ClientTimeout(10)) as resp:
                EventLogger.info(f"url:{self.urls.regular} download success")
                img_bytes: bytes = await resp.read()
        except (asyncio.TimeoutError, ValueError) as e:
            raise e
        return img_bytes

    def sendToWeiXinBot(self, img_bytes, textContent):
        post_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8ba1eaf1-6e9b-4753-903b-14d1d8c36946"
        headers = {"Content-Type": "text/plain"}
        base64_data = base64.b64encode(img_bytes)
        md = hashlib.md5()
        md.update(img_bytes)
        res1 = md.hexdigest()
        data = {
            "msgtype": "image",
            "image": {
                "base64": base64_data,
                "md5": res1
            }
        }
        requests.post(post_url, headers=headers, json=data)
        data = {
            "msgtype": "text",
            "text": {
                "content": textContent
            }
        }
        requests.post(post_url, headers=headers, json=data)

class SetuDatabase(BaseModel):
    __root__: Set[SetuData] = set()

    @classmethod
    def load_from_file(cls) -> "SetuDatabase":
        try:
            db: SetuDatabase = cls.parse_file(SAVE_FILE)
        except (FileNotFoundError, json.JSONDecodeError, ValidationError):
            db = cls()
        return db

    def save_to_file(self) -> None:
        with SAVE_FILE.open('w', encoding='utf8') as f:
            json.dump([data.dict() for data in self.__root__], f, ensure_ascii=False, indent=2)

    @classmethod
    def save(cls, *data_array: SetuData) -> None:
        db: SetuDatabase = cls.load_from_file()
        for data in data_array:
            db.__root__.discard(data)
            db.__root__.add(data)
        db.save_to_file()


class SetuResp(BaseModel):
    error: str
    count: int = 0
    data: List[SetuData] = []

    def save(self) -> None:
        SetuDatabase.save(*self.data)

    @staticmethod
    async def get(keyword='') -> "SetuResp":
        api_url = 'https://api.lolicon.app/setu/v2'
        params = {
            "apikey": setu_apikey,
            "r18": setu_r18,
            "keyword": keyword,
            "num": 100,
            "proxy": setu_proxy,
            "size": 'regular'
        }
        async with aiohttp.request('GET', api_url, params=params) as response:
            setu_j = await response.read()
        resp: SetuResp = SetuResp.parse_raw(setu_j)
        resp.count = len(resp.data)
        resp.save()
        return resp
