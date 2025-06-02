from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Случайная задача'), KeyboardButton(text='Задача из категории')],
                                          [KeyboardButton(text='Посмотреть статистику'), KeyboardButton(text='Соревнование')]])