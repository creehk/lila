from asyncio import sleep
import warnings
import datetime

from aiogram import types, filters, md
from aiogram.utils.markdown import hide_link
from aiogram.utils.exceptions import RetryAfter, ChatNotFound, MessageCantBeDeleted, MessageCantBeEdited

from bot import bot, dp
import sqlite as db
import keyboards as kb

fast = False

# main game handlers \/

async def game_start(msg: types.Message):
    try: await msg.delete()
    except MessageCantBeDeleted: await msg.answer('⚠️ Сделайте бота админом с правами удалять сообщения')
    if not msg.from_user.id in [admin.user.id for admin in await msg.chat.get_administrators()]:
        temp_msg = await msg.answer('⚠️ Игру может запустить только админ группы')
        await sleep(3)
        await temp_msg.delete()
    elif db.get_game_users(msg.chat.id) is not None:
        temp_msg = await msg.answer('⚠️ Игра уже запущена')
        await sleep(3)
        await temp_msg.delete()
    else:
        db.create_game(msg.chat.id)
        db.set_game_state(msg.chat.id, 1)
        temp_msg = await msg.answer('Участники, пожалуйста нажмите на кнопку <b>«🤚🏻 Я Участвую»</b>\nПосле отправьте /start_game', 'html', reply_markup=kb.participate)
        db.set_game_msg(msg.chat.id, temp_msg.message_id)

async def game_start_complete(msg: types.Message):
    if (msg.from_user.id in [admin.user.id for admin in await msg.chat.get_administrators()]) and db.get_game_state(msg.chat.id) == 1:
        users = db.get_game_users(msg.chat.id)
        if users:
            db.set_game_state(msg.chat.id, 2)
            text = ''
            for i in users:
                text += '\n • <a href="tg://user?id=%i">%s</a>' % (i[0], i[1])
            try: await bot.delete_message(msg.chat.id, db.get_games_msg(msg.chat.id))
            except MessageCantBeDeleted: await msg.answer('⚠️ Сделайте бота админом с правами удалять сообщения')
            await msg.answer('<b><i>Игра начался!</i>\n\nУчастники:</b>'+text, 'html')
            user = users[0]
            db.set_game_current_user(msg.chat.id, user[0])
            await msg.answer('<a href="tg://user?id=%i">%s</a>, бросьте кубик' % (user[0], md.quote_html(user[1])), 'html', reply_markup=kb.dice)
        else:
            temp_msg = await msg.answer('⚠️ Нету участников')
            await sleep(2)
            try: await msg.delete()
            except MessageCantBeDeleted: await msg.answer('⚠️ Сделайте бота админом с правами удалять сообщения')
            await temp_msg.delete()
    else:
        try: await msg.delete()
        except MessageCantBeDeleted: await msg.answer('⚠️ Сделайте бота админом с правами удалять сообщения')
        temp_msg = await msg.answer('⚠️ Игру может запустить только админ группы')
        await sleep(3)
        await temp_msg.delete()

