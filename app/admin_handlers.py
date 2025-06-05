from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.keyboards as keyboards

from DataBase.Tables.HintTable import *
from DataBase.Tables.RoomParticipants import *
from DataBase.Tables.RoomTable import *
from DataBase.Tables.RoomTasksTable import *
from DataBase.Tables.TaskTable import *
from DataBase.Tables.TaskTypeTable import *
from DataBase.Tables.TaskAttemptsTable import *
from DataBase.Tables.UserTable import *

admin_router = Router()

class New_Task(StatesGroup): # create new task
    title = State()
    category = State()
    complexity = State()
    description = State()
    question = State()
    answer = State()
    solution = State()
    hint_1 = State()
    hint_2 = State()
    hint_3 = State()


# ZAGLUSHKA for saving task in db
async def save_task_in_db(
    title: str,
    category: str,
    complexity: str,
    description: str,
    question: str,
    answer: str,
    solution: str,
    hint_1: str,
    hint_1_penalty: int,
    hint_2: str,
    hint_2_penalty: int,
    hint_3: str,
    hint_3_penalty: int
) -> bool:
    try:
        # Преобразуем category в int (если это ID)
        type_id = int(category)

        # Сохраняем само задание
        task_id = create_task(
            title, type_id, complexity,
            description, question, answer, solution
        )

        # Сохраняем подсказки
        if hint_1:
            create_hint(task_id, hint_1, 1, hint_1_penalty)
        if hint_2:
            create_hint(task_id, hint_2, 2, hint_2_penalty)
        if hint_3:
            create_hint(task_id, hint_3, 3, hint_3_penalty)

        return True
    except Exception as e:
        print(f"[Ошибка при сохранении задания]: {e}")
        return False


@admin_router.message(Command('admin')) # /admin
async def start_admin_settings(message: Message):
    user_id = message.from_user.id
    role = get_user_role(user_id)  # твоя функция получения роли
    if role != 'admin':
        await message.answer("⛔️ У вас нет прав администратора")
        return  # не запускаем FSM

    await message.answer('Добро пожаловать, администратор!\n'
                         'Выберите действие:', reply_markup=keyboards.admin_actions)
    
@admin_router.callback_query(F.data == 'create_new_task')
async def enter_title(callback: CallbackQuery, state: FSMContext):
    await state.set_state(New_Task.title)
    await callback.message.answer('Напишите заголовок к задаче')
    
@admin_router.message(New_Task.title)
async def enter_category(message: Message, state: FSMContext):
    await state.update_data(title=message.text) # save title in New_Task field title
    await state.set_state(New_Task.category)
    await message.answer('Укажите категорию задачи', reply_markup=keyboards.task_category_for_admin) # admin keyboard with types
    
@admin_router.callback_query(New_Task.category, F.data == 'cypher_task')
async def enter_complexity_1(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category_id=2, category_name="Шифр")
    await state.set_state(New_Task.complexity)
    await callback.message.answer('Выберите сложность', reply_markup=keyboards.task_complexity_for_admin)

@admin_router.callback_query(New_Task.category, F.data == 'symbol_task')
async def enter_complexity_2(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category_id=1, category_name="Символьные")
    await state.set_state(New_Task.complexity)
    await callback.message.answer('Выберите сложность', reply_markup=keyboards.task_complexity_for_admin)
    
@admin_router.callback_query(New_Task.complexity, F.data == 'easy_task')
async def enter_description_1(callback: CallbackQuery, state: FSMContext):
    await state.update_data(complexity_id=1, complexity_name="Простая")
    await state.set_state(New_Task.description)
    await callback.message.answer('Напишите условие задачи')

@admin_router.callback_query(New_Task.complexity, F.data == 'normal_task')
async def enter_description_2(callback: CallbackQuery, state: FSMContext):
    await state.update_data(complexity_id=2, complexity_name="Средняя")
    await state.set_state(New_Task.description)
    await callback.message.answer('Напишите условие задачи')

