from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.keyboards as keyboards

comp_router = Router()

class Join_Closed_Room(StatesGroup): # join the closed room
    password = State()
    
class Create_Room(StatesGroup): # create room
    room_type = State() # opened/closed
    count_tasks = State() # in room

# ZAGLUSHKA for creating room in db
async def create_room_in_db(user_id: int, count_task: int) -> bool:
    # function to create closed room in db
    # and check count task in room
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

@comp_router.message(F.text == 'Соревнование')
async def choose_comp_format(message: Message):
    await message.answer('В этом режиме Вы сможете соревноваться в решении задач с другими игроками.\n'
                         'Соревнования проходят в виртуальных комнатах.\nВам доступен выбор:'
                         , reply_markup=keyboards.actions_with_room) # choosing competition format
    
@comp_router.callback_query(F.data == 'join_room')
async def choose_join_room_type(callback: CallbackQuery):
    context = 'join' # context for creating keyboard
    await callback.message.answer('🔓  Если Вы выбираете открытую комнату, бот подключит вас к случайной с любыми участниками.\n'
                                  '🔐  При выборе закрытой, нужно будет ввести пароль, чтобы присоединиться.\n'
                                  , reply_markup=keyboards.get_room_type_keyboard(context))
    
@comp_router.callback_query(F.data == 'create_room')
async def choose_create_room_type(callback: CallbackQuery):
    context = 'create' # context for creating keyboard
    await callback.message.answer('🔓  Если Вы создаёте открытую комнату, к ней смогут подключиться любые участники.\n'
                                  '🔐  При выборе закрытой, участники смогут получить доступ к комнате только по паролю.\n'
                                  , reply_markup=keyboards.get_room_type_keyboard(context))
    
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
    
    # ZAGLUSHKA for creating room in db
    success_creation = await create_room_in_db(user_id, count_tasks)
    
    if room_type == 'closed':
        # ZAGLUSHKA for sending room password
        password = await get_room_password()
    
    if success_creation and password == '':
        await message.answer(f'✅  Вы создали открытую комнату на {count_tasks} задач и пока являетесь единственным игроком.\n'
                             'Подождите, другие участники скоро присоединятся')
    elif success_creation and password != '':
        await message.answer(f'✅  Вы создали закрытую комнату на {count_tasks} задач и пока являетесь единственным игроком.\n'
                             'Отправьте данный пароль другим участникам, чтобы они смогли присоединиться:\n\n'
                             f'*{password}*', parse_mode='Markdown')
    else:
        await message.answer('❌  Не удалось создать комнату.\n'
                             'Возможно Вы указали некорректное число задач')
    await state.clear()
    # VIKA, I DON'T KNOW WHERE TO INSERT "START THE GAME" AND "EXIT THE GAME" BUTTONS AND
    # WHEN HIDE THE MAIN MENU KEYBOARD
    
@comp_router.callback_query(F.data == 'join_closed_room')
async def enter_password(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Join_Closed_Room.password)
    await callback.message.answer('Введите пароль, чтобы войти в комнату')
    await callback.answer()
    
@comp_router.message(Join_Closed_Room.password)
async def join_closed_room(message: Message, state: FSMContext):
    await state.update_data(password=message.text) # save password in Join_Closed_Room field password
    room_data = await state.get_data() # Join_Closed_Room class info
    password = room_data.get("password")
    
    # ZAGLUSHKA for checking password for room
    is_correct_password = await check_password(password)
    
    if is_correct_password:
        await message.answer('✅  Вы присоединились к закрытой комнате')
        await state.clear() 
        # VIKA, your logic (count players, count_tasks, ...)
    
    else:
        await message.answer('❌  Неверный пароль!\nПопробуйте ещё раз')
        await state.clear()
        await state.set_state(Join_Closed_Room.password)
       
    # VIKA, I DON'T KNOW WHERE TO INSERT "START THE GAME" AND "EXIT THE GAME" BUTTONS AND
    # WHEN HIDE THE MAIN MENU KEYBOARD
    
@comp_router.callback_query(F.data == 'join_opened_room')
async def join_opened_room(callback: CallbackQuery):
    await callback.message.answer('✅  Вы присоединились к открытой комнате')
    # VIKA, your logic (count players, count_tasks, ...)