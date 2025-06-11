from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.handlers import *
import asyncio
from aiogram import Bot
from DataBase.DBConnect import connect
from typing import Optional, Any
from DataBase.Tables.RoomTable import create_room as db_create_room


import app.keyboards as keyboards

comp_router = Router()

class Join_Closed_Room(StatesGroup): # join the closed room
    password = State()
    
class Create_Room(StatesGroup): # create room
    room_type = State() # opened/closed
    count_tasks = State() # in room

class Room_States(StatesGroup):
    in_room = State()
    
class CompetitionStates(StatesGroup):
    waiting_for_answer = State()


async def create_room_in_db(user_id: int, is_closed: bool, task_count: int = None) -> Optional[int]:
    """Создает комнату с полным логированием всех этапов"""
    print(f"\n[DEBUG] Начало создания комнаты. Параметры: user_id={user_id}, is_closed={is_closed}, task_count={task_count}")

    try:
        # 1. Генерация ключа ТОЛЬКО для закрытых комнат
        key = generate_random_key() if is_closed else None
        if is_closed:
            print(f"[DEBUG] Сгенерирован ключ комнаты: {key}")
        else:
            print("[DEBUG] Создается открытая комната (без ключа)")

        # 2. Проверка существования пользователя
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM User WHERE user_tg_id = ?", (user_id,))
            if not cur.fetchone():
                print(f"[ERROR] Пользователь {user_id} не найден в базе")
                return None

        # 3. Создание комнаты
        print("[DEBUG] Вызов db_create_room...")
        room_id = db_create_room(creator_id=user_id, is_closed=is_closed, key=key)
        print(f"[DEBUG] Результат db_create_room: {room_id}")

        if not room_id:
            print("[ERROR] db_create_room вернул None без исключения")
            return None

        # 4. Сохранение количества задач (если указано)
        if task_count:
            print(f"[DEBUG] Пытаюсь сохранить task_count={task_count} для комнаты {room_id}")
            try:
                with connect() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE Room SET task_count = ? 
                        WHERE id = ?
                    """, (task_count, room_id))
                    conn.commit()
                    print("[DEBUG] Количество задач успешно сохранено")
            except Exception as e:
                print(f"[WARNING] Ошибка сохранения task_count: {e}")
                # Не прерываем выполнение, т.к. комната уже создана

        print(f"[SUCCESS] Комната успешно создана. ID: {room_id}")
        return room_id

    except Exception as e:
        print(f"[CRITICAL ERROR] Исключение при создании комнаты:")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Сообщение: {str(e)}")
        print("Трассировка:")
        import traceback
        traceback.print_exc()
        return None
        
async def get_room_password(room_id: int) -> str:
    """Возвращает ключ комнаты из БД"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT key FROM Room WHERE id = ?", (room_id,))
        result = cur.fetchone()
        return result[0] if result else None

async def check_password(password: str) -> bool:
    """Проверяет существование комнаты с таким паролем"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM Room WHERE key = ?", (password,))
        return cur.fetchone() is not None

async def get_room_users(room_id: int) -> list[str]:
    """Возвращает список имен участников комнаты"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT U.name FROM Room_Participants RP
            JOIN User U ON RP.user_id = U.user_tg_id
            WHERE RP.room_id = ?
        """, (room_id,))
        return [row[0] for row in cur.fetchall()]

async def get_room_users_id(room_id: int) -> list[int]:
    """Возвращает ID участников комнаты"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM Room_Participants WHERE room_id = ?", (room_id,))
        return [row[0] for row in cur.fetchall()]

async def add_user_in_random_room(user_id: int) -> Optional[int]:
    """Добавляет пользователя в случайную открытую комнату"""
    room_id = find_open_room()
    if room_id:
        join_room(user_id, room_id)
        return room_id
    return None


