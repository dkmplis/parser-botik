import asyncio
import logging
from collections import OrderedDict

import httpx
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.types import BufferedInputFile

from src.announcement import Announcement
from src.services.kufar_service import get_image_bytes

logger = logging.getLogger(__name__)
_notify_queue: asyncio.Queue | None = None
TG_SEND_DELAY = 0.05
MAX_CACHE_SIZE = 500
_image_cache = OrderedDict()


async def start_notify_worker(bot: Bot, client: httpx.AsyncClient):
    global _notify_queue
    _notify_queue = asyncio.Queue()
    logger.info("Воркер рассылки запущен")

    while True:
        try:
            task = await _notify_queue.get()
            if task is None:
                break
            user_id, annoucement = task
            await _send_announcement(
                bot,
                client,
                user_id,
                annoucement,
            )
            _notify_queue.task_done()
            await asyncio.sleep(TG_SEND_DELAY)
        except asyncio.CancelledError:
            break
        except Exception as e:  # noqa: BLE001
            logger.error(f"Непредвиденная ошибка в воркере рассылки: {e}")


async def stop_notify_worker():
    if _notify_queue:
        await _notify_queue.put(None)


async def enqueue_notifications(requests: dict):
    if _notify_queue is None:
        logger.warning("Очередь рассылки не инициализирована")
        return

    for request_data in requests.values():
        ads = request_data["ads"]
        if not ads:
            continue
        subs = request_data["subs"]

        for ad in ads:
            for sub in subs:
                await _notify_queue.put((sub.user_id, ad))


async def _send_announcement(
    bot: Bot,
    client: httpx.AsyncClient,
    user_id: int,
    announcement: Announcement,
):
    message_text = (
        f"**{announcement.name}**\n"
        f"Цена: {announcement.price} BYN\n"
        f"[Открыть на Kufar]({announcement.link})"
    )
    try:
        if announcement.image:
            if announcement.id in _image_cache:
                file_id = _image_cache[announcement.id]
                await bot.send_photo(
                    chat_id=user_id,
                    photo=file_id,
                    caption=message_text,
                    parse_mode="Markdown",
                )
            else:
                images_bytes = await get_image_bytes(client, announcement.image)
                if images_bytes:
                    photo = BufferedInputFile(images_bytes, filename="image.jpg")
                    response_tg = await bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption=message_text,
                        parse_mode="Markdown",
                    )
                    new_file_id = response_tg.photo[-1].file_id
                    _image_cache[announcement.id] = new_file_id
                    if len(_image_cache) > MAX_CACHE_SIZE:
                        _image_cache.popitem(last=False)
                else:
                    await bot.send_message(
                        chat_id=user_id, text=message_text, parse_mode="Markdown"
                    )
        else:
            await bot.send_message(chat_id=user_id, text=message_text)
        logger.info(
            f"Уведомление '{announcement.name}' успешно отправлено юзеру {user_id}"
        )
    except TelegramRetryAfter as e:
        logger.warning(f"Telegram Limit! {e.retry_after} секунд")
        await asyncio.sleep(e.retry_after)
        return await _send_announcement(
            bot,
            client,
            user_id,
            announcement,
        )
    except TelegramAPIError as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