async def turn(msg: types.Message):
    if db.get_game_state(msg.chat.id) == 2:
        global fast
        if fast:
            try: await msg.delete()
            except MessageCantBeDeleted: await msg.answer('⚠️ Сделайте бота админом с правами удалять сообщения')
            return
        fast = True
        
        dice = await msg.answer_dice()
        dice_value = dice.dice.value
        # elif msg.text.isdigit() and 0 < int(msg.text) < 7:
        #     dice_value = int(msg.text)
        # else:
        #     return
        if msg.from_user.id == db.get_current_user(msg.chat.id):
            await sleep(3)

            text = ''
            
            progress = db.get_user_progress(msg.chat.id, msg.from_user.id)

            again_turn = False
            start = False
            arrow = False
            sneak = False
            disable_preview = False
    
            users = db.get_game_users(msg.chat.id)
            current_user = users.index((msg.from_user.id, msg.from_user.full_name))
            try: next_user = users[current_user + 1]
            except: next_user = users[0]

            position = 0
            for i in progress.split('.'): position += int(i)

            if position == 0:
                if dice_value == 6:
                    db.set_game_current_user(msg.chat.id, msg.from_user.id)
                    position += dice_value
                    text += 'Вам выпало: <b>%s</b>\n' % await get_value(dice_value)
                    text += '\n<b>Вы начали игру: <a href="%s">%s</a></b>' % await get_pos_meaing(1)
                    text += '\n\n<i>Перейдите на 6-клетку</i>'
                    start = True
                    db.set_game_state(msg.chat.id, 3)
                else:
                    db.user_move(msg.chat.id, msg.from_user.id, 0)
                    text += 'Вам выпало: <b>%s</b>\n' % await get_value(dice_value)
                    text += '\n<b>Для начала игры необходимо выбросить 6️⃣</b>' +\
                    '\n<i>Если 6️⃣ не выпадает то стоит подумать, правильно ли ты выбрал цель, возможно это не то, чего ты хочешь на самом деле</i>'
                    db.set_game_current_user(msg.chat.id, next_user[0])

            else:
                if (position > 68) and (dice_value > (72 - position)):
                    disable_preview = True
                    db.user_move(msg.chat.id, msg.from_user.id, 0)
                    text += 'Вам выпал: <b>%s</b>' % await get_value(dice_value)
                    text += '\n<b>Вы остаетесь на месте</b>'
                    text += '\n<b>Ваша позиция: <a href="%s">%s</a></b>' % await get_pos_meaing(position)
                    text += '\n<i>Чтобы продолжить надо выбросить кубик меньше или равной до 72-клетки</i>'
                    if dice_value == 6:
                        again_turn = True
                        db.set_game_current_user(msg.chat.id, msg.from_user.id)
                    else:
                        db.set_game_current_user(msg.chat.id, next_user[0])
                else:
                    if dice_value == 6:
                        if all(i == 6 for i in [progress[-3:]]):
                            db.set_game_current_user(msg.chat.id, next_user[0])
                            db.user_move(msg.chat.id, msg.from_user.id, -position)
                            text += '<b>Вы были в клетке: <a href="%s">%s</a></b>' % await get_pos_meaing(position)
                            text += '\nВам выпал 6️⃣, 4 раза подряд. Поэтому вы возвращаетесь в самое начало: '
                            position = 1
                            text += '<b><a href="%s">%s</a></b>' % await get_pos_meaing(position)
                        else:
                            db.set_game_current_user(msg.chat.id, msg.from_user.id)
                            db.user_move(msg.chat.id, msg.from_user.id, dice_value)
                            text += '<b>Вы были в клетке: <a href="%s">%s</a></b>' % await get_pos_meaing(position)
                            text += '\nВам выпало: <b>%s</b>' % await get_value(dice_value)
                            position += dice_value
                            text += '\n<b>Вы переходите в клетку: <a href="%s">%s</a></b>' % await get_pos_meaing(position)
                            again_turn = True

                    else:
                        db.set_game_current_user(msg.chat.id, next_user[0])
                        if all([i == 6 for i in [progress[-3:]]]):
                            db.user_move(msg.chat.id, msg.from_user.id, -18 + dice_value)
                            text += '<b>Вы были в клетке: <a href="%s">%s</a></b>' % await get_pos_meaing(position)
                            text += '\nВам выпало: <b>%s</b>' % await get_value(dice_value)
                            position += dice_value
                            text += '\n<i>Если шесть выпадает три раза подряд и игрок (пройдя 18 клеток) бросает кость ещё раз и получает не 6️⃣, он должен вернуться в то место, где он находился, прежде чем начал выбрасывать шестерки, и уже оттуда пройти столько клеток, сколько очков было в четвертом броске.</i>'
                            position -= 18
                            text += '\n<b>Вы возвращаетесь на клетку: <a href="%s">%s</a></b>' % await get_pos_meaing(position)
                            position += dice_value
                            text += '\n<b>И переходите на клетку: <a href="%s">%s</a></b>' % await get_pos_meaing(position)
                        else:
                            db.user_move(msg.chat.id, msg.from_user.id, dice_value)
                            text += '<b>Вы были в клетке: <a href="%s">%s</a></b>' % await get_pos_meaing(position)
                            text += '\nВам выпало: <b>%s</b>' % await get_value(dice_value)
                            position += dice_value
                            text += '\n<b>Вы переходите на клетку: <a href="%s">%s</a></b>' % await get_pos_meaing(position)

                boost = await get_boost(position)
                if boost:
                    db.set_game_current_user(msg.chat.id, msg.from_user.id)
                    db.set_game_state(msg.chat.id, 3)
                    if boost > position:
                        text += '\n\n<i>Вы попали на стрелу</i>'
                        arrow = True
                    else:
                        text += '\n\n<i>Вы попали на змею</i>'
                        sneak = True
            
                pos_meaning = await get_pos_meaing(position)
                link = pos_meaning[0]
                text = hide_link(link) + text

            if start: await msg.reply(text, 'html', reply_markup=kb.dice_start, disable_notification=True)
            elif arrow: await msg.reply(text, 'html', reply_markup=kb.dice_arrow, disable_notification=True)
            elif sneak: await msg.reply(text, 'html', reply_markup=kb.dice_sneak, disable_notification=True)
            else:
                await msg.reply(text, 'html', disable_notification=True, disable_web_page_preview=disable_preview)

                if position == 68:
                    db.set_user_finish(msg.chat.id, msg.from_user.id)
                    again_turn = False
                    await msg.answer('🥳 <b>Поздравляю!!!\n\n<a href="tg://user?id=%i">%s</a>, ты прошёл игру!</b>' % (msg.from_user.id, msg.from_user.full_name), 'html')
                    await story(msg)
                    if len(users) == 1:
                        db.delete_game(msg.chat.id)
                        await msg.answer('Все прошли игру, игра закончилась!')
                    else:
                        await msg.answer('<a href="tg://user?id=%i">%s</a>, бросьте кубик' % (next_user[0], md.quote_html(next_user[1])), 'html', reply_markup=kb.dice, disable_notification=True)
                        db.set_game_current_user(msg.chat.id, next_user[0])

                elif again_turn: await msg.answer('<a href="tg://user?id=%i">%s</a>, так как вым выпал 6️⃣, кидайте кубик ещё раз' % (msg.from_user.id, md.quote_html(msg.from_user.full_name)), 'html', reply_markup=kb.dice, disable_notification=True)
                else: await msg.answer('<a href="tg://user?id=%i">%s</a>, бросьте кубик' % (next_user[0], md.quote_html(next_user[1])), 'html', reply_markup=kb.dice, disable_notification=True)

        else:
            try: await msg.delete()
            except MessageCantBeDeleted: return
    elif db.get_game_state(msg.chat.id) == 3:
        try: await msg.delete()
        except MessageCantBeDeleted: return
    fast = False

