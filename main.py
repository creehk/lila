import logging

from aiogram import executor

from bot import dp, bot
from h_client import register_handlers_client
from h_group import register_handlers_game
from sqlite import shutdown

logging.basicConfig(level=logging.INFO)

try:
    register_handlers_client()
    register_handlers_game()
    executor.start_polling(dp, skip_updates=True)
except Exception:
    bot.send_message(741474395, str(Exception))
finally:
    shutdown()