from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from DataBase.Tables.HintTable import *
from DataBase.Tables.RoomParticipants import *
from DataBase.Tables.RoomTable import *
from DataBase.Tables.RoomTasksTable import *
from DataBase.Tables.TaskTable import *
from DataBase.Tables.TaskTypeTable import *
from DataBase.Tables.TaskAttemptsTable import *
from DataBase.Tables.UserTable import *


import app.keyboards as keyboards

router = Router()

class User(StatesGroup): # user data for registration
    name = State()

class Task(StatesGroup):
    type = State()

class Answer(StatesGroup):
    answer = State()
    answer_type = State()


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    user_name = await get_user_name_from_db(user_id)
    await state.update_data(user_id=user_id)

    if user_name and user_name != "Имя не найдено":
        await message.answer(f'Рады видеть Вас снова, {user_name}!', reply_markup=keyboards.main_menu)
        await send_game_rules(message)
        await state.clear()
    else:
        await message.answer(
            'Привет! Это кибер-игра для студентов НИУ ВШЭ.\n'
            'Здесь ты сможешь решать интересные задачи, разгадывать шифры '
            'и соревноваться с другими пользователями'
        )
        await state.set_state(User.name)
        await message.answer('Прежде чем играть, нужно зарегистрироваться!\nКак тебя зовут?')


async def register_user(user_id: int, name: str) -> bool:
    print(f"Регистрация пользователя {user_id} с именем '{name}'")
    try:
        get_or_create_user(user_id, name)
        return True
    except Exception as e:
        print(f"Ошибка при регистрации пользователя: {e}")
        return False
    
async def get_user_name_from_db(user_id: int) -> str:
    print(f"Получение имени для пользователя {user_id}")
    try:
        name = get_username_by_tg_id(user_id)
        return name if name else "Имя не найдено"
    except Exception as e:
        print(f"Ошибка при получении имени пользователя: {e}")
        return "Ошибка"

@router.message(Command('help')) # /help
async def send_game_rules(message: Message):
    await message.answer('Правила игры очень просты. Вам нужно будет разгадывать разнообразные шифры, решая задачи.\n\
        \n⭐️  За верное решение Вы будете получать баллы в зависимости от уровня сложности. Чем больше и труднее решите, тем выше Ваш рейтинг среди других игроков.\
        \n💡  У каждой задачи есть подсказки. При их использовании количество баллов за решение снижается.\
        \n💯  Чтобы посмотреть свой рейтинг - нажмите на кнопку "Посмотреть статистику".\n\
        \nВы можете играть один или участвовать в соревнованиях.\
        \nДля одиночной игры на клавиатуре есть команды:\
        \n❓️  "Случайная задача" - бот пришлёт Вам любую задачу из базы.\
        \n✔️  "Задача из категории" - Вы сможете выбрать для себя задачу конкретного вида и уровня сложности.\n\
        \nСоревнование позволяет состязаться в решении задач с другими пользователями на скорость.\
 Бот сам предложит задания и по количеству верных ответов и набранных баллов определит победителя.\
        \nТакая игра проходит в виртуальных комнатах, которые Вы сможете создавать сами или присоединиться к существующей.\
        \n🏆  Чтобы попробовать - нажмите "Соревнование".\n\
        \nНапишите /help чтобы снова увидеть правила')
    
@router.message(User.name)
async def get_user_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text) # save username in User field name
    
    registration_success = await register_user(user_id=message.from_user.id, name=message.text)
    
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