async def inline_handler(cb: types.CallbackQuery):
    if db.get_game_state(cb.message.chat.id) == 1:
        users_game = db.get_user_game(cb.from_user.id)
        if users_game:
            if cb.message.chat.id == users_game:
                await cb.answer('🟡 Вы уже участвуете в этой игре')
            else:
                await cb.answer('🟡 Вы уже участвуете в другой игре')
        else:
            db.add_user_to_game(cb.message.chat.id, cb.from_user.id, cb.from_user.full_name)
            users = db.get_game_users(cb.message.chat.id)
            await cb.answer('✅ Вы участвуете')
            text = ''
            for i in users:
                text += '\n • <a href="tg://user?id=%i">%s</a>' % (i[0], md.quote_html(i[1]))
            await bot.edit_message_text('Участники, пожалуйста нажмите на кнопку <b>«🤚🏻 Я Участвую»</b>\nПосле этого отправьте /start_game\n\n<b>Участники:</b>'+text, cb.message.chat.id, db.get_games_msg(cb.message.chat.id), parse_mode='html', reply_markup=kb.participate)
    elif db.get_game_state(cb.message.chat.id) == 3:
        if cb.from_user.id == db.get_current_user(cb.message.chat.id):
            await cb.message.delete_reply_markup()
            if cb.data == 'start':
                db.user_move(cb.message.chat.id, cb.from_user.id, 6)
                await cb.message.answer('<b>Вы переходите на клетку: <a href="%s">%s</a></b>' % await get_pos_meaing(6), 'html', disable_notification=True)
                await cb.message.answer('<a href="tg://user?id=%i">%s</a>, так как вым выпал 6️⃣, кидайте кубик ещё раз' % (cb.from_user.id, md.quote_html(cb.from_user.full_name)), 'html', disable_notification=True)
            else:
                progress = db.get_user_progress(cb.message.chat.id, cb.from_user.id)
                position = 0
                for i in progress.split('.'): position += int(i)
                boost = await get_boost(position)

                users = db.get_game_users(cb.message.chat.id)
                current_user = users.index((cb.from_user.id, cb.from_user.full_name))
                try: next_user = users[current_user + 1]
                except: next_user = users[0]

                if cb.data == 'arrow':
                    db.user_move(cb.message.chat.id, cb.from_user.id, boost - position)
                    await cb.message.answer('🏹 <b>Вы поднимаетесь по стреле: <a href="%s">%s</a></b>' % await get_pos_meaing(boost), 'html')
                elif cb.data == 'sneak':
                    db.user_move(cb.message.chat.id, cb.from_user.id, boost - position)
                    await cb.message.answer('🐍 <b>Вы опускаетесь по змее: <a href="%s">%s</a></b>' % await get_pos_meaing(boost), 'html')

                if position == 68:
                    db.set_user_finish(cb.message.chat.id, cb.from_user.id)
                    await cb.message.answer('<b>Поздравляю!!!\n\n<a href="tg://user?id=%i">%s</a>, ты прошёл игру!</b>' % (cb.from_user.id, cb.from_user.full_name), 'html')
                    await cb.message.answer('🥳')
                    if len(users) == 1:
                        await cb.message.answer('ну всё, игра закончилас!)')
                        db.delete_game(cb.message.chat.id)
                    else:
                        db.set_game_current_user(cb.message.chat.id, next_user[0])
                        await cb.message.answer('<a href="tg://user?id=%i">%s</a>, бросьте кубик' % (next_user[0], md.quote_html(next_user[1])), 'html', reply_markup=kb.dice, disable_notification=True)

                elif int(progress.split('.')[-1]) == 6: await cb.message.answer('<a href="tg://user?id=%i">%s</a>, так как вым выпал 6️⃣, кидайте кубик ещё раз' % (cb.from_user.id, md.quote_html(cb.from_user.full_name)), 'html', reply_markup=kb.dice, disable_notification=True)
                else:
                    db.set_game_current_user(cb.message.chat.id, next_user[0])
                    await cb.message.answer('<a href="tg://user?id=%i">%s</a>, бросьте кубик' % (next_user[0], md.quote_html(next_user[1])), 'html', reply_markup=kb.dice, disable_notification=True)
            db.set_game_state(cb.message.chat.id, 2)
        else:
            await cb.answer('⚠️ Это не ваш ход')
    else:
        await cb.message.delete_reply_markup()

