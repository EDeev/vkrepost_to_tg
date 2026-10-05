import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties

from config import botToken
from sql import Users, Base

bot = Bot(token=botToken, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

os.makedirs("../db", exist_ok=True)
du = Users('../db/users.db')
db = Base('../db/base.db')

# лог в файл, если задан LOG_FILE (так бот работал на сервере), иначе — в консоль
logging.basicConfig(level=logging.INFO, filename=os.getenv("LOG_FILE") or None,
                    format="%(asctime)s %(levelname)s %(message)s")