def check_db_structure():
    with connect() as conn:
        cur = conn.cursor()
        print("\n[Проверка БД]")

        # Проверка таблицы User
        cur.execute("PRAGMA table_info(User)")
        print("Структура User:", cur.fetchall())

        # Проверка таблицы Room
        cur.execute("PRAGMA table_info(Room)")
        print("Структура Room:", cur.fetchall())

        # Проверка существования пользователя
        cur.execute("SELECT id, user_tg_id FROM User WHERE user_tg_id = ?", (929645294,))
        user = cur.fetchone()
        print(f"Данные пользователя 929645294: {user}")


check_db_structure()

def check_db_permissions():
    try:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER)")
            cur.execute("DROP TABLE test_table")
            print("[Проверка] Права на запись в БД: OK")
    except Exception as e:
        print(f"[Проверка] Ошибка записи в БД: {e}")

check_db_permissions()

async def add_user_in_closed_room(user_id: int, password: str) -> Optional[int]:
    """Добавляет пользователя в закрытую комнату по паролю"""
    with connect() as conn:
        cur = conn.cursor()
        # Находим комнату по ключу
        cur.execute("SELECT id FROM Room WHERE key = ? AND is_closed = 1", (password,))
        room = cur.fetchone()
        if room:
            room_id = room[0]
            join_room(user_id, room_id)
            return room_id
        return None

async def get_all_closed_rooms_ids() -> list[int]:
    """Возвращает список ID всех закрытых комнат в статусе waiting"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM Room 
            WHERE is_closed = 1 AND status = 'waiting'
        """)
        return [row[0] for row in cur.fetchall()]

async def get_all_opened_rooms_ids() -> list[int]:
    """Возвращает список ID всех открытых комнат в статусе waiting"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM Room 
            WHERE is_closed = 0 AND status = 'waiting'
        """)
        return [row[0] for row in cur.fetchall()]

async def asking_for_count_tasks(user_id: int) -> int:
    """Возвращает рекомендуемое количество задач на основе статистики пользователя"""
    with connect() as conn:
        cur = conn.cursor()
        # Получаем количество решенных пользователем задач
        cur.execute("""
            SELECT solved_count FROM User 
            WHERE user_tg_id = ?
        """, (user_id,))
        result = cur.fetchone()
        if result:
            solved_count = result[0]
            # Рекомендуем больше задач опытным пользователям
            if solved_count > 50:
                return 7
            elif solved_count > 20:
                return 5
        return 3  # Значение по умолчанию

async def get_room_id_for_user(user_id: int) -> int:
    """Возвращает ID комнаты, в которой находится пользователь"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT room_id FROM Room_Participants 
            WHERE user_id = ?
        """, (user_id,))
        result = cur.fetchone()
        return result[0] if result else None


async def deleting_user_from_competition(user_id: int) -> bool:
    """Удаляет пользователя из комнаты"""
    with connect() as conn:
        cur = conn.cursor()
        # Находим комнату пользователя
        cur.execute("SELECT room_id FROM Room_Participants WHERE user_id = ?", (user_id,))
        room = cur.fetchone()
        if room:
            room_id = room[0]
            # Удаляем пользователя
            cur.execute("DELETE FROM Room_Participants WHERE user_id = ? AND room_id = ?",
                        (user_id, room_id))
            conn.commit()

            # Проверяем, остались ли участники
            cur.execute("SELECT COUNT(*) FROM Room_Participants WHERE room_id = ?", (room_id,))
            if cur.fetchone()[0] == 0:
                # Если комната пуста - закрываем ее
                finish_room(room_id)
            return True
        return False

async def save_task_in_room(room_id: int, task_id: int) -> bool:
    """Добавляет задачу в комнату"""
    try:
        add_task_to_room(room_id, task_id)
        return True
    except Exception as e:
        print(f"Ошибка при добавлении задачи в комнату: {e}")
        return False


