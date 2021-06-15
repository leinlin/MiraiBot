import aiohttp
import lxml.html
import typing as T
import re
from mirai import Mirai, Group, GroupMessage, MessageChain, Image, Plain, QQFaces, At, AtAll
from mirai.logger import Event as EventLogger

sub_app = Mirai(f"mirai://localhost:8080/?authKey=0&qq=0")

last_message = None
@sub_app.receiver(GroupMessage)
async def fudu(app: Mirai, group: Group, message: MessageChain):
    global last_message
    match = re.match(r'(?:.*?([\d一二两三四五六七八九十]*)张|来点)?(.{0,10}?)的?[色|涩]图$', message.toString())
    if match:
        return

    if last_message != None and last_message.toString() == message.toString():
        EventLogger.info(f"{message.toString()}消息已复读")
        replyArray = []
        for v in message:
            if type(v) == Image or type(v) == Plain or type(v) == At or type(v) == AtAll or type(v) == QQFaces:
                replyArray.append(v)

        await app.sendGroupMessage(group, replyArray)
    else:
        if last_message != None:
            EventLogger.info(f"last_message:{last_message.toString()}")
        EventLogger.info(f"{message.toString()}消息已缓存")
        last_message = message
