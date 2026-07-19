from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN

bot = Bot(TOKEN, timeout=15)
dp = Dispatcher(bot, storage=MemoryStorage())