@comp_router.message(F.text == 'Начать соревнование')
async def start_competition(message: Message, state: FSMContext, bot: Bot):
    """Обработчик начала соревнования в комнате"""
    try:
        user_id = message.from_user.id
        print(f"\n[DEBUG] Начало соревнования для пользователя {user_id}")

        # 1. Получаем данные из состояния
        data = await state.get_data()
        room_id = data.get('room_id')
        count_tasks = data.get('count_tasks', 3)  # Значение по умолчанию

        # 2. Проверка существования комнаты
        if not room_id:
            print("[ERROR] room_id не найден в состоянии")
            await message.answer("❌ Сначала создайте или войдите в комнату")
            return

        # 3. Получаем список участников
        try:
            participants = await get_room_users_id(room_id)
            if not participants:
                await message.answer("⚠️ В комнате нет участников")
                return

            print(f"[DEBUG] Участники комнаты {room_id}: {participants}")
        except Exception as e:
            print(f"[ERROR] Ошибка получения участников: {e}")
            await message.answer("❌ Ошибка получения списка участников")
            return

        # 4. Проверка количества задач
        if not isinstance(count_tasks, int) or count_tasks <= 0:
            count_tasks = 3  # Значение по умолчанию
            print("[WARNING] Некорректное количество задач, установлено значение по умолчанию")

        # 5. Уведомление участников
        try:
            for user_id in participants:
                await bot.send_message(
                    user_id,
                    "🏁 Соревнование начинается!\n"
                    f"Количество задач: {count_tasks}\n"
                    "На решение каждой задачи - 5 минут",
                    reply_markup=keyboards.exit_competition
                )
        except Exception as e:
            print(f"[ERROR] Ошибка уведомления участников: {e}")

        # 6. Запуск задач
        try:
            await run_competition_tasks(bot, room_id, count_tasks, participants)
        except Exception as e:
            print(f"[CRITICAL] Ошибка в run_competition_tasks: {e}")
            await message.answer("❌ Критическая ошибка при запуске задач")
            import traceback
            traceback.print_exc()

        # 7. Обновление состояния комнаты
        try:
            with connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE Room SET status = 'finished' WHERE id = ?",
                    (room_id,)
                )
                conn.commit()
        except Exception as e:
            print(f"[ERROR] Ошибка обновления статуса комнаты: {e}")

    except Exception as e:
        print(f"[UNHANDLED ERROR] Необработанное исключение: {e}")
        await message.answer("⚠️ Произошла непредвиденная ошибка")
    finally:
        await state.set_state(None)


