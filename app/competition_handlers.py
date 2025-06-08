from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.handlers import *
import asyncio
from aiogram import Bot

import app.keyboards as keyboards

comp_router = Router()

class Join_Closed_Room(StatesGroup): # join the closed room
    password = State()
    
class Create_Room(StatesGroup): # create room
    room_type = State() # opened/closed
    count_tasks = State() # in room

class Room_States(StatesGroup):
    in_room = State()

# ZAGLUSHKA for creating room in db
async def create_room_in_db(user_id: int, count_task: int, is_room_closed: int) -> bool:
    # function to create closed room in db
    # and check count task in room
    # if is_room_closed == 1: room is closed
    # elif is_room_closed == 0: room is opened
    is_room_created = True
    return is_room_created
        
# ZAGLUSHKA for sending room password
async def get_room_password() -> str:
    # function to generate random password
    password = "cUtIe105"
    return password

# ZAGLUSHKA for checking password for room
async def check_password(password: str) -> bool:
    is_correct = False
    # logic to compare password
    
    if password == "cUtIe105":
        is_correct = True
    return is_correct

# ZAGLUSHKA for having people's names who are in room
async def get_room_users(room_id: int) -> list[str]:
    # function for finding people who are in room right now
    id_s = [5757254840, 612504339] # Вика, Соня, Илья
    names = []
    for i in range (len(id_s)):
        names.append(await get_user_name_from_db(id_s[i]))
    return names

async def get_room_users_id(room_id: int) -> list[str]:
    return [5757254840, 612504339]

# ZAGLUSHKA add user in random room
async def add_user_in_random_room(user_id: int) -> int:
    # function for finding random opened room in db:
    all_rooms = [123, 124, 125]
    random_room = random.choice(all_rooms)
    print(f'DEBUG: {random_room}')
    return random_room

# ZAGLUSHKA add user in closed room
async def add_user_in_closed_room(user_id: int) -> int:
    # function for finding random closed room in db:
    all_closed_rooms = [123, 124, 125]
    random_room = random.choice(all_closed_rooms)
    print(f'DEBUG: {random_room}')
    return random_room

# ZAGLUSHKA for sending list of all closed rooms ids
async def get_all_closed_rooms_ids() -> list[int]:
    # function for sending all closed rooms ids in db
    closed_rooms_ids = []
    return closed_rooms_ids

# ZAGLUSHKA for sending list of all opened rooms ids
async def get_all_opened_rooms_ids() -> list[int]:
    # function for sending all opened rooms ids in db
    opened_rooms_ids = []
    return opened_rooms_ids

# ZAGLUSHKA for asking count_tasks from db
async def asking_for_count_tasks(user_id: int) -> int:
    # function for asking count_tasks
    count = 5
    return count

# ZAGLUSHKA for getting room id from db for user in room
async def get_room_id_for_user(id: int) -> int:
    # function for finding user in room
    room_id = 123
    return room_id

# ZAGLUSHKA for deleting user from room for taping "Exit competition"
async def deleting_user_from_competition(user_id: int) -> int:
    return True

# ZAGLUSHKA for saving random task in room
async def save_task_in_room(room_id: int, task) -> bool:
    # function in db for saing task in db
    save = True
    return save

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

async def run_competition_tasks(bot: Bot, room_id: int, count_tasks: int, users: list):
    for curr_index in range(1, count_tasks + 1):
        task_number = f"📝 Задание номер {curr_index}"
        task = get_random_task()
        task_id, title, type_id, difficulty, description, question, correct_answer, solution = task[:8]
        
        # ZAGLUSHKA for saving random task in room
        success_saving = await save_task_in_room(room_id, task)

        task_text = (
            f"📌 *{title}*\n\n"
            f"📝 *Описание:* {description}\n\n"
            f"❓ *Вопрос:* {question}\n\n"
            f"(Введите ваш ответ сообщением)"
        )
        for user_id in users:
            await bot.send_message(user_id, task_number)
            await bot.send_message(user_id, task_text, parse_mode='Markdown')
            
        # waiting for 7 minutes (420 seconds) or while all members answer
        await asyncio.sleep(5)
        
        # ZAGLUSHKA for checking answers
        # await check_answers(room_id, task_id)
    
    # await show_final_results(bot, room_id, users)
    
#async def check_answers(room_id: int, task_id: int) ->    

# ZAGLUSHKA for checking user in competitions
async def is_user_in_competition(user_id: int) -> bool:
    # function from db for checking that user in room 
    in_competition = True
    return in_competition

""" @comp_router.message(lambda message: is_user_in_competition(message.from_user.id))
async def handle_competition_answer(message: Message):
    user_id = message.from_user.id
    room_id = await get_room_id_for_user(user_id) """
    