# other handlers \/

async def kick(msg: types.Message):
    if msg.from_user.id in [admin.user.id for admin in await msg.chat.get_administrators()]:
        if msg.reply_to_message and \
         ((msg.reply_to_message.from_user.id, msg.reply_to_message.from_user.full_name) in db.get_game_users(msg.chat.id)):
            db.set_user_finish(msg.chat.id, msg.reply_to_message.from_user.id, True)
            await msg.reply('✔️ Пользователь был удалён из очереди', disable_notification=True)
            if len(db.get_current_user(msg.chat.id)) == 1:
                db.delete_game()
                await msg.answer('Игроков не осталось, игра закончилась!')
            elif msg.reply_to_message.from_user.id == db.get_current_user(msg.chat.id):
                users = db.get_game_users(msg.chat.id)
                current_user = users.index((msg.reply_to_message.from_user.id, msg.reply_to_message.from_user.full_name))
                try: next_user = users[current_user + 1]
                except: next_user = users[0]
                db.set_game_current_user(next_user[0])
                await msg.answer('<a href="tg://user?id=%i">%s</a>, бросьте кубик' % (next_user[0], next_user[1]))
        elif msg.reply_to_message:
            temp_msg = await msg.reply('Пользователя и так нету в очереди', disable_notification=True)
            await sleep(5)
            await msg.delete()
            await temp_msg.delete()
        else:
            temp_msg = await msg.reply('⚠️ Надо ответить на сообщние пользователя которого хотите удалить из очереди', disable_notification=True)
            await sleep(5)
            await msg.delete()
            await temp_msg.delete()
    else:
        await msg.delete()
        temp_msg = await msg.answer('⚠️ Этой команду может использовать только админ группы')
        await sleep(3)
        await temp_msg.delete()