async def giving_task_from_category(callback: CallbackQuery, state: FSMContext, complexity: str, type_name: str):
    """
    complexity: строка 'лёгкую', 'среднюю', 'сложную'
    """
    type_name_map = {
        "шифрового": "cipher",
        "символьного": "symbol"
    }

    difficulty_map = {'лёгкую': 1, 'среднюю': 2, 'сложную': 3}
    difficulty = difficulty_map.get(complexity)
    print(f"[DEBUG] giving_task_from_category: complexity='{complexity}' -> difficulty={difficulty}, type_name='{type_name}'")

    if difficulty is None:
        await callback.message.answer("Не удалось распознать сложность задачи.")
        return

    db_type_name = type_name_map.get(type_name)
    if db_type_name is None:
        await callback.message.answer("Неизвестный тип задачи.")
        return

    type_id = get_type_id_by_name(db_type_name)
    print(f"[DEBUG] giving_task_from_category: type_id для '{db_type_name}' = {type_id}")

    if type_id is None:
        await callback.message.answer("Не удалось найти тип задачи в базе данных.")
        return

    print(f"[DEBUG] giving_task_from_category: пытаемся получить задачу с type_id={type_id} и difficulty={difficulty}")
    task = get_task_by_category_and_difficulty(type_id, difficulty)
    print(f"[DEBUG] giving_task_from_category: задача из базы: {task}")

    if task is None:
        await callback.message.answer("Не удалось найти задачу с указанными параметрами.")
        return

    task_id, title, type_id, difficulty, description, question, correct_answer, solution = task[:8]

    await state.update_data(task_id=task_id)
    await state.update_data(user_id=callback.from_user.id)
    await state.update_data(hint_count=0, hints_exhausted=False)

    task_text = (
        f"📌 *{title}*\n\n"
        f"📝 *Описание:* {description}\n\n"
        f"❓ *Вопрос:* {question}\n\n"
        f"(Введите Ваш ответ сообщением)"
    )
    await callback.message.answer(task_text, parse_mode='Markdown')
    await state.set_state(Answer.answer)


async def get_task_solution_from_db(task_id: int) -> str:
    try:
        solution = get_task_solution(task_id)
        return solution if solution else "Решение не найдено."
    except Exception as e:
        print(f"[ERROR] Не удалось получить решение задачи {task_id}: {e}")
        return "Произошла ошибка при получении решения."


@router.callback_query(Task.type)
async def choose_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    complexity = data.get('complexity')
    print(f"[DEBUG] choose_type: complexity из state = '{complexity}'")


    tmp_type = callback.data
    if tmp_type == 'symbol':
        type_name = "символьного"
    else:
        type_name = "шифрового"

    await callback.message.answer(f'Вы выбрали {complexity} задачу {type_name} типа. \nГенерируем...')
    await state.update_data(user_id=callback.from_user.id)

    await giving_task_from_category(callback, state, complexity, type_name)



@router.message(F.text == 'Случайная задача')
async def task_from_category(message: Message, state: FSMContext):
    await message.answer('Вы выбрали случайную задачу. \nГенерируем...')

    task = get_random_task()
    print(task)
    if task is None:
        await message.answer("Не удалось найти задачу в базе данных.")
        return

    task_id, title, type_id, difficulty, description, question, correct_answer, solution = task[:8]

    await state.update_data(task_id=task_id)
    await state.update_data(user_id=message.from_user.id)
    await state.update_data(hint_count=0, hints_exhausted=False)

    task_text = (
        f"📌 *{title}*\n\n"
        f"📝 *Описание:* {description}\n\n"
        f"❓ *Вопрос:* {question}\n\n"
        f"(Введите ваш ответ сообщением)"
    )
    await message.answer(task_text, parse_mode='Markdown')
    await state.set_state(Answer.answer)



async def giving_hint(state: FSMContext) -> str:
    data = await state.get_data()
    task_id = data.get("task_id")
    hint_count = data.get("hint_count", 0)  # hint_count уже увеличен в основном хэндлере
    hints_exhausted = data.get("hints_exhausted", False)
    
    if hints_exhausted:
        return "🔒 Все подсказки уже использованы для этой задачи!"

    hint = get_hint_by_taskid_ordernum(task_id, hint_count)
    if hint:
        text, penalty = hint
        return f"💡 Подсказка: {text}\n\n💸 Штраф: -{penalty} баллов"
    else:
        return "🔒 Все подсказки уже использованы для этой задачи!"

async def are_there_any_hints(task_id: int, hint_count: int) -> bool: # checking hints
    hint = get_hint_by_taskid_ordernum(task_id, hint_count + 1)
    return hint is not None
    
@router.callback_query(F.data == "yes")
async def getting_hint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    hint_count = data.get("hint_count", 0)
    hints_exhausted = data.get("hints_exhausted", False)
    
    if hints_exhausted:
        await callback.message.answer(
            "🔒 Количество подсказок иссякло. Сдаться?",
            reply_markup=keyboards.exit_game_after_hints_turn_zero
        )
        await callback.answer()
        return
    
    if not await are_there_any_hints(task_id, hint_count):
        await state.updade_data(hints_exhausted=True)
        await callback.message.answer(
            "🔒 Количество подсказок иссякло. Сдаться?",
            reply_markup=keyboards.exit_game_after_hints_turn_zero
        )
        await callback.answer()
        return

    hint_count += 1
    await state.update_data(hint_count=hint_count)
    hint = get_hint_by_taskid_ordernum(task_id, hint_count)
    if hint:
        text, penalty = hint
        update_user_score(user_id, -penalty)
        print(user_id, penalty)
        await callback.message.answer(
            f"💡 Подсказка: {text}\n\n💸 Штраф: -{penalty} баллов"
        )
    else:
        await state.update_data(hints_exhausted=True)
        await callback.message.answer(
            "🔒 Количество подсказок иссякло. Сдаться?",
            reply_markup=keyboards.exit_game_after_hints_turn_zero
        )
    await state.set_state(Answer.answer)
    await callback.answer()



