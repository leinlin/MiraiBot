import asyncio
import random
import re
from typing import List, Set, Union

from mirai import (
    Mirai,
    Group, Member, GroupMessage,
    Image, Plain, At)
from mirai.event.message.chain import Source
from mirai.logger import Event as EventLogger

from .SetuData import SetuData, SetuResp, SetuDatabase
from .._utils import CoolDown, shuzi2number
from config import setu_r18

cd = CoolDown(app='setu', td=20)

sub_app = Mirai(f"mirai://localhost:8080/?authKey=0&qq=0")


@sub_app.receiver("GroupMessage")
async def GMHandler(app: Mirai, message: GroupMessage):
    msgStr = message.toString()
    match = re.match(r'(?:.*?([\d一二两三四五六七八九十]*)张|来点)?(.{0,10}?)的?[色|涩]图$', msgStr)
    if match:
        number: int = shuzi2number(match[1])
        if number > 10:
            number = 1
        keyword = match[2]
        try:
            await setuExecutor(app, message, number, keyword)
        except Exception as e:
            import traceback
            EventLogger.error(e)
            EventLogger.error(traceback.format_exc())


async def setuExecutor(app: Mirai, message: GroupMessage, number: int, keyword: str):
    """根据关键词获取data_array，并调用sendSetu"""
    member_id: int = message.sender.id
    if keyword == '':
        resp = await SetuResp.get()
    elif cd.check(member_id):
        resp = await SetuResp.get(keyword)
    else:
        resp = SetuResp(error='欧尼酱你的速度太快了，休息一下吧')

    if resp.error == "":
        cd.update(member_id)
        await sendSetu(app, message, resp.data, number)
    else:
        group: Group = message.sender.group
        source: Source = message.messageChain.getSource()
        await app.sendGroupMessage(group, resp.error, source)


async def sendSetu(app: Mirai, message: GroupMessage, data_array: Union[Set[SetuData], List[SetuData]], number: int):
    """发送data_array"""
    sender: Member = message.sender
    group: Group = message.sender.group

    async def send(prefix_: str, data_: SetuData):
        try:
            setu_b: bytes = await data_.get()
            await app.sendGroupMessage(group,
                                       [At(sender.id), Plain(prefix_ + data_.purl + '\n'), Image.fromBytes(setu_b), Plain(f"XP：{','.join(data_.tags)}")])
            EventLogger.info(f"{prefix_}色图已发送，标签：{','.join(data_.tags)}")
        except asyncio.TimeoutError as e:
            EventLogger.warn('连接超时' + str(e))
            raise e
        except ValueError as e:
            EventLogger.warn('图片尺寸检查失败' + str(e))
            raise e

    number = min(number, len(data_array))

    if number == 0:
        await app.sendGroupMessage(group,
                            [At(sender.id), Plain(f"抱歉没有找到对应的色图")])
    # 延时逐个启动任务
    tasks: List[asyncio.Task[None]] = []
    for i, data in enumerate(random.sample(data_array, k=number)):
        prefix = f'[{i + 1}/{number}]' if number > 1 else ''
        task = asyncio.create_task(send(prefix, data))
        tasks.append(task)
        await asyncio.wait(tasks, timeout=5)

    # 等待返回
    done, pending = await asyncio.wait(tasks, timeout=10)
    num_exception = len([task.exception() for task in done if task.exception()])
    num_timeout = len([t.cancel() for t in pending])

    # 报告结果
    if num_exception or num_timeout:
        msg_timeout = f'{num_timeout}个任务超时' if num_timeout else ''
        msg_exception = f'{num_exception}个任务异常' if num_exception else ''
        msg = msg_timeout or msg_exception
        if msg_timeout and msg_exception:
            msg += ', ' + msg_exception
        await app.sendGroupMessage(group, msg)
