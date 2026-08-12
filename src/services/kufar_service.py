import logging
from datetime import datetime, timezone

import httpx
from pydantic import ValidationError

from src.announcement import Announcement
from src.config import HEADERS, HEADERS_FOR_IMAGE, KUFAR_IMAGE_URL, KUFAR_URL
from src.schemas.kufar import KufarAd

logger = logging.getLogger(__name__)
DELAY = 120


async def get_valid_data(client: httpx.AsyncClient, params: dict) -> list[Announcement]:
    response = await _fetch_data(client, params)
    response_data = response.get("ads", [])
    new_announcements: list[Announcement] = []
    current_limit = int(datetime.now(timezone.utc).timestamp()) - DELAY

    for order_data in response_data:
        try:
            ad = KufarAd.model_validate(order_data)
            if ad.timestamp < current_limit:
                continue
            new_announcements.append(
                Announcement(
                    id=str(ad.ad_id),
                    name=ad.subject,
                    link=ad.ad_link,
                    timestamp=ad.timestamp,
                    price=ad.parsed_price,
                    image=ad.image_path,
                )
            )
        except ValidationError as e:
            ad_id = order_data.get("ad_id", "Unknown")
            logger.warning(
                f"Ошибка структуры Kufar API (ad_id: {ad_id}): {e.errors()[0]['msg']}"
            )
            continue

    return new_announcements


async def _fetch_data(client: httpx.AsyncClient, params: dict) -> dict:
    try:
        response = await client.get(url=KUFAR_URL, params=params, headers=HEADERS)
        if response.status_code != 200:
            logger.error(
                f"Ошибка API Kufar по запросу '{params.get('query')}\n"
                f"Статус: {response.status_code}\n"
                f"URL: {response.url}\n"
                f"Ответ сервера: {response.text}"
            )
            return {}
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Ошибка запроса Kufar по запросу {params['query']}: {e}")
        return {}


async def get_image_bytes(client: httpx.AsyncClient, image_path: str) -> bytes:
    if not image_path:
        return b""
    return await _fetch_image(client, image_path)


async def _fetch_image(client: httpx.AsyncClient, image_path: str) -> bytes:
    url = f"{KUFAR_IMAGE_URL}{image_path}"
    try:
        response = await client.get(url=url, headers=HEADERS_FOR_IMAGE)
        response.raise_for_status()
        return response.content
    except httpx.HTTPError as e:
        logger.error(f"Ошибка загрузки изображения {url}: {e}")
        return b""
