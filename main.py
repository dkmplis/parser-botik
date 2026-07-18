import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.config import BOT_TOKEN
from src.tg.handlers.handlers import router as tg_router
from src.scheduler import tick_kufar_parser
from src.db.models import init_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN отсуствует в переменных окружения")

    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(tg_router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(tick_kufar_parser, 'interval', minutes=2, args=[bot])
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logging.info("Бот остановлен")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Бот остановлен: {e}")