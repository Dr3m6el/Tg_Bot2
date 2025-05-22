import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from support import router as support_router, setup_support
from handler import router as main_router  # Твой основной обработчик с /start, faq, чат ИИ и т.д.

ADMIN_ID = 1326404077  # Задай ID администратора здесь

TOKEN = os.getenv("BOT_TOKEN")
if TOKEN is None:
    raise ValueError("BOT_TOKEN environment variable is not set")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Устанавливаем ID админа для поддержки
setup_support(ADMIN_ID)

dp.include_router(main_router)
dp.include_router(support_router)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
