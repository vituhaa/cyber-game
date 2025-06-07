from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.handlers import *

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
    id_s = [5757254840, 612504339, 786083570, 783367128, 1159819601, 1362082185] # Вика, Соня, Илья
    names = []
    for i in range (len(id_s)):
        names.append(await get_user_name_from_db(id_s[i]))
    return names

# ZAGLUSHKA add user in random room
async def add_user_in_random_room(user_id: int) -> int:
    # function for finding random room 
    all_rooms = [123, 124, 125]
    random_room = random.choice(all_rooms)
    print(f'DEBUG: {random_room}')
    return random_room

@comp_router.message(F.text == 'Начать соревнование')
async def start_competition(message: Message):
    await message.answer('У вас есть пять минут на решение задач. Время пошло!')

@comp_router.message(F.text == "Выйти из соревнования")
async def exit_competition(message: Message):
    await message.answer('Вы вышли из режима соревнования!', reply_markup=ReplyKeyboardRemove())
    await message.answer('Вы вернулись в главное меню', reply_markup=keyboards.main_menu)

@comp_router.message(F.text == 'Соревнование')
async def choose_comp_format(message: Message):
    await message.answer('В этом режиме Вы сможете соревноваться в решении задач с другими игроками.\n'
                         'Соревнования проходят в виртуальных комнатах.\nВам доступен выбор:'
                         , reply_markup=keyboards.actions_with_room) # choosing competition format
    
@comp_router.callback_query(F.data == 'join_room')
async def choose_join_room_type(callback: CallbackQuery, state: FSMContext):
    context = 'join' # context for creating keyboard
    # await state.set_state(Room_States.in_room)
    await callback.message.answer('🔓  Если Вы выбираете случайную комнату, бот подключит Вас к игре с любыми участниками.\n'
                                  '🔐  При выборе входа по коду подключения, Вы присоединитесь к конкретной комнате, в которую Вас пригласили.\n'
                                  , reply_markup=keyboards.room_security)
    
@comp_router.callback_query(F.data == 'create_room')
async def choose_create_room_type(callback: CallbackQuery):
    context = 'create' # context for creating keyboard
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
        await state.update_data(in_room=True)
        # ZAGLUSHKA add user in random room
        await state.set_state(Room_States.in_room)
        await message.answer(f'✅  Вы создали открытую комнату на {count_tasks} задач и пока являетесь единственным игроком.\n'
                             'К вам смогут присоединиться любые участники, а также те, кому вы сообщите следующий код подключения:', reply_markup=ReplyKeyboardRemove())
        await message.answer(f'*{password}*', parse_mode='Markdown',  reply_markup=keyboards.start_competition)
        # await message.answer(f'Выберите действие:', reply_markup=keyboards.start_competition)
        await state.update_data(in_room=True)
        # room_id = 123
        # users_names = await get_room_users(room_id)
        # if users_names:
        #     participants = "В комнату добавились:\n" + "\n".join(users_names)
        #     await message.answer(participants)
        # else:
        #     await message.answer("В комнате пока никого нет.")
    elif success_creation and access_type == 1:
        await message.answer(f'✅  Вы создали закрытую комнату на {count_tasks} задач и пока являетесь единственным игроком.\n'
                             'Отправьте данный код подключения другим участникам, чтобы они смогли присоединиться:', reply_markup=ReplyKeyboardRemove())
        await message.answer(f'*{password}*', parse_mode='Markdown', reply_markup=keyboards.start_competition)
        # await message.answer(f'Выберите действие:', reply_markup=keyboards.start_competition)
    else:
        await message.answer('❌  Не удалось создать комнату.\n'
                             'Возможно Вы указали некорректное число задач')
    await state.clear()
    # VIKA, I DON'T KNOW WHERE TO INSERT "START THE GAME" AND "EXIT THE GAME" BUTTONS AND
    # WHEN HIDE THE MAIN MENU KEYBOARD
    
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
        await state.set_state(Room_States.in_room)
        await state.update_data(in_room=True)
        room_id = 123
        users_names = await get_room_users(room_id)
        if users_names:
            participants = "В комнате присутствуют:\n" + "\n".join(users_names)
            await message.answer(participants)
        else:
            await message.answer("В комнате пока никого нет.")
        await state.clear() 
        # VIKA, your logic (count players, count_tasks, ...)
    
    else:
        await message.answer('❌  Неверный пароль!\nПопробуйте ещё раз')
        await state.clear()
        await state.set_state(Join_Closed_Room.password)
       
    # VIKA, I DON'T KNOW WHERE TO INSERT "START THE GAME" AND "EXIT THE GAME" BUTTONS AND
    # WHEN HIDE THE MAIN MENU KEYBOARD
    
@comp_router.callback_query(F.data == 'join_opened_room')
async def join_opened_room(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('✅  Вы присоединились к комнате', reply_markup=ReplyKeyboardRemove())
    await callback.message.answer(f'Вы можете в любой момент покинуть соревнование.', reply_markup=keyboards.exit_competition)
    # ZAGLUSHKA add user in random room
    await state.set_state(Room_States.in_room)
    await state.update_data(in_room=True)
    room_id = 123
    # id_s = [5757254840, 612504339, 786083570, 783367128, 1159819601, 1362082185]
    # for i in range (len(id_s)):
    #     user_id = id_s[i]
    #     room_id = add_user_in_random_room(user_id)
    users_names = await get_room_users(room_id)
    if users_names:
        participants = "В комнате присутствуют:\n" + "\n".join(users_names)
        await callback.message.answer(participants)
    else:
        await callback.message.answer("В комнате пока никого нет.")
    # VIKA, your logic (count players, count_tasks, ...)