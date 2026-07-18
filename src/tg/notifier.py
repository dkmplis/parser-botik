import logging
from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)


async def send_announcement(bot: Bot,
                            user_id: int,
                            announcement: dict,
                            image_bytes: bytes):
    message_text = (
        f"**{announcement['name']}**\n"
        f"Цена: {announcement['price']} BYN\n"
        f"[Открыть на Kufar]({announcement['link']})"
    )
    try:
        if image_bytes:
            photo = BufferedInputFile(image_bytes, filename='image.jpg')
            await bot.send_photo(chat_id=user_id,
                                 photo=photo,
                                 caption=message_text,
                                 parse_mode='Markdown')
        else:
            await bot.send_message(chat_id=user_id, text=message_text)
    except TelegramAPIError as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
