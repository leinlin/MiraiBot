import aiohttp
import lxml.html
import typing as T
from mirai import Mirai, Group, GroupMessage, MessageChain, Image

sub_app = Mirai(f"mirai://localhost:8080/?authKey=0&qq=0")

last_message = ""
@sub_app.receiver(GroupMessage)
async def fudu(app: Mirai, message: GroupMessage):
    if message.toString() == last_message:
        await app.sendGroupMessage(message.sender.group, last_message)
    else
        last_message = message.toString()
