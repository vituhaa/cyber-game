import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiogram.types import Update
import os
from app.handlers import router
from app.admin_handlers import admin_router
from app.competition_handlers import comp_router

load_dotenv()  # load data from .env

bot = Bot(token=os.getenv("BOT_TOKEN")) # bot object with token from .env
dispatcher = Dispatcher() # dispatcher object for handlers
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# async def main():
#     dispatcher.include_router(router)
#     dispatcher.include_router(admin_router)
#     dispatcher.include_router(comp_router)
#     await dispatcher.start_polling(bot) # checking updates




dispatcher.include_router(router)
dispatcher.include_router(admin_router)
dispatcher.include_router(comp_router)

async def handle_webhook(request: web.Request):
    data = await request.text()
    update = Update.model_validate_json(data)
    await dispatcher.feed_update(bot, update)
    return web.Response(text='OK')

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()

def create_app():
    app = web.Application()

    # Установка aiogram-хендлера
    SimpleRequestHandler(dispatcher=dispatcher, bot=bot).register(app, path=WEBHOOK_PATH)

    # Старт и стоп хуков
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Настройка aiogram приложения
    setup_application(app, dispatcher, bot=bot)
    return app
    
if __name__ == '__main__': # running file main
    # try:
    #     asyncio.run(main())
    # except KeyboardInterrupt:
    #     print('Бот выключен')
    web.run_app(create_app(), port=int(os.getenv("PORT", 8080)))
 