@admin_router.callback_query(New_Task.complexity, F.data == 'hard_task')
async def enter_description_3(callback: CallbackQuery, state: FSMContext):
    await state.update_data(complexity_id=3, complexity_name="Сложная")
    await state.set_state(New_Task.description)
    await callback.message.answer('Напишите условие задачи')
    
@admin_router.message(New_Task.description)
async def enter_question(message: Message, state: FSMContext):
    await state.update_data(description=message.text) # save description in New_Task field description
    await state.set_state(New_Task.question)
    await message.answer('Укажите вопрос задачи')
    
@admin_router.message(New_Task.question)
async def enter_answer(message: Message, state: FSMContext):
    await state.update_data(question=message.text) # save question in New_Task field question
    await state.set_state(New_Task.answer)
    await message.answer('Какой правильный ответ?')
    
@admin_router.message(New_Task.answer)
async def enter_solution(message: Message, state: FSMContext):
    await state.update_data(answer=message.text) # save answer in New_Task field answer
    await state.set_state(New_Task.solution)
    await message.answer('Приведите решение задачи')
    
@admin_router.message(New_Task.solution)
async def enter_hint_1(message: Message, state: FSMContext):
    await state.update_data(solution=message.text) # save solution in New_Task field solution
    await state.set_state(New_Task.hint_1)
    await message.answer('Введите 1 подсказку')
    
@admin_router.message(New_Task.hint_1)
async def enter_hint_2(message: Message, state: FSMContext):
    await state.update_data(hint_1=message.text) # save hint_1 in New_Task field hint_1
    await state.set_state(New_Task.hint_2)
    await message.answer('Введите 2 подсказку')
    
@admin_router.message(New_Task.hint_2)
async def enter_hint_3(message: Message, state: FSMContext):
    await state.update_data(hint_2=message.text) # save hint_2 in New_Task field hint_2
    await state.set_state(New_Task.hint_3)
    await message.answer('Введите 3 подсказку')
    
@admin_router.message(New_Task.hint_3)
async def create_new_task(message: Message, state: FSMContext):
    await state.update_data(hint_3=message.text) # save hint_3 in New_Task field hint_3

    user_id = message.from_user.id
    role = get_user_role(user_id)

    if role != 'admin':
        await message.answer("⛔️ У вас нет прав администратора")
        await state.clear()
        return

    task_data = await state.get_data() # New_Task class info
    title = task_data.get("title")
    category_id = task_data.get("category_id")
    category_name = task_data.get("category_name")
    complexity_id = task_data.get("complexity_id")
    complexity_name = task_data.get("complexity_name")
    category = task_data.get("category")
    complexity = task_data.get("complexity")
    description = task_data.get("description")
    question = task_data.get("question")
    answer = task_data.get("answer")
    solution = task_data.get("solution")
    hint_1 = task_data.get("hint_1")
    hint_2 = task_data.get("hint_2")
    hint_3 = task_data.get("hint_3")
    hint_1_penalty = 10
    hint_2_penalty = 20
    hint_3_penalty = 30
    
    # ZAGLUSHKA for saving task in db
    success_creating_task = await save_task_in_db(
        title, category_id, complexity_id,
        description, question, answer, solution,
        hint_1, hint_1_penalty,
        hint_2, hint_2_penalty,
        hint_3, hint_3_penalty
    )

    if success_creating_task:
        await message.answer(
            f'✅ Задание успешно создано!\n\n'
            f'📌 Название: {title}\n'
            f'✔️ Категория: {category_name}\n'
            f'⚠️ Сложность: {complexity_name}\n'
            f'📝 Описание: {description}\n'
            f'❓️ Вопрос: {question}\n'
            f'✅ Ответ: {answer}\n'
            f'📚 Решение: {solution}\n'
            f'💡 Подсказка 1: {hint_1} (штраф: {hint_1_penalty})\n'
            f'💡 Подсказка 2: {hint_2} (штраф: {hint_2_penalty})\n'
            f'💡 Подсказка 3: {hint_3} (штраф: {hint_3_penalty})'
        )
    else:
        await message.answer("❌ Произошла ошибка при сохранении задания")

    await state.clear()