import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher
from fastapi import FastAPI

from src.core.config import settings
from src.core.database import db
from src.bot.handlers import registration, admin as bot_admin
from src.api.routes import admin_web

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Ініціалізація бота та диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Реєстрація роутерів бота (обробники команд та повідомлень)
dp.include_router(registration.router)
dp.include_router(bot_admin.admin_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Керування життєвим циклом додатку:
    виконується при старті та зупинці сервера.
    """
    # 1. Підключення до бази даних
    logger.info("Підключення до бази даних MongoDB...")
    await db.connect()
    
    # 2. Налаштування та запуск бота
    logger.info("Підготовка Telegram-бота...")
    
    
    
    logger.info(f"Запуск бота @{(await bot.get_me()).username}...")
    
   
    polling_task = asyncio.create_task(
        dp.start_polling(bot, limit=20, allowed_updates=dp.resolve_used_update_types())
    )
    
    yield  # Тут FastAPI починає приймати запити в адмінку
    
    # 3. Зупинка всього
    logger.info("Зупинка сервера та бота...")
    polling_task.cancel()  # Зупиняємо задачу поллінгу
    await bot.session.close()
    logger.info("Сесія бота закрита. Додаток зупинено.")

# Створення додатку FastAPI
app = FastAPI(
    title="Job Fair Admin Panel",
    lifespan=lifespan
)

# Кладемо об'єкт бота в пам'ять сервера (app.state), 
# щоб діставати його в маршрутах через request.app.state.bot
app.state.bot = bot 

# Реєстрація веб-роутерів для адмінки
app.include_router(admin_web.router)

if __name__ == "__main__":
    # Запуск сервера
    # host 0.0.0.0 дозволяє підключатися по локальній мережі або через Docker
    uvicorn.run(app, host="0.0.0.0", port=8000)