from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)

main_menu = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Случайная задача'), KeyboardButton(text='Задача из категории')],
                                          [KeyboardButton(text='Посмотреть статистику'), KeyboardButton(text='Соревнование')]],
                                resize_keyboard=True,
                                input_field_placeholder='Выбери действие')

task_from_category = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Простая', callback_data='easy')],
    [InlineKeyboardButton(text='Средняя', callback_data='normal')],
    [InlineKeyboardButton(text='Сложная', callback_data='hard')]
])

choosing_type_of_task = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Шифр', callback_data='cypher')],
    [InlineKeyboardButton(text='Символьные', callback_data='symbol')]
])

choosing_hint_or_not = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Взять подсказку', callback_data='yes')],
])

exit_game_after_hints_turn_zero = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Сдаться', callback_data='give_up')],
])

start_competition = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Начать соревнование'), KeyboardButton(text='Выйти из соревнования')]],
                                        resize_keyboard=True,
                                        input_field_placeholder='Выбери действие')


# admin keyboards

admin_actions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Создать задачу', callback_data='create_new_task')]
])

task_complexity_for_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Простая', callback_data='easy_task')],
    [InlineKeyboardButton(text='Средняя', callback_data='normal_task')],
    [InlineKeyboardButton(text='Сложная', callback_data='hard_task')]
])

task_category_for_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Шифр', callback_data='cypher_task')],
    [InlineKeyboardButton(text='Символьные', callback_data='symbol_task')]
])

# competition keyboards
actions_with_room = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Присоединиться к комнате', callback_data='join_room')],
    [InlineKeyboardButton(text='Создать свою комнату', callback_data='create_room')]
])

# function which create keyboard for 2 actionts: join the room and create the room
def get_room_type_keyboard(context: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Открытая', 
                callback_data=f'{context}_opened_room'
            ),
            InlineKeyboardButton(
                text='Закрытая', 
                callback_data=f'{context}_closed_room'
            )
        ]
    ])