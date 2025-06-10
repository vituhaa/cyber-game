from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.handlers import *
import asyncio
from aiogram import Bot
from DataBase.DBConnect import connect
from typing import Optional


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

async def create_room_in_db(user_id: int, count_task: int, is_room_closed: bool) -> Optional[int]:
    """Создает комнату в БД и возвращает ID созданной комнаты"""
    try:
        key = generate_random_key()
        room_id = create_room(creator_id=user_id, key=key, is_closed=is_room_closed)
        return room_id
    except Exception as e:
        print(f"Ошибка при создании комнаты: {e}")
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
async def start_competition(message: Message, bot: Bot):
    id = message.from_user.id
    # ZAGLUSHKA for asking count_tasks from db
    count_tasks = await asking_for_count_tasks(id)
    
    # ZAGLUSHKA for getting room id from db for user in room
    room_id = await get_room_id_for_user(id)
    #room_id = 123 # !for example!
    users_in_competition = []
    users_in_competition = await get_room_users_id(room_id)

    for user_in_competition in users_in_competition:
        if user_in_competition == id:
            await bot.send_message(chat_id=user_in_competition, text = "Соревнование началось!", 
                                   reply_markup=ReplyKeyboardRemove())
            await bot.send_message(chat_id=user_in_competition, text="На решение каждой задачи у вас есть 7 минут. Время пошло!",
                                   reply_markup=keyboards.exit_competition)
        else:
            await bot.send_message(chat_id=user_in_competition, text = "Соревнование началось!")
            await bot.send_message(chat_id=user_in_competition, text="На решение каждой задачи у вас есть 7 минут. Время пошло!")

    await run_competition_tasks(bot, room_id, count_tasks, users_in_competition) # print tasks
    """ for curr_index in range(1, count_tasks + 1):
        task_number = f"Задание номер {curr_index}"
        for user_in_competition in users_in_competition:
            await bot.send_message(chat_id=user_in_competition, text=task_number)
        await asyncio.sleep(5)
            
    for user_in_competition in users_in_competition:
        await bot.send_message(chat_id=user_in_competition, text="Соревнование завершено!") """
    # await state.clear()

async def run_competition_tasks(bot: Bot, room_id: int, count_tasks: int, users: list[int]):
    for curr_index in range(1, count_tasks + 1):
        task_number = f"📝 Задание номер {curr_index}"
        task = get_random_task()
        task_id, title, type_id, difficulty, description, question, correct_answer, solution = task[:8]
        
        # ZAGLUSHKA for saving random task in room
        success_saving = await save_task_in_room(room_id, task_id)

        task_text = (
            f"📌 *{title}*\n\n"
            f"📝 *Описание:* {description}\n\n"
            f"❓ *Вопрос:* {question}\n\n"
            f"(Введите ваш ответ сообщением)"
        )
        for user_id in users:
            await bot.send_message(user_id, task_number)
            await bot.send_message(user_id, task_text, parse_mode='Markdown')
            #state = Dispatcher.get_current().fsm.get_context(bot=bot, chat_id=user_id, user_id=user_id)
            #await state.set_state(CompetitionStates.waiting_for_answer)
        # waiting for 7 minutes (420 seconds) or while all members answer
        await asyncio.sleep(5)
    
    await show_final_results(bot, room_id, users)
      

async def get_last_task_in_room_from_db(room_id: int):
    """Возвращает последнюю добавленную задачу в комнате"""
    task_id = get_last_task_in_room(room_id)
    if task_id:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Task WHERE id = ?", (task_id,))
            return cur.fetchone()
    return None

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
    
""" @comp_router.message()
async def handle_competition_answer(message: Message):
    user_id = message.from_user.id
    room_id = await get_room_id_for_user(user_id)
    if room_id is not None:
        user_answer = message.text
    
        # ZAGLUSHKA for getting the last task in room
        last_task = await get_last_task_in_room_from_db(room_id)
        
        if last_task is None:
            await message.answer("⛔️  Вы не можете отправить ответ на задачу!")
            return

        last_task_id = last_task[0]
        if check_answer(last_task_id, user_answer):
            # ZAGLUSHKA for increasing score for player
            success = await increase_score(user_id, room_id)
            await message.answer("✅  Верно!")
        else:
            await message.answer("❌  Неверно")
    else:
        return """

# ZAGLUSHKA for formation of the rating table
async def get_names_rating(room_id: int, users: list[int]) -> dict[int: list[str]]:
    # function from db, which return score by user id
    # EXAMPLE for output format and processing:
    # users = [5757254840, 612504339]
    score_table = {}
    score_table_ids = {}
    for user in users:
        # function from db, which return score by user_id
        user_score = random.randint(4, 5) # !for example!
        user_name = await get_user_name_from_db(user)
        if user_score not in score_table:
            score_table[user_score] = []
            score_table_ids[user_score] = []
            score_table[user_score].append(user_name)
            score_table_ids[user_score].append(user)
        else:
            score_table[user_score].append(user_name)
            score_table_ids[user_score].append(user)
    
    sorted_score_table = dict(sorted(score_table.items(), reverse=True))
    sorted_score_table_ids = dict(sorted(score_table_ids.items(), reverse=True))
    return sorted_score_table, sorted_score_table_ids

async def show_final_results(bot: Bot, room_id: int, users: list[int]):
    # ZAGLUSHKA for formation of the rating table
    users_rating = {} # dict score_1: [name_1, name_2, ...], score_2: [name_3], score_3: [name_4], ...
    users_rating, rating_ids = await get_names_rating(room_id, users)
    
    text_results = ''
    place = 1
    emoji = ''

    points = 500
    first_plase_score = 0
    for score in users_rating:
        if place == 1:
            emoji = '🥇'
            # ZAGLUSHKA for add +point to winners
            # for example for only 1st place
            for id in rating_ids[score]:
                update_user_score(user_tg_id=id, score_delta=points, increment_solved=False)
            first_place_score = score
        elif place == 2:
            emoji = '🥈'
        elif place == 3:
            emoji = '🥉'
        else:
            emoji = '🔹️'
        place_users = ", ".join(users_rating[score])
        place_info = f'{emoji}  {place} место: {place_users}\n\n'
        text_results += place_info
        place += 1
    
    for user_id in users:
        await bot.send_message(user_id, "Игра окончена!\nРезультаты соревнования:")
        await bot.send_message(user_id, text_results)
        if user_id in rating_ids[first_place_score]:
            await bot.send_message(user_id, f"Поздравляем! Вы зарабатываете {points} баллов!")


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
        count_tasks = int(message.text)
        if count_tasks <= 0:
            raise ValueError
    except ValueError:
        await message.answer('❌ Пожалуйста, введите корректное число задач (больше 0)')
        return

    user_id = message.from_user.id
    room_data = await state.get_data()
    room_type = room_data.get("room_type")

    # Создаем комнату в БД
    room_id = await create_room_in_db(user_id, count_tasks, room_type == 'closed')
    if not room_id:
        await message.answer('❌ Не удалось создать комнату. Попробуйте позже')
        await state.clear()
        return

    # Получаем пароль комнаты
    password = await get_room_password(room_id)

    # Сообщаем пользователю
    room_type_text = "открытую" if room_type == 'opened' else "закрытую"
    await message.answer(
        f'✅ Вы создали {room_type_text} комнату на {count_tasks} задач.\n'
        f'Код подключения: *{password}*',
        parse_mode='Markdown',
        reply_markup=keyboards.start_competition
    )

    await state.update_data(room_id=room_id, in_room=True)
    await state.set_state(Room_States.in_room)
    
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