async def cancel_game(msg: types.Message):
    if msg.from_user.id in [741474395, 5610170020]:
        cancel = db.delete_game(msg.chat.id)
        if cancel:
            await msg.answer('✔️ Игра отменена', disable_notification=True)
        else:
            await msg.answer('⚠️ Игра и так не запущена', disable_notification=True)
    else:
        await msg.delete()

async def story(msg: types.Message):
    if db.get_game_state(msg.chat.id) == 2:
        if msg.text == '/story' and msg.reply_to_message:
            user = msg.reply_to_message.from_user.id
            user_name = msg.reply_to_message.from_user.full_name
        else:
            user = msg.from_user.id
            user_name = msg.from_user.full_name
        progress = db.get_user_progress(msg.chat.id, user)
        text = '<b>История ходов игрока</b> <a href="tg://user?id=%i">%s</a>:\n\n' % (user, user_name)
        if progress.split('.')[1:]:
            position = 6
            numeration = 0
            empty = False
            is_born = False
            value = None
            for i in progress.split('.')[1:]:
                value = i
                numeration += 1
                if not is_born and i != '0':
                    is_born = True
                    empty = False
                    text = '<b>' + text[:-2] + ') неудачные ходы</b>\n'
                    text += '<b>%i) </b>6️⃣ - <i><a href="https://telegra.ph/1-Rozhdenie-02-10">1. Рождение</a>' % numeration
                    text += ' - <a href="https://telegra.ph/6-Zabluzhdenie-02-10">6. Заблуждение</a></i>\n'
                elif i == '0':
                    text += '%i, ' % numeration
                    empty = True
                else:
                    if empty:
                        text = '<b>' + text[:-2] + ') неудачные ходы</b>\n'
                        empty = False
                    text += '<b>%i) </b>' % numeration
                    if 0 < int(i) < 7:
                        text += '%s - ' % await get_value(int(i))
                    elif int(i) > 6:
                        text += '↗️🟢 Поднимание по стреле - '
                    elif position + int(i) == 0:
                        text += '⚫️ Чел сломал игру и начал заново - '
                    elif int(i) < 0:
                        text += '↘️🔴 Спускание по змее - '
                    position += int(i)
                    text += '<i><a href="%s">%s</a></i>\n' % await get_pos_meaing(position)
            if value == '0':
                text = '<b>' + text[:-2] + ') неудачные ходы</b>\n'
            try:
                await bot.send_message(msg.from_user.id, text, 'html', reply_markup=kb.return_to_chat('https://t.me/c/'+str(msg.chat.id).replace('-100', '').replace('-', '')), disable_web_page_preview=True, disable_notification=True)
                await msg.reply('Я отправил вам историю:', reply_markup=kb.story, disable_notification=True)
            except ChatNotFound:
                await msg.reply('Сначала запустите бота в ЛС', reply_markup=kb.bot_ls, disable_notification=True)
        else:
            await msg.reply('⚠️ Вы ещё не начали игру', disable_notification=True)
    else:
        await msg.delete()