async def run_competition_tasks(bot: Bot, room_id: int, count_tasks: int, users: list[int]):
    if not room_id:
        print("[ERROR] Передан пустой room_id!")
        return

    print(f"[DEBUG] Начало соревнования в комнате {room_id}")

    for curr_index in range(1, count_tasks + 1):
        task = get_random_task()
        if not task:
            await bot.send_message(users[0], "❌ Не удалось получить задачу")
            continue

        task_id, title, *_ = task  # Распаковка задачи

        # Явная проверка перед сохранением
        if not isinstance(room_id, int) or room_id <= 0:
            print(f"[ERROR] Некорректный room_id: {room_id}")
            continue

        try:
            # Добавляем задачу в комнату
            add_task_to_room(room_id, task_id)
            print(f"[DEBUG] Задача {task_id} добавлена в комнату {room_id}")

            # Отправка задачи участникам
            task_text = f"📌 *{title}*\n\n(Введите ответ сообщением)"
            for user_id in users:
                try:
                    await bot.send_message(
                        user_id,
                        f"📝 Задание {curr_index}/{count_tasks}\n{task_text}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"[ERROR] Ошибка отправки пользователю {user_id}: {e}")

            await asyncio.sleep(15)  # Таймер на решение

        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Ошибка БД при добавлении задачи: {e}")
            await bot.send_message(
                users[0],
                "⚠️ Техническая ошибка при загрузке задачи"
            )

    await show_final_results(bot, room_id, users)
      

'''async def get_last_task_in_room_from_db(room_id: int):
    """Возвращает последнюю добавленную задачу в комнате"""
    task_id = get_last_task_in_room(room_id)
    if task_id:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Task WHERE id = ?", (task_id,))
            return cur.fetchone()
    return None'''

async def increase_score(user_id: int, room_id: int, score_delta: int = 100):
    """Увеличивает счет игрока в комнате"""
    try:
        update_player_score(user_id, room_id, score_delta)
        return True
    except Exception as e:
        print(f"Ошибка при обновлении счета: {e}")
        return False

async def notify_room_members(bot: Bot, room_id: int, message: str, exclude_user_id: int = None):
    """Отправляет сообщение всем участникам комнаты"""
    user_ids = await get_room_users_id(room_id)
    for user_id in user_ids:
        if user_id != exclude_user_id:
            try:
                await bot.send_message(user_id, message)
            except Exception as e:
                print(f"Ошибка уведомления пользователя {user_id}: {e}")


def get_room_creator(room_id: int) -> Optional[int]:
    """Возвращает ID создателя комнаты"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT creator_id FROM Room WHERE id = ?", (room_id,))
        result = cur.fetchone()
        return result[0] if result else None


async def add_creator_in_room(room_id: int) -> bool:
    """
    Добавляет создателя комнаты как участника

    Args:
        room_id: ID комнаты

    Returns:
        bool: True если добавление прошло успешно
    """
    try:
        # Получаем создателя комнаты
        creator_id = get_room_creator(room_id)
        if not creator_id:
            return False

        # Добавляем создателя в комнату
        join_room(creator_id, room_id)
        return True

    except Exception as e:
        print(f"Error adding creator to room: {e}")
        return False


def calculate_score(difficulty: int) -> int:
    """Вычисляет количество очков за задачу"""
    return {1: 100, 2: 200, 3: 300}.get(difficulty, 100)


async def get_last_task_in_room_from_db(room_id: int) -> Optional[tuple]:
    """Возвращает последнюю задачу в комнате"""
    task_id = get_last_task_in_room(room_id)
    if not task_id:
        return None

    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Task WHERE id = ?", (task_id,))
        return cur.fetchone()

@comp_router.message(CompetitionStates.waiting_for_answer)
async def handle_competition_answer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_answer = message.text.strip()

    try:
        # 1. Получаем данные о комнате пользователя
        room_id = await get_room_id_for_user(user_id)
        if not room_id:
            await message.answer("⛔ Вы не участвуете в активном соревновании")
            return

        # 2. Получаем текущую задачу
        last_task = await get_last_task_in_room_from_db(room_id)
        if not last_task:
            await message.answer("⛔ Нет активных задач для ответа")
            return

        task_id, title, _, _, _, _, correct_answer, _ = last_task

        # 3. Проверяем ответ
        if check_answer(task_id, user_answer):
            # Начисляем очки с учетом сложности
            difficulty = get_task_difficulty(task_id)
            score = calculate_score(difficulty)  # 100, 200, 300 для easy, normal, hard

            # Обновляем статистику
            with connect() as conn:
                cur = conn.cursor()
                # Добавляем попытку
                cur.execute("""
                    INSERT INTO Task_Attempt (user_id, task_id, is_correct, used_hints, solved_at)
                    VALUES (?, ?, 1, 0, datetime('now'))
                """, (user_id, task_id))

                # Обновляем счет в комнате
                cur.execute("""
                    UPDATE Room_Participants 
                    SET score = score + ? 
                    WHERE user_id = ? AND room_id = ?
                """, (score, user_id, room_id))

                conn.commit()

            await message.answer(f"✅ Верно! +{score} баллов")

            # Уведомляем создателя комнаты
            creator_id = get_room_creator(room_id)
            if creator_id and creator_id != user_id:
                user_name = await get_user_name_from_db(user_id)
                try:
                    await message.bot.send_message(
                        creator_id,
                        f"🎯 Участник {user_name} правильно решил задачу '{title}'"
                    )
                except Exception as e:
                    print(f"Ошибка уведомления создателя: {e}")

        else:
            await message.answer("❌ Неверный ответ")
            # Фиксируем неудачную попытку
            with connect() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO Task_Attempt (user_id, task_id, is_correct, used_hints, solved_at)
                    VALUES (?, ?, 0, 0, datetime('now'))
                """, (user_id, task_id))
                conn.commit()

    except Exception as e:
        print(f"Ошибка обработки ответа: {e}")
        await message.answer("⚠ Произошла ошибка при проверке ответа")


