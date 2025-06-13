from aiogram.types import ReplyKeyboardRemove
from app.handlers import *
import asyncio
from aiogram import Bot
from DataBase.DBConnect import connect
from typing import Optional
from DataBase.Tables.RoomTable import finish_room as async_finish_room
from DataBase.Tables.RoomTable import create_room as db_create_room
from aiogram.fsm.storage.base import StorageKey, BaseStorage
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

room_events: dict[int, asyncio.Event] = {} #room_id и событие для перехода к следующему вопросу после первого правильного ответа


async def create_room_in_db(user_id: int, is_closed: bool) -> Optional[int]:
    res = get_user_by_tg(user_id)
    if not res:
        print(f"[ERROR] Пользователь {user_id} не найден")
        return None
    
    room_id = db_create_room(user_id,is_closed)
    if room_id:
        print(f"[SUCCESS] Комната создана. ID: {room_id}")
        return room_id
    



async def notify_new_participant(room_id: int, new_user_id: int, bot: Bot):
    try:
        new_user_name = get_username_by_tg_id(new_user_id)
        existing_participants = get_room_participants_without_news(room_id,new_user_id)

        if existing_participants:
            participants_list = "👥 Уже в комнате:\n" + "\n".join(f"• {name}" for name in existing_participants)
            await bot.send_message(
                new_user_id,
                f"{participants_list}"
            )
        else:
            await bot.send_message(
                new_user_id,
                "✅ Вы присоединились к комнате! Ожидайте начала соревнования."
            )

        # Уведомление для остальных участников
        if existing_participants:
            message = f"🎉 Новый участник: {new_user_name}"
            user_ids = get_room_users_id(room_id)
            for user_id in user_ids:
                if user_id != new_user_id:
                    try:
                        await bot.send_message(user_id, message)
                    except Exception as e:
                        print(f"Ошибка уведомления о новом участнике: {e}")

    except Exception as e:
        print(f"Ошибка в notify_new_participant: {e}")


async def get_room_users(room_id: int) -> list[str]:
    return get_room_participants_without_news(room_id,0) #вместо new_user_id просто несуществующий id

async def add_user_in_random_room(user_id: int) -> Optional[int]:
    room_id = find_open_room()
    if room_id:
        join_room(user_id, room_id)
        return room_id
    return None


# def check_db_structure():
#     with connect() as conn:
#         cur = conn.cursor()
#         print("\n[Проверка БД]")

#         # Проверка таблицы User
#         cur.execute("PRAGMA table_info(User)")
#         print("Структура User:", cur.fetchall())

#         # Проверка таблицы Room
#         cur.execute("PRAGMA table_info(Room)")
#         print("Структура Room:", cur.fetchall())

#         # Проверка существования пользователя
#         cur.execute("SELECT id, user_tg_id FROM User WHERE user_tg_id = ?", (929645294,))
#         user = cur.fetchone()
#         print(f"Данные пользователя 929645294: {user}")

# def check_db_permissions():
#     try:
#         with connect() as conn:
#             cur = conn.cursor()
#             cur.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER)")
#             cur.execute("DROP TABLE test_table")
#             print("[Проверка] Права на запись в БД: OK")
#     except Exception as e:
#         print(f"[Проверка] Ошибка записи в БД: {e}")

async def add_user_in_closed_room(user_id: int, password: str) -> Optional[int]:
    room_id = get_room_id_by_key(password)
    if room_id:
        join_room(user_id, room_id)
        return room_id
    return None

async def deleting_user_from_competition(user_id: int, message: Message, state: FSMContext) -> bool:
    room_id = get_room_id_for_user(user_id)
    if room_id:
        remove_participant_from_room(room_id,user_id)

        res = get_room_participant_count(room_id)
        if res == 0:
            # Если комната пуста - закрываем ее
            await async_finish_room(
                room_id=room_id,
                bot=message.bot,  # или другой доступный экземпляр бота
                storage=state.storage
            )
        
        return True
    return False

async def save_task_in_room(room_id: int, task_id: int) -> bool:
    try:
        add_task_to_room(room_id, task_id)
        return True
    except Exception as e:
        print(f"Ошибка при добавлении задачи в комнату: {e}")
        return False


