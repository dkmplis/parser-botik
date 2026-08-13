import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import httpx
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import BOT_TOKEN
from src.db.models import init_db
from src.kufar.regions_cache import init_regions_cache
from src.schedulers.scheduler import tick_kufar, tick_realty_kufar
from src.tg.handlers.handlers import router as tg_router
from src.tg.handlers.kufar_handlers import router as kufar_router
from src.tg.handlers.realty_kufar_handlers import router as realty_kufar_router
from src.tg.notifier import start_notify_worker, stop_notify_worker

logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN отсуствует в переменных окружения")
    setup_logging()
    await init_db()
    await init_regions_cache()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(tg_router)
    dp.include_router(kufar_router)
    dp.include_router(realty_kufar_router)

    client = httpx.AsyncClient(timeout=10, http2=True)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(tick_kufar, "interval", minutes=2, args=[client])
    scheduler.add_job(tick_realty_kufar, "interval", minutes=2, args=[client])
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот запущен.")
    notify_worker_task = asyncio.create_task(start_notify_worker(bot, client))
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await client.aclose()
        await stop_notify_worker()
        await notify_worker_task
        logger.info("Бот остановлен")


def setup_logging():
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)

    log_format = "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
    formatter = logging.Formatter(log_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=f"{log_dir}/bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:  # noqa: BLE001
        logger.error(f"Бот остановлен: {e}")