@router.callback_query(F.data == "give_up")
async def giving_up(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    
    solution = await get_task_solution_from_db(task_id)
    
    await callback.message.answer(f"Вот разбор решения задачи:\n{solution}")
    await callback.message.answer("Теперь Вы можете заново выбрать игровой режим.")
    await state.clear()


@router.message(Answer.answer)
async def comparing_answer(message: Message, state: FSMContext):
    user_answer = message.text.strip()
    data = await state.get_data()
    task_id = data.get("task_id")
    hint_count = data.get("hint_count", 0)
    hints_exhausted = data.get("hints_exhausted", False)

    if task_id is None:
        await message.answer("Ошибка: ID задачи не найден.")
        return

    # Если ответ верный — начисляем очки и увеличиваем счётчик задач
    if check_answer(task_id, user_answer):
        # 1) Берём сложность задачи из БД (1, 2 или 3)
        difficulty = get_task_difficulty(task_id)
        if difficulty is None:
            # На всякий случай, если по какой-то причине не удалось получить difficulty
            difficulty = 1

        # 2) Считаем количество очков
        score_delta = difficulty * 100

        # 3) Обновляем рейтинг пользователя: добавляем score_delta и инкрементируем solved_count
        update_user_score(
            user_tg_id=message.from_user.id,
            score_delta=score_delta,
            increment_solved=True
        )

        # 4) Получаем решение из БД и отправляем пользователю
        solution = await get_task_solution_from_db(task_id)

        await message.answer(
            f"✅ Ответ верный! Вы получаете {score_delta} баллов и +1 к количеству решённых задач.\n"
            f"Можете выбрать другую задачу или другой игровой режим."
        )
        await message.answer(f"Показываем решение задачи:\n{solution}")
        await state.clear()

    else:
        # Если ответ неверный и есть ещё подсказки
        if not hints_exhausted and await are_there_any_hints(task_id, hint_count):
            await message.answer(
                "❌ Ответ неверный! Попробуйте ещё раз или возьмите подсказку.",
                reply_markup=keyboards.choosing_hint_or_not
            )
        else:
            # Подсказки закончились
            await state.update_data(hints_exhausted=True)
            await message.answer(
                "❌ Ответ неверный!\n"
                "🔒 Количество подсказок иссякло. Сдаться?",
                reply_markup=keyboards.exit_game_after_hints_turn_zero
            )

# statistics 
async def get_stats_info(user_id: int) -> str:
    user_stats = get_user_stats(user_id)

    if user_stats:
        user_rating, solved_count = user_stats

        # Получаем место в топе по рейтингу
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) + 1
                FROM User
                WHERE rating > (
                    SELECT rating FROM User WHERE user_tg_id = ?
                )
            """, (user_id,))
            place_row = cur.fetchone()
            place = place_row[0] if place_row else 0

        statistics = f"{place}+{solved_count}"
        return statistics
    else:
        return '0'  # пользователь не найден в таблице
          
@router.message(F.text == 'Посмотреть статистику')
async def check_statistics(message: Message):
    user_id = message.from_user.id
    # ZAGLUSHKA for checking statistics
    statistics = await get_stats_info(user_id)
    
    if statistics != '0':
        stats_data = statistics.split('+')
        place = int(stats_data[0])
        count_tasks = stats_data[1]
        name = await get_user_name_from_db(user_id)
        
        emoji = ''
        if place == 1:
            emoji = '🥇'
        elif place == 2:
            emoji = '🥈'
        elif place == 3:
            emoji = '🥉'
        else:
            emoji = '🔹️'
        await message.answer(f'{name}, вот Ваша игровая статистика:\n'
                            f'{emoji}  Место в топе игроков: {place}\n'
                            f'✅️  Решено задач: {count_tasks}')
        