def calculate_places(scores: tuple[dict[int, list[str]], dict[int, list[int]]]) -> list[
    tuple[int, int, list[str], list[int]]]:
    """
    Добавляет места к рейтингу

    Args:
        scores: Кортеж из (словарь_рейтинга, словарь_id)

    Returns:
        Список кортежей: (место, баллы, [имена], [ID])
    """
    score_dict, id_dict = scores
    return [
        (place, score, names, id_dict[score])
        for place, (score, names) in enumerate(
            sorted(score_dict.items(), key=lambda x: x[0], reverse=True),
            start=1
        )
    ]

async def format_rating_table(room_id: int) -> str:
    """
    Форматирует рейтинг в красивый текст
    """
    users = await get_room_users_id(room_id)
    scores, score_ids = await get_names_rating(room_id, users)

    if not scores:
        return "Рейтинг пока недоступен"

    table = ["🏆 Текущий рейтинг:"]
    for place, (score, names, _) in enumerate(calculate_places((scores, score_ids)), start=1):
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(place, '🔹')
        table.append(f"{medal} {place}. {', '.join(names)} - {score} баллов")

    return '\n'.join(table)

async def get_names_rating(room_id: int, users: list[int]) -> tuple[dict[int, list[str]], dict[int, list[int]]]:
    """
    Формирует рейтинговую таблицу участников комнаты

    Args:
        room_id: ID комнаты
        users: Список ID участников

    Returns:
        Кортеж из двух словарей:
        1. {баллы: [имена]}
        2. {баллы: [ID пользователей]}
        Оба словаря отсортированы по убыванию баллов
    """
    score_table = {}
    score_table_ids = {}

    with connect() as conn:
        cur = conn.cursor()

        # Получаем текущие баллы всех участников
        cur.execute("""
            SELECT user_id, score 
            FROM Room_Participants 
            WHERE room_id = ? AND user_id IN ({})
            ORDER BY score DESC
        """.format(','.join('?' for _ in users)), [room_id] + users)

        results = cur.fetchall()

        if not results:
            return {}, {}

        # Формируем словари рейтинга
        for user_id, score in results:
            user_name = await get_user_name_from_db(user_id)

            if score not in score_table:
                score_table[score] = []
                score_table_ids[score] = []

            score_table[score].append(user_name)
            score_table_ids[score].append(user_id)

    # Сортируем по убыванию баллов
    sorted_score_table = dict(sorted(score_table.items(), key=lambda x: x[0], reverse=True))
    sorted_score_table_ids = dict(sorted(score_table_ids.items(), key=lambda x: x[0], reverse=True))

    return sorted_score_table, sorted_score_table_ids


