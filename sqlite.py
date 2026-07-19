import sqlite3
import random
from datetime import date

con = sqlite3.connect('database.db')
cur = con.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER NOT NULL UNIQUE, first_name TEXT NOT NULL, last_name TEXT, username TEXT, phone_number TEXT, games TEXT, register_date TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1)')
cur.execute('CREATE TABLE IF NOT EXISTS games (group_id INTEGER NOT NULL UNIQUE, msg_id INTEGER, state INTEGER NOT NULL DEFAULT 0, current_user INTEGER NOT NULL DEFAULT 0)')

def _generateID():
    code = 0
    while True:
        code = random.randint(100, 999)
        if not cur.execute('SELECT id FROM games WHERE id = ?', (code,)).fetchone():
            return code

def user_init(user_id: int, user_first_name: str, user_last_name: str | None = None, username: str | None = None):
    user = con.execute('SELECT first_name, last_name, username FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        if user[0] != user_first_name or user[1] != user_last_name or user[2] != username:
            cur.execute('UPDATE users SET first_name = ?, last_name = ?, username = ? WHERE id = ?', (user_first_name, user_last_name, username,))
        return True
    else:
        register_date = date.strftime(date.today(), '%Y.%m.%d')
        cur.execute('INSERT INTO users (id, first_name, last_name, username, register_date) VALUES (?, ?, ?, ?, ?)', (user_id, user_first_name, user_last_name, username, register_date,))

def create_game(group_id: int):
    cur.execute('CREATE TABLE "%i" (user_id INTEGER NOT NULL, user_name TEXT, progress TEXT NOT NULL DEFAULT "0", state INTEGER NOT NULL DEFAULT 1)' % group_id)
    cur.execute('INSERT INTO games (group_id) VALUES (?)', (group_id,))
    con.commit()

def add_user_to_game(group_id: int, user_id: int, user_name: str):
    cur.execute('INSERT INTO "%i" (user_id, user_name) VALUES (?, ?)' % group_id, (user_id, user_name,))
    con.commit()

def remove_user_from_game(group_id: int, user_id: int):
    cur.execute('DELETE FROM "%i" WHERE user_id = ?' % group_id, (user_id,))
    con.commit()

def user_move(group_id: int, user_id: int, progress: int):
    old_progress = cur.execute('SELECT progress FROM "%s" WHERE user_id = ?' % group_id, (user_id,)).fetchone()[0]
    cur.execute('UPDATE "%s" SET progress = ? WHERE user_id = ?' % group_id, (old_progress + '.' + str(progress), user_id,))
    con.commit()

def get_games_msg(group_id: int):
    result = cur.execute('SELECT msg_id FROM games WHERE group_id = ?', (group_id,)).fetchone()
    if result:
        return result[0]

def get_game_users(group_id: int, return_all: True = False):
    try:
        if return_all: return cur.execute('SELECT user_id, user_name FROM "%i"' % group_id).fetchall()
        else: return cur.execute('SELECT user_id, user_name FROM "%i" WHERE state = 1' % group_id).fetchall()
    except: pass

def get_current_user(group_id: int):
    return cur.execute('SELECT current_user FROM games WHERE group_id = ?', (group_id,)).fetchone()[0]

def get_user_progress(group_id: int, user_id: int):
    return cur.execute('SELECT progress FROM "%i" WHERE user_id = ?' % group_id, (user_id,)).fetchone()[0]

def get_game_state(group_id: int):
    result =  cur.execute('SELECT state FROM games WHERE group_id = ?', (group_id,)).fetchone()
    if result:
        return result[0]

def get_user_game(user_id: int):
    tables = cur.execute('SELECT * FROM sqlite_master WHERE type = "table"').fetchall()
    table_names = []
    for i in tables:
        if not (i[1] == 'users' or i[1] == 'games'):
            table_names.append(i[1])
    for group_id in table_names:
        result = cur.execute('SELECT user_id FROM "%s"' % group_id).fetchall()
        user_ids = []
        for i in result:
            user_ids.append(i[0])
        if user_id in user_ids: return int(group_id)

def set_game_current_user(group_id: int, user_id: int):
    cur.execute('UPDATE games SET current_user = ? WHERE group_id = ?', (user_id, group_id,))
    con.commit()

def set_game_state(group_id: int, state: int):
    cur.execute('UPDATE games SET state = ? WHERE group_id = ?', (state, group_id,))
    con.commit()

def set_game_msg(group_id: int, temp_msg_id: int):
    cur.execute('UPDATE games SET msg_id = ? WHERE group_id = ?', (temp_msg_id, group_id,))
    con.commit()

def set_user_finish(group_id: int, user_id: int, is_kick: True = None):
    progress = get_user_progress(group_id, user_id)

    cur.execute('UPDATE "%i" SET state = ? WHERE user_id = ?' %  group_id, (0, user_id,))

    if not is_kick:
        games = ''
        result = cur.execute('SELECT games FROM users WHERE id = ?', (user_id,)).fetchone()[0]
        if result: games = result

        cur.execute('UPDATE users SET games = ? WHERE id = ?', (games+progress+'|', user_id,))
        con.commit()

def delete_game(group_id: int):
    if cur.execute('SELECT * FROM games WHERE group_id = ?', (group_id,)).fetchone():
        cur.execute('DROP TABLE "%i"' % group_id)
        cur.execute('DELETE FROM games WHERE group_id = ?', (group_id,))
        con.commit()
        return 1

def get_user_games(user_id: int):
    return cur.execute('SELECT games FROM users WHERE id = ?', (user_id,)).fetchone()[0]

def shutdown():
    cur.execute('DELETE FROM games')
    tables = cur.execute('SELECT * FROM sqlite_master WHERE type = "table"').fetchall()
    for i in tables:
        if not (i[1] == 'users' or i[1] == 'games'):
            cur.execute('DROP TABLE "%s"' % i[1])
    con.commit()