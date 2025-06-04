import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os
from app.handlers import router
from app.admin_handlers import admin_router

load_dotenv()  # load data from .env

bot = Bot(token=os.getenv("BOT_TOKEN")) # bot object with token from .env
dispatcher = Dispatcher() # dispatcher object for handlers

async def main():
    dispatcher.include_router(router)
    dispatcher.include_router(admin_router)
    await dispatcher.start_polling(bot) # checking updates
    
if __name__ == '__main__': # running file main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
 