async def show_final_results(bot: Bot, room_id: int, users: list[int]):
    """
    Показывает финальные результаты соревнования с использованием вспомогательных функций
    """
    try:
        # 1. Получаем отформатированную таблицу рейтинга
        rating_text = await format_rating_table(room_id)
        if "недоступен" in rating_text:
            raise ValueError("Не удалось получить рейтинг")

        # 2. Получаем детальные данные для начисления баллов
        users_rating, rating_ids = await get_names_rating(room_id, users)
        places_data = calculate_places((users_rating, rating_ids))

        # 3. Награждаем победителей
        reward_points = {1: 500, 2: 300, 3: 100}

        for place, score, names, user_ids in places_data[:3]:  # Только первые 3 места
            for user_id in user_ids:
                try:
                    update_player_score(user_id, room_id, reward_points[place])
                    update_user_score(
                        user_tg_id=user_id,
                        score_delta=reward_points[place],
                        increment_solved=False
                    )
                except Exception as e:
                    print(f"Ошибка начисления баллов {user_id}: {e}")

        # 4. Отправляем результаты всем участникам
        for user_id in users:
            try:
                # Основное сообщение с рейтингом
                await bot.send_message(
                    user_id,
                    f"🏁 Соревнование завершено!\n\n{rating_text}",
                    parse_mode='Markdown'
                )

                # Персональное сообщение для призеров
                user_place = next(
                    (place for place, _, _, ids in places_data if user_id in ids),
                    None
                )

                if user_place in reward_points:
                    await bot.send_message(
                        user_id,
                        f"🎉 Вы заняли {user_place} место и получаете {reward_points[user_place]} баллов!",
                        reply_markup=keyboards.main_menu
                    )

            except Exception as e:
                print(f"Ошибка отправки сообщения {user_id}: {e}")

        # 5. Обновляем статус комнаты
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE Room SET status = 'finished' 
                WHERE id = ?
            """, (room_id,))
            conn.commit()

    except Exception as e:
        print(f"Ошибка в show_final_results: {e}")
        creator_id = get_room_creator(room_id)
        if creator_id:
            await bot.send_message(
                creator_id,
                "⚠ При подсчете результатов произошла ошибка",
                reply_markup=keyboards.main_menu
            )


@comp_router.message(F.text == "Выйти из соревнования")
async def exit_competition(message: Message, state: FSMContext):
    user_id = message.from_user.id
    room_id = await get_room_id_for_user(user_id)

    if room_id:
        # Удаляем пользователя из комнаты
        remove_participant_from_room(room_id, user_id)

        # Проверяем, остались ли участники
        participants_count = get_room_participant_count(room_id)

        await message.answer('Вы вышли из соревнования!',
                             reply_markup=ReplyKeyboardRemove())
        await message.answer('Вы вернулись в главное меню',
                             reply_markup=keyboards.main_menu)

        # Уведомляем остальных участников
        if participants_count > 0:
            user_name = await get_user_name_from_db(user_id)
            await notify_room_members(
                bot=message.bot,
                room_id=room_id,
                message=f"Участник {user_name} покинул соревнование"
            )
    else:
        await message.answer('Вы не находитесь в комнате')

    await state.clear()

@comp_router.message(F.text == 'Соревнование')
async def choose_comp_format(message: Message):
    await message.answer('В этом режиме Вы сможете соревноваться в решении задач с другими игроками.\n'
                         'Соревнования проходят в виртуальных комнатах.\nВам доступен выбор:'
                         , reply_markup=keyboards.actions_with_room) # choosing competition format
    
@comp_router.callback_query(F.data == 'join_room')
async def choose_join_room_type(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('🔓  Если Вы выбираете случайную комнату, бот подключит Вас к игре с любыми участниками.\n'
                                  '🔐  При выборе входа по коду подключения, Вы присоединитесь к конкретной комнате, в которую Вас пригласили.\n'
                                  , reply_markup=keyboards.room_security)
    
@comp_router.callback_query(F.data == 'create_room')
async def choose_create_room_type(callback: CallbackQuery):
    await callback.message.answer('🔓  Если Вы создаёте открытую комнату, к ней смогут подключиться любые участники, а также те, кому Вы дадите код подключения.\n'
                                  '🔐  При выборе закрытой, участники смогут получить доступ к комнате только по коду.\n'
                                  , reply_markup=keyboards.room_type)
    
@comp_router.callback_query(F.data == 'create_closed_room') # closed room
async def enter_count_tasks_closed_room(callback: CallbackQuery, state: FSMContext):
    await state.update_data(room_type='closed')
    await state.set_state(Create_Room.count_tasks)
    await callback.message.answer('Сколько задач подготовить для соревнования?')
    await callback.answer()
    
@comp_router.callback_query(F.data == 'create_opened_room') # opened room
async def enter_count_tasks_opened_room(callback: CallbackQuery, state: FSMContext):
    await state.update_data(room_type='opened')
    await state.set_state(Create_Room.count_tasks)
    await callback.message.answer('Сколько задач подготовить для соревнования?')
    await callback.answer()


@comp_router.message(Create_Room.count_tasks)
async def create_room(message: Message, state: FSMContext, bot: Bot):
    try:
        # Проверка количества задач
        try:
            count_tasks = int(message.text)
            if count_tasks <= 0:
                raise ValueError
        except ValueError:
            await message.answer('❌ Пожалуйста, введите корректное число задач (больше 0)')
            return

        user_id = message.from_user.id
        room_data = await state.get_data()
        room_type = room_data.get("room_type")
        is_closed = (room_type == 'closed')

        # Создаем комнату в БД (ключ передаем только для закрытых комнат)
        room_id = await create_room_in_db(
            user_id=user_id,
            is_closed=is_closed,
            task_count=count_tasks
        )

        if not room_id:
            await message.answer('❌ Не удалось создать комнату. Попробуйте позже')
            await state.clear()
            return

        # Формируем сообщение в зависимости от типа комнаты
        if is_closed:
            # Получаем пароль только для закрытой комнаты
            password = await get_room_password(room_id)
            message_text = (
                f'✅ Вы создали закрытую комнату на {count_tasks} задач.\n'
                f'Код подключения: *{password}*\n\n'
                f'Отправьте этот код участникам для присоединения'
            )
            await add_user_in_closed_room(user_id, password)
        else:
            message_text = (
                f'✅ Вы создали открытую комнату на {count_tasks} задач.\n'
                f'Участники могут присоединиться через меню соревнований'
            )

        await message.answer(
            message_text,
            parse_mode='Markdown' if is_closed else None,
            reply_markup=keyboards.start_competition
        )

        add = await add_creator_in_room(room_id)
        if add:
            await message.answer('✅ Вы присоединились к комнате!', reply_markup=keyboards.start_competition)

        await state.update_data(room_id=room_id, in_room=True)
        await state.set_state(Room_States.in_room)

    except Exception as e:
        print(f"Ошибка при создании комнаты: {e}")
        await message.answer('❌ Произошла ошибка при создании комнаты')
        await state.clear()
    
@comp_router.callback_query(F.data == 'join_closed_room')
async def enter_password(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Join_Closed_Room.password)
    await callback.message.answer('Введите код подключения, чтобы войти в комнату')
    await callback.answer()


@comp_router.message(Join_Closed_Room.password)
async def join_closed_room(message: Message, state: FSMContext, bot: Bot):
    password = message.text.strip()
    user_id = message.from_user.id

    # Используем реальную проверку пароля
    room_id = await add_user_in_closed_room(user_id, password)

    if room_id:
        await message.answer('✅ Вы успешно присоединились к комнате!',
                             reply_markup=keyboards.exit_competition)

        # Получаем список участников
        participants = await get_room_users(room_id)
        if participants:
            participants_text = "Участники комнаты:\n" + "\n".join(participants)
            await message.answer(participants_text)

        # Уведомляем других участников
        user_name = await get_user_name_from_db(user_id)
        await notify_room_members(bot, room_id, f"Новый участник: {user_name}")

        await state.update_data(room_id=room_id, in_room=True)
        await state.set_state(Room_States.in_room)
    else:
        await message.answer('❌ Неверный код комнаты или комната не существует')
        await state.set_state(Join_Closed_Room.password)  # Повторный запрос пароля


@comp_router.callback_query(F.data == 'join_opened_room')
async def join_opened_room(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id

    # Используем реальную функцию добавления
    room_id = await add_user_in_random_room(user_id)

    if room_id:
        await callback.message.answer('✅ Вы присоединились к открытой комнате!',
                                      reply_markup=keyboards.exit_competition)

        # Получаем информацию о комнате
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM Room_Participants 
                WHERE room_id = ? AND user_id != ?
            """, (room_id, user_id))
            other_participants = cur.fetchone()[0]

        if other_participants > 0:
            participants = await get_room_users(room_id)
            await callback.message.answer(f"Участники комнаты:\n{', '.join(participants)}")

            # Уведомляем других участников
            user_name = await get_user_name_from_db(user_id)
            await notify_room_members(bot, room_id, f"Новый участник: {user_name}", user_id)
        else:
            await callback.message.answer("Вы первый участник в комнате!")

        await state.update_data(room_id=room_id, in_room=True)
        await state.set_state(Room_States.in_room)
    else:
        await callback.message.answer('❌ Нет доступных открытых комнат. Создайте свою!')
        await callback.answer()