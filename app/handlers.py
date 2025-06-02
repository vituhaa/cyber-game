from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

import app.keyboards as keyboards

router = Router()


@router.message(CommandStart()) # decorator for \start message
async def command_start(message: Message):
    await message.answer('Привет! Это кибер-игра для студентов НИУ ВШЭ.\
\nЗдесь ты сможешь решать интересные задачи, разгадывать шифры\
 и соревноваться с другими пользователями')
    await message.answer('Прежде чем играть, нужно зарегистрироваться!\nКак тебя зовут?')