from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.keyboards as keyboards

router = Router()

class User(StatesGroup): # user data for registration
    name = State()

class Task(StatesGroup):
    type = State()

class Answer(StatesGroup):
    answer = State()
    answer_type = State()


@router.message(CommandStart()) # decorator for \start message
async def command_start(message: Message, state: FSMContext):
    await message.answer('Привет! Это кибер-игра для студентов НИУ ВШЭ.\
\nЗдесь ты сможешь решать интересные задачи, разгадывать шифры\
 и соревноваться с другими пользователями')
    await state.set_state(User.name) # state for waiting entering name
    await message.answer('Прежде чем играть, нужно зарегистрироваться!\nКак тебя зовут?')

#ZAGLUSHKA for saving user in db
async def register_user(user_id: int, name: str) -> bool:
        # Controller sends user_id, name to db
        print(f"Регистрация пользователя {user_id} с именем '{name}'")
        return True
    
#ZAGLUSHKA for getting user name from db
async def get_user_name_from_db(user_id: int) -> str:
    # Controller sends user_id to db, gets name and sends to bot
    print(f"Получение имени для пользователя {user_id}")
    return "Твоё имя"

@router.message(Command('help')) # /help
async def send_game_rules(message: Message):
    await message.answer('Правила игры очень просты. Тебе нужно будет разгадывать разнообразные шифры, решая задачи.\n\
        \nЗа верное решение ты будешь получать баллы в зависимости от уровня сложности. Чем больше и труднее решишь, тем выше твой рейтинг среди других игроков.\
        \nУ каждой задачи есть подсказки. При их использовании количество баллов за решение снижается.\
        \nЧтобы посмотреть свой рейтинг - нажми на кнопку "Посмотреть статистику".\n\
        \nТы можешь играть один или участвовать в соревнованиях.\
        \nДля одиночной игры на клавиатуре есть команды:\
        \n"Случайная задача" - бот пришлёт тебе любую задачу из базы\
        \n"Задача из категории" - ты сможешь выбрать для себя задачу конкретного вида и уровня сложности\n\
        \nСоревнование позволяет состязаться в решении задач с другими пользователями на скорость.\
 Бот сам предложит задания и по количеству верных ответов и набранных баллов определит победителя.\
        \nТакая игра проходит в виртуальных комнатах, которые ты сможешь создавать сам или присоединиться к существующей.\
        \nЧтобы попробовать - нажми "Соревнование".\n\
        \nНапиши /help чтобы снова увидеть правила')
    
@router.message(User.name)
async def get_user_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text) # save username in User field name
    
    #ZAGLUSHKA for saving user in db
    registration_success = await register_user(user_id=message.from_user.id, name=message.text)
    
    #ZAGLUSHKA for getting user name from db
    user_name = await get_user_name_from_db(message.from_user.id)
    
    if registration_success:
        await message.answer(f'{user_name}, регистрация прошла успешно!', reply_markup=keyboards.main_menu) # open keyboard for user
        await send_game_rules(message)
    else:
        await message.answer('Ошибка регистрации!')
    await state.clear() # clear states

# tap on button "task from category"
@router.message(F.text == 'Задача из категории')
async def task_from_category(message: Message):
    await message.answer('Выберите сложность задачи', reply_markup=keyboards.task_from_category) # choosing complexity 

# if we choose any complexity, then we have a keyboard with choosing type of task
@router.callback_query(F.data == 'easy')
async def easy(callback: CallbackQuery, state: FSMContext):
    await state.update_data(complexity='лёгкую')
    await callback.message.answer('Выберите тип задачи', reply_markup=keyboards.choosing_type_of_task)
    await state.set_state(Task.type)

@router.callback_query(F.data == 'normal')
async def normal(callback: CallbackQuery, state: FSMContext):
    await state.update_data(complexity='среднюю')
    await callback.message.answer('Выберите тип задачи', reply_markup=keyboards.choosing_type_of_task)
    await state.set_state(Task.type)

