import aiohttp
import lxml.html
import typing as T
from mirai import Mirai, Group, GroupMessage, MessageChain, Image

sub_app = Mirai(f"mirai://localhost:8080/?authKey=0&qq=0")

last_message = None
@sub_app.receiver(GroupMessage)
async def fudu(app: Mirai, group: Group, message: MessageChain):
    if last_message.toString() == message.toString():
        image: T.Optional[Image] = message.getFirstComponent(Image)
        if image and image.url:
            last_image: T.Optional[Image] = last_message.getFirstComponent(Image)
            if last_image and last_image.url and last_image.url == image.url:
                await app.sendGroupMessage(group, message)
        else
            await app.sendGroupMessage(group, message)
    else
        last_message = message
