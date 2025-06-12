import sys
from pathlib import Path
from datetime import datetime
import random
import string
from typing import Optional
from aiogram.fsm.storage.base import StorageKey, BaseStorage
from aiogram import Bot
from sqlite3 import connect

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from DBConnect import connect
from Tables.RoomParticipants import join_room

"""
Room

PK  id                          int
------------------------------------------
    key                         text
------------------------------------------
FK1 creator_id                  int
------------------------------------------
    status                      text
    __________
    [waiting, active, finished]
------------------------------------------
    created_at                  timestamp
------------------------------------------
    is_closed                   bool


"""

#checked

def generate_random_key():
     with connect() as conn:
        cur = conn.cursor()
        characters = string.ascii_uppercase + string.digits  # A-Z и 0-9
        key = ''.join(random.choices(characters, k=6))
        cur.execute("SELECT id FROM Room WHERE key = ?",(key,))
        row = cur.fetchone()
        while row:
            key = ''.join(random.choices(characters, k=6))
            cur.execute("SELECT id FROM Room WHERE key = ?",(key,))
            row = cur.fetchone()
        return key
            
def get_room_id_by_key(key):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM Room WHERE key = ?", (key,))
        return cur.fetchone()[0]


def create_room(creator_id: int, is_closed: bool) -> Optional[int]:
    """
    Создает комнату ВСЕГДА с ключом, даже если она открытая
    Возвращает ID комнаты или None при ошибке
    """
    with connect() as conn:
        cur = conn.cursor()
        key = generate_random_key()  # Генерируем ключ ВСЕГДА

        cur.execute("""
            INSERT INTO Room (creator_id, key, status, created_at, is_closed)
            VALUES (?, ?, 'waiting', datetime('now'), ?)
        """, (creator_id, key, is_closed))

        room_id = cur.lastrowid
        conn.commit()
        return room_id


def find_open_room():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM Room 
            WHERE status = 'waiting' AND is_closed = 0
            LIMIT 1
        """)
        row = cur.fetchone()
        return row[0] if row else None


def start_game(room_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE Room SET status = 'active' WHERE id = ?", (room_id,))


async def finish_room(
        room_id: int,
        bot: Bot,
        storage: BaseStorage
) -> bool:
    """
    Завершает комнату, сбрасывает состояния всех участников,
    удаляет участников, задачи и саму комнату из базы данных.

    Args:
        room_id: ID комнаты для завершения
        bot: Экземпляр бота (для формирования StorageKey)
        storage: Хранилище состояний FSM

    Returns:
        bool: True если операция выполнена успешно
    """
    try:
        with connect() as conn:
            cur = conn.cursor()

            # Проверка: существует ли комната
            cur.execute("SELECT id FROM Room WHERE id = ?", (room_id,))
            if not cur.fetchone():
                return False

            # Получаем всех участников комнаты
            cur.execute("SELECT user_id FROM Room_Participants WHERE room_id = ?", (room_id,))
            participants = [row[0] for row in cur.fetchall()]

            # Удаляем участников комнаты
            cur.execute("DELETE FROM Room_Participants WHERE room_id = ?", (room_id,))

            # Удаляем задачи комнаты
            cur.execute("DELETE FROM Room_Tasks WHERE room_id = ?", (room_id,))

            # Удаляем саму комнату
            cur.execute("DELETE FROM Room WHERE id = ?", (room_id,))

            conn.commit()

        # Сброс FSM состояния и данных для участников
        for user_id in participants:
            try:
                key = StorageKey(
                    chat_id=user_id,
                    user_id=user_id,
                    bot_id=bot.id
                )
                await storage.set_state(key=key, state=None)
                await storage.set_data(key=key, data={})
            except Exception as e:
                print(f"Ошибка сброса состояния для пользователя {user_id}: {e}")
                continue

        return True

    except Exception as e:
        print(f"Ошибка при завершении комнаты {room_id}: {e}")
        return False