async def positions(msg: types.Message):
    if db.get_game_state(msg.chat.id) == 2 and msg.from_user.id == db.get_current_user(msg.chat.id):
        text = '<b>Текущие позиции всех игроков:</b>\n\n'
        for user in db.get_game_users(msg.chat.id, True):
            progress = db.get_user_progress(msg.chat.id, user[0])
            position = 0
            for i in progress.split('.'): position += int(i)
            text += '<a href="tg://user?id=%s">%s</a> 👉🏻 ' % (user[0], user[1])
            if position == 68: text += '<b>Закончил игру</b>\n'
            elif position: text += '<a href="%s">%s</a>\n' % await get_pos_meaing(position)
            else: text += '<b>Ещё не родился</b>\n'
        await msg.reply(text, 'html', disable_web_page_preview=True, disable_notification=True)
    else:
        await msg.delete()

# private funcs \/

async def get_boost(pos: int):
    if pos == 10: return 23
    elif pos == 17: return 69
    elif pos == 20: return 32
    elif pos == 22: return 66
    elif pos == 27: return 41
    elif pos == 28: return 50
    elif pos == 37: return 66
    elif pos == 45: return 67
    elif pos == 46: return 62
    elif pos == 54: return 68

    elif pos == 72: return 51
    elif pos == 63: return 2
    elif pos == 61: return 13
    elif pos == 55: return 3
    elif pos == 52: return 35
    elif pos == 44: return 9
    elif pos == 29: return 6
    elif pos == 24: return 7
    elif pos == 16: return 4
    elif pos == 12: return 8

async def get_value(value: int):
    if value == 1: return '1️⃣'
    elif value == 2: return '2️⃣'
    elif value == 3: return '3️⃣'
    elif value == 4: return '4️⃣'
    elif value == 5: return '5️⃣'
    elif value == 6: return '6️⃣'

