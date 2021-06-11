import aiohttp
import lxml.html
import typing as T
from mirai import Mirai, Group, GroupMessage, MessageChain, Image
from mirai.logger import Event as EventLogger

sub_app = Mirai(f"mirai://localhost:8080/?authKey=0&qq=0")

last_message = None
@sub_app.receiver(GroupMessage)
async def fudu(app: Mirai, group: Group, message: MessageChain):
    global last_message
    if last_message != None and last_message.toString() == message.toString():
        EventLogger.info(f"{message.toString()}消息已复读")
        await app.sendGroupMessage(group, message.asSendable())
    else:
        if last_message != None:
            EventLogger.info(f"last_message:{last_message.toString()}")
        EventLogger.info(f"{message.toString()}消息已缓存")
        last_message = message
