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

        # 2. Проверка существования пользователя
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM User WHERE user_tg_id = ?", (user_id,))
            if not cur.fetchone():
                print(f"[ERROR] Пользователь {user_id} не найден в базе")
                return None

        # 3. Создание комнаты
        print("[DEBUG] Вызов db_create_room...")
        room_id = db_create_room(creator_id=user_id, is_closed=is_closed)
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
    """Обработчик начала соревнования в комнате."""
    try:
        user_id = message.from_user.id
        data = await state.get_data()
        room_id = data.get('room_id')
        count_tasks = data.get('count_tasks', 3)  # Берём из состояния

        if not room_id:
            await message.answer("❌ Сначала создайте или войдите в комнату")
            return

        participants = await get_room_users_id(room_id)
        if not participants:
            await message.answer("⚠️ В комнате нет участников")
            return

        # Уведомляем участников
        for user_id in participants:
            await bot.send_message(
                user_id,
                f"🏁 Соревнование начинается!\nКоличество задач: {count_tasks}",
                reply_markup=keyboards.exit_competition
            )

        # Передаём state в run_competition_tasks
        await run_competition_tasks(bot, room_id, participants, state)

    except Exception as e:
        print(f"Ошибка при запуске соревнования: {e}")
        await message.answer("❌ Произошла ошибка")


async def run_competition_tasks(bot: Bot, room_id: int, users: list[int], state: FSMContext):
    """Запускает задачи в комнате на основе указанного количества."""
    data = await state.get_data()
    count_tasks = data.get("count_tasks", 3)  # По умолчанию 3, если не указано

    for curr_index in range(1, count_tasks + 1):  # Используем count_tasks
        task = get_random_task()
        if not task:
            await bot.send_message(users[0], "❌ Не удалось получить задачу.")
            continue

        task_id, title, *_ = task
        add_task_to_room(room_id, task_id)

        task_text = f"📝 Задание {curr_index}/{count_tasks}\n📌 *{title}*\n(Введите ответ сообщением)"

        for user_id in users:
            try:
                await bot.send_message(user_id, task_text, parse_mode='Markdown')
            except Exception as e:
                print(f"Ошибка отправки пользователю {user_id}: {e}")

        await asyncio.sleep(15)  # Таймер на решение задачи

    await show_final_results(bot, room_id, users)


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


async def show_final_results(bot: Bot, room_id: int, users: list[int]):
    """
    Формирует и выводит итоговые результаты соревнования в формате:
    {
        баллы: [список участников],
        ...
    }
    """
    # 1. Получаем данные участников
    participants = []
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT U.name, RP.score 
            FROM Room_Participants RP
            JOIN User U ON RP.user_id = U.user_tg_id
            WHERE RP.room_id = ?
            ORDER BY RP.score DESC
        """, (room_id,))
        participants = cur.fetchall()

    if not participants:
        await bot.send_message(
            users[0],
            "⚠ Нет данных об участниках"
        )
        return

    # 2. Создаем словарь {баллы: [имена]}
    results = {}
    for name, score in participants:
        if score not in results:
            results[score] = []
        results[score].append(name)

    # 3. Форматируем вывод
    message_lines = ["🏆 Итоговые результаты:"]
    for place, (score, names) in enumerate(sorted(results.items(), reverse=True), start=1):
        # Определяем медаль для места
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(place, '▫️')
        names_str = ", ".join(names)
        message_lines.append(f"{medal} {place}. {names_str} — {score} баллов")

    result_message = "\n".join(message_lines)

    # 4. Отправляем всем участникам
    for user_id in users:
        try:
            await bot.send_message(
                user_id,
                result_message,
                reply_markup=keyboards.main_menu
            )
        except Exception as e:
            print(f"Ошибка отправки результатов пользователю {user_id}: {e}")

    # 5. Обновляем статус комнаты
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE Room SET status = 'finished' 
            WHERE id = ?
        """, (room_id,))
        conn.commit()


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
        # Проверяем, что введено корректное число задач
        try:
            count_tasks = int(message.text)
            if count_tasks <= 0:
                await message.answer('❌ Число задач должно быть больше 0!')
                return
        except ValueError:
            await message.answer('❌ Введите число (например, 3, 5, 10)!')
            return

        user_id = message.from_user.id
        room_data = await state.get_data()
        room_type = room_data.get("room_type")
        is_closed = (room_type == 'closed')

        # Создаём комнату с указанным количеством задач
        room_id = await create_room_in_db(
            user_id=user_id,
            is_closed=is_closed,
            task_count=count_tasks  # Передаём count_tasks в БД
        )

        if not room_id:
            await message.answer('❌ Не удалось создать комнату. Попробуйте позже.')
            await state.clear()
            return

        # Формируем сообщение в зависимости от типа комнаты
        if is_closed:
            password = await get_room_password(room_id)
            message_text = (
                f'✅ Вы создали закрытую комнату на *{count_tasks}* задач.\n'
                f'Код подключения: `{password}`\n\n'
                f'Отправьте этот код участникам для присоединения.'
            )
            await add_user_in_closed_room(user_id, password)
        else:
            password = await get_room_password(room_id)
            message_text = (
                f'✅ Вы создали открытую комнату на *{count_tasks}* задач.\n'
                f'Код подключения: `{password}`\n\n'
                f'Участники могут присоединиться случайно или по коду.'
            )

        await message.answer(
            message_text,
            parse_mode='Markdown',
            reply_markup=keyboards.start_competition
        )

        # Добавляем создателя в комнату
        await add_creator_in_room(room_id)
        await state.update_data(room_id=room_id, count_tasks=count_tasks)
        await state.set_state(Room_States.in_room)

    except Exception as e:
        print(f"Ошибка при создании комнаты: {e}")
        await message.answer('❌ Произошла ошибка при создании комнаты.')
        await state.clear()
    
@comp_router.callback_query(F.data == 'join_closed_room')
async def enter_password(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Join_Closed_Room.password)
    await callback.message.answer('Введите код подключения, чтобы войти в комнату')
    await callback.answer()


@comp_router.message(Join_Closed_Room.password)
async def join_by_password(message: Message, state: FSMContext):
    """Поиск комнаты по коду (проверяет ВСЕ комнаты)"""
    user_id = message.from_user.id
    password = message.text.strip()

    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, is_closed FROM Room 
            WHERE key = ? AND status = 'waiting'
        """, (password,))
        room = cur.fetchone()

    if not room:
        await message.answer("❌ Комната не найдена или игра уже началась")
        return

    room_id, is_closed = room
    if join_room(user_id, room_id):
        room_type = "закрытой" if is_closed else "открытой"
        await message.answer(
            f"✅ Вы присоединились к {room_type} комнате!",
            reply_markup=keyboards.exit_competition
        )
    else:
        await message.answer("❌ Не удалось присоединиться")


@comp_router.callback_query(F.data == 'join_opened_room')
async def join_random_room(callback: CallbackQuery, state: FSMContext):
    """Присоединение к любой открытой комнате в статусе waiting"""
    user_id = callback.from_user.id

    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM Room 
            WHERE is_closed = 0 AND status = 'waiting'
            LIMIT 1
        """)
        room = cur.fetchone()

    if not room:
        await callback.message.answer("❌ Нет доступных открытых комнат")
        return

    room_id = room[0]
    if join_room(user_id, room_id):
        await callback.message.answer(
            "✅ Вы присоединились к случайной комнате!",
            reply_markup=keyboards.exit_competition
        )
    else:
        await callback.message.answer("❌ Не удалось присоединиться")