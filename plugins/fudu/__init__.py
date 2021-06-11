import aiohttp
import lxml.html
import typing as T
from mirai import Mirai, Group, GroupMessage, MessageChain, Image

sub_app = Mirai(f"mirai://localhost:8080/?authKey=0&qq=0")

last_message = None
@sub_app.receiver(GroupMessage)
async def fudu(app: Mirai, group: Group, message: MessageChain):
    global last_message
    if last_message != None and last_message.toString() == message.toString():
        await app.sendGroupMessage(group, message)
    else:
        last_message = message