@comp_router.message(F.text == 'Начать соревнование')
async def start_competition(message: Message, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        room_id = data.get('room_id')
        count_tasks = data.get('count_tasks', 3)

        if not room_id:
            await message.answer("❌ Сначала создайте или войдите в комнату")
            return

        participants = get_room_users_id(room_id)
        if not participants:
            await message.answer("⚠️ В комнате нет участников")
            return

        participants_names = get_room_participants(room_id)
        participants_list = "👥 Участники соревнования:\n" + "\n".join(f"• {name}" for name in participants_names)

        for participant_id in participants:
            try:
                await bot.send_message(
                    participant_id,
                    f"🏁 Соревнование начинается!\n{participants_list}\n\nКоличество задач: {count_tasks}",
                    reply_markup=keyboards.exit_competition
                )
            except Exception as e:
                print(f"Ошибка уведомления участника {participant_id}: {e}")

        # Запускаем соревнование
        await run_competition_tasks(bot, room_id, participants, state, state.storage)

    except Exception as e:
        print(f"Ошибка при запуске соревнования: {e}")
        await message.answer("❌ Произошла ошибка")

async def run_competition_tasks(
        bot: Bot,
        room_id: int,
        users: list[int],
        state: FSMContext,
        storage: BaseStorage
):
    data = await state.get_data()
    count_tasks = data.get("count_tasks", 3)

    # Устанавливаем статус комнаты как 'active'
    start_game(room_id)

    for curr_index in range(1, count_tasks + 1):
        task = None
        max_attempts = 20  # ограничим количество попыток, чтобы не попасть в бесконечный цикл

        for _ in range(max_attempts):
            candidate = get_random_task()
            if not candidate:
                continue

            task_id, title, *_ = candidate
            if not is_in_room(room_id, task_id):
                task = candidate
                break  # нашли подходящую задачу

        if not task:
            await bot.send_message(users[0], "❌ Не удалось найти уникальную задачу.")
            continue

        task_id, title, *_ = task
        add_task_to_room(room_id, task_id)

        description = task[4]
        question = task[5]

        # Устанавливаем состояние waiting_for_answer для всех участников
        for user_id in users:
            participants = get_room_users_id(room_id)
            if not (user_id in participants):
                continue
            try:
                await bot.send_message(
                    user_id,

                    f"📝 Задание {curr_index}/{count_tasks}\n\n📌 *{title}*\n\n📝 *Описание:* {description} \n\n*❓ Вопрос:* {question} \n\n (Введите ответ сообщением)",
                    parse_mode='Markdown'
                )

                key = StorageKey(
                    chat_id=user_id,
                    user_id=user_id,
                    bot_id=bot.id
                )

                # Устанавливаем состояние через storage
                await storage.set_state(key=key, state=CompetitionStates.waiting_for_answer)
                await storage.set_data(key=key, data={
                    "room_id": room_id,
                    "task_id": task_id
                })

            except Exception as e:
                print(f"Ошибка отправки пользователю {user_id}: {e}")

        event = asyncio.Event()
        room_events[room_id] = event

        try:
            await asyncio.wait_for(event.wait(), timeout=15)
            participants = get_room_users_id(room_id)
            for user_id in participants:
                key = StorageKey(
                    chat_id=user_id,
                    user_id=user_id,
                    bot_id=bot.id
                )
                await storage.set_state(key=key, state=None)
        except asyncio.TimeoutError:
            pass  # время вышло, никто не ответил правильно
        finally:
            room_events.pop(room_id, None)  # очистим после вопроса
        
        await asyncio.sleep(2)

    # После завершения всех задач сбрасываем состояния
    participants = get_room_users_id(room_id)
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

    print(f"✅ Завершены все задания в комнате {room_id}. Вызываем show_final_results...")
    await show_final_results(bot, room_id, users, state)



async def increase_score(user_id: int, room_id: int, score_delta: int = 100):
    try:
        update_player_score(user_id, room_id, score_delta)
        return True
    except Exception as e:
        print(f"Ошибка при обновлении счета: {e}")
        return False

async def notify_room_members(bot: Bot, room_id: int, message: str, exclude_user_id: int = None):
    user_ids = get_room_users_id(room_id)
    for user_id in user_ids:
        if user_id != exclude_user_id:
            try:
                await bot.send_message(user_id, message)
            except Exception as e:
                print(f"Ошибка уведомления пользователя {user_id}: {e}")

async def add_creator_in_room(room_id: int) -> bool:
    try:
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
    return {1: 100, 2: 200, 3: 300}.get(difficulty, 100)


async def get_last_task_in_room_from_db(room_id: int) -> Optional[tuple]:
    task_id = get_last_task_in_room(room_id)
    if not task_id:
        return None
    return get_task_by_id(task_id)


@comp_router.message(CompetitionStates.waiting_for_answer)
async def handle_competition_answer(message: Message, state: FSMContext):


    if message.text == 'Выйти из соревнования':
        await exit_competition(message, state)
        return

    try:
        user_id = message.from_user.id
        user_answer = message.text.strip()
        data = await state.get_data()

        room_id = data.get("room_id")
        task_id = data.get("task_id")

        if not room_id or not task_id:
            await message.answer("⛔ Активное соревнование не найдено")
            await state.clear()
            return

        room_status_row = get_room_status(room_id)
        if not room_status_row:
            await message.answer("⛔ Комната не найдена")
            await state.clear()
            return

        room_status = room_status_row[0]

        if room_status != 'active':
            await message.answer("⛔ Соревнование не активно или уже завершено")
            await state.clear()
            return

        task_data = get_task_by_id(task_id)

        if not task_data:
            await message.answer("⛔ Задача не найдена")
            await state.clear()
            return

        _, title, _, difficulty, *_ = task_data

        # Проверяем ответ
        if check_answer(task_id, user_answer):
            # Начисляем очки с учетом сложности
            score = calculate_score(difficulty)

            save_attempt(user_id,task_id,1,0)
            update_player_score(user_id,room_id,score)
            update_user_score(user_id,score,True)

            await message.answer(f"✅ Верно! +{score} баллов")

            # Уведомляем создателя комнаты (если это не он сам)
            # participants — список user_id всех участников комнаты
            participants = get_room_users_id(room_id)
            for participant_id in participants:
                if participant_id != user_id:
                    try:
                        user_name = get_username_by_tg_id(user_id)
                        await message.bot.send_message(
                        participant_id,
                        f"🎯 Участник {user_name} правильно решил задачу '{title}'!\nПереходим к следующему вопросу"
                        )
                    except Exception as e:
                        print(f"Ошибка уведомления участника {participant_id}: {e}")
            
            event = room_events.get(room_id)
            if event and not event.is_set():
                event.set()

        else:
            await message.answer("❌ Неверный ответ. Попробуйте еще раз!")
            save_attempt(user_id,task_id,0,0)

    except Exception as e:
        print(f"Ошибка обработки ответа: {e}")
        await message.answer("⚠ Произошла ошибка при проверке ответа")
        await state.clear()


async def show_final_results(bot: Bot, room_id: int, users: list[int], state: FSMContext):
    participants = get_room_participants_with_score(room_id)
    results = {}
    for name, score in participants:
        if score not in results:
            results[score] = []
        results[score].append(name)

    message_lines = ["🏆 Итоговые результаты:"]
    for place, (score, names) in enumerate(sorted(results.items(), reverse=True), start=1):
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(place, '▫️')
        names_str = ", ".join(names)
        message_lines.append(f"{medal} {place}. {names_str} — {score} баллов")

    result_message = "\n".join(message_lines)

    for user_id in users:
        try:
            participants = get_room_users_id(room_id)
            if not (user_id in participants):
                continue
            await bot.send_message(
                user_id,
                result_message,
                reply_markup=keyboards.main_menu
            )
        except Exception as e:
            print(f"Ошибка отправки результатов пользователю {user_id}: {e}")

    await async_finish_room(
        room_id=room_id,
        bot=bot,
        storage=state.storage)

@comp_router.message(F.text == 'Выйти из соревнования')
async def exit_competition(message: Message, state: FSMContext):

    try:
        user_id = message.from_user.id
        room_id = get_room_id_for_user(user_id)

        if not room_id:
            await message.answer("❌ Вы не находитесь в комнате")
            return


        success = await deleting_user_from_competition(
            user_id=user_id,
            message=message,
            state=state
        )

        if not success:
            await message.answer("❌ Не удалось выйти из соревнования")
            return
   
        await state.clear()
  
        user_name = get_user_name_from_db(user_id)

        participants_count = get_room_participant_count(room_id)
        if participants_count > 0:
            await notify_room_members(
                bot=message.bot,
                room_id=room_id,
                message=f"⚠ Участник {user_name} покинул соревнование"
            )

        await message.answer(
            '✅ Вы успешно вышли из соревнования!',
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            'Вы вернулись в главное меню',
            reply_markup=keyboards.main_menu
        )

    except Exception as e:
        print(f"Ошибка при выходе из соревнования: {e}")
        await message.answer("❌ Произошла ошибка при выходе из комнаты")
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

        room_id = await create_room_in_db(
            user_id=user_id,
            is_closed=is_closed  # Передаём count_tasks в БД
        )

        if not room_id:
            await message.answer('❌ Не удалось создать комнату. Попробуйте позже.')
            await state.clear()
            return

        if is_closed:
            password = get_room_password(room_id)
            print(f"[DEBUG] Created room ID: {room_id}, Key: {password}")
            message_text = (
                f'✅ Вы создали закрытую комнату на *{count_tasks}* задач.\n'
                f'Код подключения: `{password}`\n\n'
                f'Отправьте этот код участникам для присоединения.'
            )
            await add_user_in_closed_room(user_id, password)
        else:
            password = get_room_password(room_id)
            print(f"[DEBUG] Created room ID: {room_id}, Key: {password}")
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
    user_id = message.from_user.id
    password = message.text.strip().upper()

    room = get_room_by_key_and_status(password)

    if not room:
        await message.answer("❌ Комната не найдена или игра уже началась")
        return

    room_id, is_closed = room

    if join_room(user_id, room_id):
        # Уведомляем о новом участнике

        room_type = "закрытой" if is_closed else "открытой"
        await message.answer(
            f"✅ Вы присоединились к {room_type} комнате!",
            reply_markup=keyboards.exit_competition
        )
        await notify_new_participant(room_id, user_id, message.bot)
    else:
        await message.answer("❌ Не удалось присоединиться")


@comp_router.callback_query(F.data == 'join_opened_room')
async def join_random_room(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    room_id = find_open_room()

    if not room_id:
        await callback.message.answer("❌ Нет доступных открытых комнат")
        return

    if join_room(user_id, room_id):
        # Уведомляем о новом участнике
        await notify_new_participant(room_id, user_id, callback.message.bot)

        await callback.message.answer(
            "✅ Вы присоединились к случайной комнате!",
            reply_markup=keyboards.exit_competition
        )
    else:
        await callback.message.answer("❌ Не удалось присоединиться")