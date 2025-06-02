import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os
from aiogram.types import Message

load_dotenv()  # load data from .env

bot = Bot(token=os.getenv("BOT_TOKEN")) # bot object with token from .env
dispatcher = Dispatcher() # dispatcher object for handlers

@dispatcher.message() # decorator for all messages
async def command_start(message: Message):
    await message.answer('Привет! Это кибер-игра для студентов НИУ ВШЭ.\
                         Здесь ты сможешь решать интересные задачи, разгадывать шифры\
                             и соревноваться с другими пользователями')
    await message.reply('Правила очень просты')

async def main():
    await dispatcher.start_polling(bot) # checking updates
    
if __name__ == '__main__': # running file main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
 