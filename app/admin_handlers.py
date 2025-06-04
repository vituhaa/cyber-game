from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.keyboards as keyboards

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
async def save_task_in_db(title: str, category: str, complexity: str, description: str, question: str, answer: str, solution: str, hint_1: str, hint_2: str, hint_3: str) -> bool:
    # function for creating task in db
    # function for hints in db
    return True

@admin_router.message(Command('admin')) # /admin
async def start_admin_settings(message: Message):
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
    await state.update_data(category="Шифр") # save category in New_Task field category
    await state.set_state(New_Task.complexity)
    await callback.message.answer('Выберите сложность', reply_markup=keyboards.task_complexity_for_admin) # admin keyboard with difficulty
    
@admin_router.callback_query(New_Task.category, F.data == 'symbol_task')
async def enter_complexity_2(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category="Символьные") # save category in New_Task field category
    await state.set_state(New_Task.complexity)
    await callback.message.answer('Выберите сложность', reply_markup=keyboards.task_complexity_for_admin) # admin keyboard with difficulty
    
@admin_router.callback_query(New_Task.complexity, F.data == 'easy_task')
async def enter_description_1(callback: CallbackQuery, state: FSMContext):
    await state.update_data(complexity="Простая") # save complexity in New_Task field complexity
    await state.set_state(New_Task.description)
    await callback.message.answer('Напишите условие задачи')
    
@admin_router.callback_query(New_Task.complexity, F.data == 'normal_task')
async def enter_description_2(callback: CallbackQuery, state: FSMContext):
    await state.update_data(complexity="Средняя") # save complexity in New_Task field complexity
    await state.set_state(New_Task.description)
    await callback.message.answer('Напишите условие задачи')

@admin_router.callback_query(New_Task.complexity, F.data == 'hard_task')
async def enter_description_3(callback: CallbackQuery, state: FSMContext):
    await state.update_data(complexity="Сложная") # save complexity in New_Task field complexity
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
    
    task_data = await state.get_data() # New_Task class info
    title = task_data.get("title")
    category = task_data.get("category")
    complexity = task_data.get("complexity")
    description = task_data.get("description")
    question = task_data.get("question")
    answer = task_data.get("answer")
    solution = task_data.get("solution")
    hint_1 = task_data.get("hint_1")
    hint_2 = task_data.get("hint_2")
    hint_3 = task_data.get("hint_3")
    
    # ZAGLUSHKA for saving task in db
    success_creating_task = await save_task_in_db(title, category, complexity, description, question, answer, solution, hint_1, hint_2, hint_3)
    
    if success_creating_task:
        await message.answer(f'📌  Название: {title}\n\n✔️  Категория: {category}\n\n⚠️  Сложность: {complexity}\n\n'
                            f'📝  Описание: {description}\n\n❓️  Вопрос: {question}\n\n✅  Ответ: {answer}\n\n'
                            f'📚  Решение: {solution}\n\n💡  Подсказка 1: {hint_1}\n\n💡  Подсказка 2: {hint_2}\n\n'
                            f'💡  Подсказка 3: {hint_3}')
    await state.clear() # clear states