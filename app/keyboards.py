from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)

main_menu = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Случайная задача'), KeyboardButton(text='Задача из категории')],
                                          [KeyboardButton(text='Посмотреть статистику'), KeyboardButton(text='Соревнование')]],
                                resize_keyboard=True,
                                input_field_placeholder='Выбери действие')

task_from_category = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Простая', callback_data='easy')],
    [InlineKeyboardButton(text='Средняя', callback_data='normal')],
    [InlineKeyboardButton(text='Сложная', callback_data='hard')]])