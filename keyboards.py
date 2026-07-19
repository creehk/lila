from aiogram.types import ReplyKeyboardMarkup as rk
from aiogram.types import KeyboardButton as rb
from aiogram.types import ReplyKeyboardRemove as delete
from aiogram.types import InlineKeyboardMarkup as ik
from aiogram.types import InlineKeyboardButton as ib

from config import bot_link

none = delete()

dice = rk(resize_keyboard=True)
dice.row(rb('🎲 Сделать ход'))
dice.row(rb('📒 Моя историю'), rb('♻️ Текущие позиции'))

dice_solo = rk(resize_keyboard=True)
dice_solo.row(rb('🎲 Сделать ход'), rb('📒 Моя историю'))

dice_start = ik(resize_keyboard=True)
dice_start.row(ib('↗️ Перейти на 6-клетку', callback_data='start'))

dice_sneak = ik(resize_keyboard=True)
dice_sneak.row(ib('🐍 Спуститься по змее', callback_data='sneak'))

dice_arrow = ik(resize_keyboard=True)
dice_arrow.row(ib('🏹 Подняться по стреле', callback_data='arrow'))

menu = rk(resize_keyboard=True)
menu.row(rb('👤 Играть одному'), rb('👥 Играть с друзьями'))
menu.row(rb('♣️ Мои игры'))

back = rk(resize_keyboard=True)
back.row(rb('↪️ Назад'))

add_to_group = ik()
add_to_group.row(ib('➕ Добавить бота в группу', bot_link+'?startgroup'))

participate = ik()
participate.row(ib('🤚🏻 Я Участвую', callback_data='participating'))

story = ik()
story.row(ib('↗️ Посмотреть историю', bot_link))

bot_ls = ik()
bot_ls.row(ib('↗️ Перейти в ЛС с ботом', bot_link))

def return_to_chat(chat_link: str):
    kb = ik()
    kb.row(ib('↪️ Вернуться к чату', chat_link))
    return kb