@comp_router.message(F.text == "Выйти из соревнования")
async def exit_competition(message: Message):
    user_id = message.from_user.id
    # ZAGLUSHKA for deleting user from room for taping "Exit competition"
    success_exit = await deleting_user_from_competition(user_id)
    if success_exit:
        await message.answer('Вы вышли из режима соревнования!', reply_markup=ReplyKeyboardRemove())
        await message.answer('Вы вернулись в главное меню', reply_markup=keyboards.main_menu)

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
async def create_room(message: Message, state: FSMContext): # common function for closed and opened room
    await state.update_data(count_tasks=message.text) # save count_tasks in Create_Room field count_tasks
    user_id = message.from_user.id
    room_data = await state.get_data() # Create_Room class info
    room_type = room_data.get("room_type")
    count_tasks = room_data.get("count_tasks")
    password = ''
    access_type = 0 # opened room
    
    await state.set_state(Room_States.in_room)

    success_creation = False
    
    if room_type == 'opened':
        # ZAGLUSHKA for creating room in db
        success_creation = await create_room_in_db(user_id, count_tasks, access_type) # 0 - argument for opened room
        # ZAGLUSHKA for sending room password
        password = await get_room_password()
    
    elif room_type == 'closed':
        access_type = 1
        # ZAGLUSHKA for creating room in db
        success_creation = await create_room_in_db(user_id, count_tasks, access_type) # 1 - argument for closed room
        # ZAGLUSHKA for sending room password
        password = await get_room_password()
    
    if success_creation and access_type == 0:
        await state.update_data(in_room=True) # now user is in room
        # ZAGLUSHKA add user in random room
        # room_id = await add_user_in_random_room(user_id)
        await state.set_state(Room_States.in_room)
        await message.answer(f'✅  Вы создали открытую комнату на {count_tasks} задач и пока являетесь единственным игроком.\n'
                             'К вам смогут присоединиться любые участники, а также те, кому вы сообщите следующий код подключения:', reply_markup=ReplyKeyboardRemove())
        await message.answer(f'*{password}*', parse_mode='Markdown',  reply_markup=keyboards.start_competition)
        await state.update_data(in_room=True) # now user is in room
    elif success_creation and access_type == 1:
        await state.update_data(in_room=True) # now user is in room
        # ZAGLUSHKA add user in closed room
        # room_id = await add_user_in_closed_room(user_id)
        await state.set_state(Room_States.in_room)
        await message.answer(f'✅  Вы создали закрытую комнату на {count_tasks} задач и пока являетесь единственным игроком.\n'
                             'Отправьте данный код подключения другим участникам, чтобы они смогли присоединиться:', reply_markup=ReplyKeyboardRemove())
        await message.answer(f'*{password}*', parse_mode='Markdown', reply_markup=keyboards.start_competition)
        await state.update_data(in_room=True) # now user is in room
    else:
        await message.answer('❌  Не удалось создать комнату.\n'
                             'Возможно Вы указали некорректное число задач')
    await state.clear()
    
@comp_router.callback_query(F.data == 'join_closed_room')
async def enter_password(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Join_Closed_Room.password)
    await callback.message.answer('Введите код подключения, чтобы войти в комнату')
    await callback.answer()
    
@comp_router.message(Join_Closed_Room.password)
async def join_closed_room(message: Message, state: FSMContext):
    await state.update_data(password=message.text) # save password in Join_Closed_Room field password
    room_data = await state.get_data() # Join_Closed_Room class info
    password = room_data.get("password")
    
    # ZAGLUSHKA for checking password for room
    is_correct_password = await check_password(password)
    
    if is_correct_password:
        await message.answer('✅  Вы присоединились к комнате', reply_markup=ReplyKeyboardRemove())
        await message.answer(f'Вы можете в любой момент покинуть соревнование.', reply_markup=keyboards.exit_competition)
        # ZAGLUSHKA add user in closed room
        # room_id = await add_user_in_closed_room(user_id)
        await state.set_state(Room_States.in_room)
        await state.update_data(in_room=True) # now user is in room
        
        # ZAGLUSHKA for sending list of all closed rooms ids
        # closed_rooms_ids = await get_all_closed_rooms_ids()
        # for room_id in closed_rooms_ids:
        #     users_names = await get_room_users(room_id)
        #     if users_names:
        #         participants = "В комнате присутствуют:\n" + "\n".join(users_names)
        #         await message.answer(participants)
        #     else:
        #         await message.answer("В комнате пока никого нет.")
        room_id = 123 # !for example!
        users_names = await get_room_users(room_id)
        if users_names:
            participants = "В комнате присутствуют:\n" + "\n".join(users_names)
            await message.answer(participants)
        else:
            await message.answer("В комнате пока никого нет.")
        await state.clear() 
    
    else:
        await message.answer('❌  Неверный пароль!\nПопробуйте ещё раз')
        await state.clear()
        await state.set_state(Join_Closed_Room.password)
    
@comp_router.callback_query(F.data == 'join_opened_room')
async def join_opened_room(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('✅  Вы присоединились к комнате', reply_markup=ReplyKeyboardRemove())
    await callback.message.answer(f'Вы можете в любой момент покинуть соревнование.', reply_markup=keyboards.exit_competition)
    # ZAGLUSHKA add user in random room
    # room_id = await add_user_in_random_room(user_id)
    await state.set_state(Room_States.in_room)
    await state.update_data(in_room=True)
    
    # ZAGLUSHKA for sending list of all opened rooms ids
    # opened_rooms_ids = await get_all_opened_rooms_ids()
    # for room_id in opened_rooms_ids:
    #     users_names = await get_room_users(room_id)
    #     if users_names:
    #         participants = "В комнате присутствуют:\n" + "\n".join(users_names)
    #         await message.answer(participants)
    #     else:
    #         await message.answer("В комнате пока никого нет.")
    
    room_id = 123 # !for example!
    # id_s = [5757254840, 612504339, 786083570, 783367128, 1159819601, 1362082185] # !for example!
    users_names = await get_room_users(room_id)
    if users_names:
        participants = "В комнате присутствуют:\n" + "\n".join(users_names)
        await callback.message.answer(participants)
    else:
        await callback.message.answer("В комнате пока никого нет.")