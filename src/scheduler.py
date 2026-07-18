import asyncio
import logging
import time
import httpx

from aiogram import Bot
from src.kufar_service import get_valid_data, get_image_bytes
from src.tg.config_manager import load_config
from src.tg.notifier import send_announcement
from src.announcement import Announcement

logger = logging.getLogger(__name__)

CURRENCY_KUFAR = 7
CURRENCY_IMAGE = 10
TG_SEND_DELAY = 0.5


async def tick_kufar_parser(bot: Bot) -> None:
    start_time = time.perf_counter()

    config = load_config()
    if not config:
        return

    all_queries = {query for user_quries in config.values()
                   for query in user_quries}

    async with httpx.AsyncClient(timeout=10, http2=True) as client:
        all_new_announcements = await _async_req_to_kufar_receive_new_ads(
            queries=all_queries, client=client)
        queries_completed_time = time.perf_counter()

        logger.info(
            f"Время затраченное на запросы к куфар и их фильтрацию: {(queries_completed_time - start_time) * 1000} мс")

        for query, announcements in all_new_announcements.items():
            logger.info(
                f"Запрос '{query}': новых объявлений {len(announcements)}")

        image_paths = {
            announcement.id: announcement.image
            for announcements in all_new_announcements.values()
            for announcement in announcements
            if announcement.image
        }

        images = await _async_req_to_kufar_to_obtain_images(client, image_paths)
        images_completed_time = time.perf_counter()
        logger.info(
            f"Время затраченное на получения изображений: {(images_completed_time - queries_completed_time) * 1000} мс")
        for user_id, queries in config.items():
            for query in queries:
                for announcement in all_new_announcements.get(query, []):
                    image_bytes = images.get(announcement.id)
                    await send_announcement(
                        bot=bot,
                        user_id=int(user_id),
                        announcement=announcement.to_dict(),
                        image_bytes=image_bytes)
                    await asyncio.sleep(TG_SEND_DELAY)

    send_messages_tg_time = time.perf_counter()
    logger.info(
        f"Время отправки результов в телеграмм: {(send_messages_tg_time - images_completed_time) * 1000} мс")


async def _async_req_to_kufar_receive_new_ads(
    client: httpx.AsyncClient,
    queries: set
) -> dict[str, list[Announcement]]:
    semaphore = asyncio.Semaphore(CURRENCY_KUFAR)

    async def fetch_query(query: str):
        async with semaphore:
            return query, await get_valid_data(client, query)

    pairs = await asyncio.gather(*(fetch_query(query) for query in queries))
    return dict(pairs)


async def _async_req_to_kufar_to_obtain_images(
    client,
    image_paths: dict[str, str]
):
    semaphore = asyncio.Semaphore(CURRENCY_IMAGE)

    async def fetch_query(
        client: httpx.AsyncClient,
        announcement_id: str,
        image_path: str
    ) -> dict[str, bytes]:
        async with semaphore:
            return announcement_id, await get_image_bytes(client, image_path)

    pairs = await asyncio.gather(
        *(fetch_query(client, announcement_id, image_path)
          for announcement_id, image_path in image_paths.items())
    )
    return dict(pairs)
