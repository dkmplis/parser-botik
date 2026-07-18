import httpx
import logging
from datetime import datetime
from src.config import HEADERS, PARAMS, KUFAR_URL, KUFAR_IMAGE_URL, HEADERS_FOR_IMAGE
from src.decorator_timer import async_timed
from src.announcement import Announcement

logger = logging.getLogger(__name__)


@async_timed
async def get_valid_data(client: httpx.AsyncClient,
                         query: str) -> list[Announcement]:
    response = await _fetch_data(client, query)
    response_data = response.get('ads', [])
    new_announcements: list[Announcement] = []
    current_limit = int(datetime.now().timestamp()) - 120

    for order_data in response_data:
        try:
            timestamp = int(datetime.fromisoformat(
                order_data['list_time']).timestamp()
            )
            if timestamp < current_limit:
                continue
            ad_id = order_data['ad_id']
            name = order_data['subject']
            link = order_data['ad_link']
            image_path = order_data['images'][0]['path'] if order_data['images'] else None
            price = round(int(order_data['price_byn'])/100, 2)

            new_announcements.append(
                Announcement(
                    id=ad_id,
                    name=name,
                    link=link,
                    timestamp=timestamp,
                    price=price,
                    image=image_path
                )
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Не удалось распарсить объявление: {e}")
            continue

    return new_announcements


async def _fetch_data(client: httpx.AsyncClient, query: str) -> dict:
    params_copy = PARAMS.copy()
    params_copy['query'] = query
    try:
        response = await client.get(url=KUFAR_URL,
                                    params=params_copy,
                                    headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Ошибка запроса Kufar по запросу {query}: {e}")
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
        logger.error(f"Ошибка скачивания изображения {url}: {e}")
        return b""