async def get_pos_meaing(pos: int) -> str:
    if pos == 1: return ('https://telegra.ph/1-Rozhdenie-02-10', '1. Рождение')
    elif pos == 2: return ('https://telegra.ph/2-Maja-02-10', '2. Майа')
    elif pos == 3: return ('https://telegra.ph/3-Gnev-02-10', '3. Гнев')
    elif pos == 4: return ('https://telegra.ph/4-ZHadnost-02-10', '4. Жадность')
    elif pos == 5: return ('https://telegra.ph/5-Fizicheskij-plan-02-10', '5. Физический план')
    elif pos == 6: return ('https://telegra.ph/6-Zabluzhdenie-02-10', '6. Заблуждение')
    elif pos == 7: return ('https://telegra.ph/7-Tshcheslavie-02-10', '7. Тщеславие')
    elif pos == 8: return ('https://telegra.ph/8-Alchnost-02-10', '8. Алчность')
    elif pos == 9: return ('https://telegra.ph/9-CHuvstvennyj-plan-02-10', '9. Чувственный план')
    elif pos == 10: return ('https://telegra.ph/10-Ochishchenie-02-10', '10. Очищение')
    elif pos == 11: return ('https://telegra.ph/11-Razvlecheniya-02-10', '11. Развлечения')
    elif pos == 12: return ('https://telegra.ph/12-Zavist-02-10', '12. Зависть')
    elif pos == 13: return ('https://telegra.ph/13-Nichtozhnost-02-10', '13. Ничтожность')
    elif pos == 14: return ('https://telegra.ph/14-Astralnyj-plan-02-10', '14. Астральный план')
    elif pos == 15: return ('https://telegra.ph/15-Plan-fantazii-02-10', '15. План фантазии')
    elif pos == 16: return ('https://telegra.ph/16-Revnost-02-10', '16. Ревность')
    elif pos == 17: return ('https://telegra.ph/17-Sostradanie-02-10', '17. Сострадание')
    elif pos == 18: return ('https://telegra.ph/18-Plan-radosti-02-10', '18. План радости')
    elif pos == 19: return ('https://telegra.ph/19-Plan-karmy-02-10', '19. План кармы')
    elif pos == 20: return ('https://telegra.ph/20-Blagotvoritelnost-02-10', '20. Благотворительность')
    elif pos == 21: return ('https://telegra.ph/21-Iskuplenie-02-10', '21. Искупление')
    elif pos == 22: return ('https://telegra.ph/22-Plan-Dharmy-02-10', '22. План Дхармы')
    elif pos == 23: return ('https://telegra.ph/23-Nebesnyj-plan-02-10', '23. Небесный план')
    elif pos == 24: return ('https://telegra.ph/24-Plohaya-kompaniya-02-10', '24. Плохая компания')
    elif pos == 25: return ('https://telegra.ph/25-Horoshaya-kompaniya-02-10', '25. Хорошая компания')
    elif pos == 26: return ('https://telegra.ph/26-Pechal-02-10', '26. Печаль')
    elif pos == 27: return ('https://telegra.ph/27-Samootverzhennoe-sluzhenie-02-10', '27. Самоотверженное служение')
    elif pos == 28: return ('https://telegra.ph/28-Istinnaya-religioznost-02-10', '28. Истинная религиозность')
    elif pos == 29: return ('https://telegra.ph/29-Nepravednost-02-10', '29. Неправедность')
    elif pos == 30: return ('https://telegra.ph/30-Horoshie-tendencii-02-10', '30. Хорошие тенденции')
    elif pos == 31: return ('https://telegra.ph/31-Plan-svyatosti-02-10', '31. План святости')
    elif pos == 32: return ('https://telegra.ph/32-Plan-ravnovesiya-02-10', '32. План равновесия')
    elif pos == 33: return ('https://telegra.ph/33-Plan-aromatov-02-10', '33. План ароматов')
    elif pos == 34: return ('https://telegra.ph/34-Plan-vkusa-02-10', '34. План вкуса')
    elif pos == 35: return ('https://telegra.ph/35-CHistilishche-02-10', '35. Чистилище')
    elif pos == 36: return ('https://telegra.ph/36-YAsnost-soznaniya-02-10', '36. Ясность сознания')
    elif pos == 37: return ('https://telegra.ph/37-Dzhnyana-02-10', '37. Джняна')
    elif pos == 38: return ('https://telegra.ph/38-Prana-loka-02-10', '38. Прана-лока')
    elif pos == 39: return ('https://telegra.ph/39-Apana-loka-02-10', '39. Апана-лока')
    elif pos == 40: return ('https://telegra.ph/40-Vyana-loka-02-10', '40. Въяна-лока')
    elif pos == 41: return ('https://telegra.ph/41-CHelovecheskij-plan-02-10', '41. Человеческий план')
    elif pos == 42: return ('https://telegra.ph/42-Plan-Agni-02-10', '42. План Агни')
    elif pos == 43: return ('https://telegra.ph/43-Rozhdenie-cheloveka-02-10', '43. Рождение человека')
    elif pos == 44: return ('https://telegra.ph/44-Nevedenie-02-10', '44. Неведение')
    elif pos == 45: return ('https://telegra.ph/45-Pravilnoe-znanie-02-10', '45. Правильное знание')
    elif pos == 46: return ('https://telegra.ph/46-Razlichenie-02-10', '46. Различение')
    elif pos == 47: return ('https://telegra.ph/47-Plan-nejtralnosti-02-10', '47. План нейтральности')
    elif pos == 48: return ('https://telegra.ph/48-Solnechnyj-plan-02-10', '48. Солнечный план')
    elif pos == 49: return ('https://telegra.ph/49-Lunnyj-plan-02-10', '49. Лунный план')
    elif pos == 50: return ('https://telegra.ph/50-Plan-asketizma-02-10', '50. План аскетизма')
    elif pos == 51: return ('https://telegra.ph/51-Zemlya-02-10', '51. Земля')
    elif pos == 52: return ('https://telegra.ph/52-Plan-nasiliya-02-10', '52. План насилия')
    elif pos == 53: return ('https://telegra.ph/53-Plan-zhidkostej-02-10', '53. План жидкостей')
    elif pos == 54: return ('https://telegra.ph/54-Plan-duhovnoj-predannosti-02-10', '54. План духовной преданности')
    elif pos == 55: return ('https://telegra.ph/55-EHgoizm-02-10', '55. Эгоизм')
    elif pos == 56: return ('https://telegra.ph/56-Plan-iznachalnyh-vibracij-02-10', '56. План изначальных вибраций')
    elif pos == 57: return ('https://telegra.ph/57-Plan-gazov-02-10', '57. План газов')
    elif pos == 58: return ('https://telegra.ph/58-Plan-siyaniya-02-10', '58. План сияния')
    elif pos == 59: return ('https://telegra.ph/59-Plan-realnosti-02-10', '59. План реальности')
    elif pos == 60: return ('https://telegra.ph/60-Pozitivnyj-intellekt-02-10', '60. Позитивный интеллект')
    elif pos == 61: return ('https://telegra.ph/61-Negativnyj-intellekt-02-10', '61. Негативный интеллект')
    elif pos == 62: return ('https://telegra.ph/62-Schaste-02-10', '62. Счастье')
    elif pos == 63: return ('https://telegra.ph/63-Tamas-02-10', '63. Тамас')
    elif pos == 64: return ('https://telegra.ph/64-Fenomenalnyj-plan-02-10', '64. Феноменальный план')
    elif pos == 65: return ('https://telegra.ph/65-Plan-vnutrennego-prostranstva-02-10', '65. План внутреннего пространства')
    elif pos == 66: return ('https://telegra.ph/66-Plan-blazhenstva-02-10', '66. План блаженства')
    elif pos == 67: return ('https://telegra.ph/67-Plan-kosmicheskogo-blaga-02-10', '67. План космического блага')
    elif pos == 68: return ('https://telegra.ph/68-Kosmicheskoe-Soznanie-02-10', '68. Космическое Сознание')
    elif pos == 69: return ('https://telegra.ph/69-Plan-Absolyuta-02-10', '69. План Абсолюта')
    elif pos == 70: return ('https://telegra.ph/70-Sattvaguna-02-10', '70. Саттвагуна')
    elif pos == 71: return ('https://telegra.ph/71-Radzhoguna-02-10', '71. Раджогуна')
    elif pos == 72: return ('https://telegra.ph/72-Tamoguna-02-10', '72. Тамогуна')

# ----------------

def register_handlers_game():
    dp.register_message_handler(game_start, filters.ChatTypeFilter(['group', 'supergroup']), commands=['start'], state='*')
    dp.register_message_handler(game_start_complete, filters.ChatTypeFilter(['group', 'supergroup']), commands=['start_game'])
    dp.register_message_handler(kick, filters.ChatTypeFilter(['group', 'supergroup']), commands=['kick'])
    dp.register_message_handler(story, filters.ChatTypeFilter(['group', 'supergroup']), commands=['story'])
    dp.register_message_handler(cancel_game, filters.ChatTypeFilter(['group', 'supergroup']), commands=['cancel'])
    dp.register_message_handler(story, filters.ChatTypeFilter(['group', 'supergroup']), filters.Text(['📒 Моя историю']))
    dp.register_message_handler(positions, filters.ChatTypeFilter(['group', 'supergroup']), filters.Text(['♻️ Текущие позиции']))
    dp.register_message_handler(turn, filters.ChatTypeFilter(['group', 'supergroup']), filters.Text(['🎲 Сделать ход']))
    dp.register_callback_query_handler(inline_handler, filters.ChatTypeFilter(['group', 'supergroup']))