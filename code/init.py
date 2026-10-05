from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties


from config import botToken

bot = Bot(token=botToken, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


from sql import Users, Base

du = Users('../db/users.db')
db = Base('../db/base.db')


import logging, functools

logging.basicConfig(level=logging.INFO, filename='../info.log',filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")