@router.callback_query(F.data == 'hard')
async def hard(callback: CallbackQuery, state: FSMContext):
    await state.update_data(complexity='сложную')
    await callback.message.answer('Выберите тип задачи', reply_markup=keyboards.choosing_type_of_task)
    await state.set_state(Task.type)


# ZAGLUSHKA for giving task from category
# запрос к БД, выбор любой задачи с соответствующими характеристиками 
# заглушка для контроллера, на вход которой подаю сложность и тип задачи
async def giving_task_from_category(complexity: int, type: int) -> str:
    # Controller asks complexity and type of task from db
    print(f'Вы выбрали {complexity} задачу {type} типа. \nГенерируем...')


# choosing type of task, text about task added and after that we can write an answer 
@router.callback_query(Task.type)
async def choose_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    complexity = data.get('complexity')
    type = ''
    tmp_type = callback.data 
    if (tmp_type == 'symbol'):
        type = "символьного"
    else:
        type = "шифрового"
    await callback.message.answer(f'Вы выбрали {complexity} задачу {type} типа. \nГенерируем...')
    # calling ZAGLUSHKA for giving task from category
    task_complexity_and_type = await giving_task_from_category(complexity, type)
    await callback.message.answer(f'Вот ваша задача! (текст) \nВведите ответ сообщением')
    await state.set_state(Answer.answer)


# ZAGLUSHKA for giving random task
async def giving_random_task() -> str:
    # Controller asks text of task from db
    print(f'Вы выбрали случайную задачу. \nГенерируем...')


# if we choose random task, this message appear and after that we can write an answer 
@router.message(F.text == 'Случайная задача')
async def task_from_category(message: Message, state: FSMContext):
    await message.answer('Вы выбрали случайную задачу. \nГенерируем...')
    random_task = await giving_random_task()
    await message.answer('Вот ваша задача! (текст) \nВведите ответ сообщением')
    await state.set_state(Answer.answer)


# example of db 
correct_answers_db = {
    "444": "444",
    "lala": "lala"
}


# ZAGLUSHKA for getting answer from db
async def get_answer_from_db(correct_answer: str) -> str:
    # Controller sends user_id to db, gets name and sends to bot
    print(f"Получение правильного ответа к задаче: {correct_answer}")
    return correct_answers_db.get(correct_answer, "")
    # return "Правильный ответ"


# ZAGLUSHKA for giving hint
async def giving_hint() -> str:
    # Controller asks text of hint from db
    print(f'Вы выбрали подсказку.')
    return "подсказка"


# if we choose hint
@router.callback_query(F.data == "yes")
async def getting_hint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    hint_count = data.get("hint_count", 0) + 1  # count of used hints
    await state.update_data(hint_count=hint_count)
    if (hint_count > 3):
        await callback.message.answer("Количество подсказок иссякло. Сдаться?", reply_markup=keyboards.exit_game_after_hints_turn_zero)
    hint = await giving_hint()
    await callback.message.answer(f"{hint}")
    await state.set_state(Answer.answer)
    await callback.answer()


# if we choose to give up after having 0 hints
@router.callback_query(F.data == "give_up")
async def giving_up(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Вы можете заново выбрать игровой режим.")
    await state.clear()


# answer controller
@router.message(Answer.answer)
async def get_user_answer(message: Message, state: FSMContext):
    user_answer = message.text.strip()
    data = await state.get_data()
    correct_key = data.get("correct_key", "444")
    correct_answer = await get_answer_from_db(correct_key)
    if user_answer == correct_answer:
        await message.answer("Ответ верный! Вы получаете n баллов. \nМожете выбрать другую задачу или другой игровой режим")
        await state.clear()
    else:
        await message.answer("Ответ неверный! Попробуйте заново или возьмите подсказку.", reply_markup=keyboards.choosing_hint_or_not) # choosing hint 
            
    


    

