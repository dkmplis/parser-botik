import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from aiogram import Bot

import src.tg.notifier as notifier
from src.announcement import Announcement


@pytest.mark.asyncio
async def test_enqueue_notifications():
    notifier._notify_queue = asyncio.Queue()

    mock_ad = Announcement(id="1", name="Тест", link="http",
                           timestamp=123, price="100", image=None)
    mock_sub = MagicMock()
    mock_sub.user_id = 999888

    requests_data = {
        "query1": {
            "ads": [mock_ad],
            "subs": [mock_sub]
        }
    }

    await notifier.enqueue_notifications(requests_data)

    assert not notifier._notify_queue.empty()
    task = await notifier._notify_queue.get()

    assert task == (999888, mock_ad)


@pytest.mark.asyncio
async def test_send_announcement_no_image():
    mock_bot = AsyncMock(spec=Bot)
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    ad = Announcement(id="1", name="Квартира", link="http",
                      timestamp=123, price="100", image=None)

    await notifier._send_announcement(mock_bot, mock_client, 111, ad)

    mock_bot.send_message.assert_called_once()
    mock_bot.send_photo.assert_not_called()


@pytest.mark.asyncio
@patch("src.tg.notifier.get_image_bytes")
async def test_send_announcement_with_new_image(mock_get_image_bytes):
    mock_bot = AsyncMock(spec=Bot)
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    notifier._image_cache.clear()

    ad = Announcement(id="2", name="Дом", link="http",
                      timestamp=123, price="200", image="img.jpg")

    mock_get_image_bytes.return_value = b"fake_image_bytes"

    mock_tg_response = MagicMock()
    mock_tg_photo = MagicMock()
    mock_tg_photo.file_id = "TELEGRAM_FILE_ID_777"
    mock_tg_response.photo = [mock_tg_photo]
    mock_bot.send_photo.return_value = mock_tg_response

    await notifier._send_announcement(mock_bot, mock_client, 222, ad)

    mock_get_image_bytes.assert_called_once()
    mock_bot.send_photo.assert_called_once()
    assert "2" in notifier._image_cache
    assert notifier._image_cache["2"] == "TELEGRAM_FILE_ID_777"


@pytest.mark.asyncio
@patch("src.tg.notifier.get_image_bytes")
async def test_send_announcement_with_cached_image(mock_get_image_bytes):
    mock_bot = AsyncMock(spec=Bot)
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    ad = Announcement(id="3", name="Гараж", link="http",
                      timestamp=123, price="300", image="img2.jpg")

    notifier._image_cache["3"] = "ALREADY_CACHED_FILE_ID"

    await notifier._send_announcement(mock_bot, mock_client, 333, ad)

    mock_get_image_bytes.assert_not_called()

    mock_bot.send_photo.assert_called_once()

    kwargs = mock_bot.send_photo.call_args.kwargs
    assert kwargs["photo"] == "ALREADY_CACHED_FILE_ID"
