import logging
from datetime import datetime, timezone

import httpx
from pydantic import ValidationError

from src.announcement import Announcement
from src.config import HEADERS, KUFAR_URL
from src.schemas.kufar import KufarAd

logger = logging.getLogger(__name__)
DELAY = 120


async def get_valid_realty_data(
    client: httpx.AsyncClient, params: dict
) -> list[Announcement]:
    response_data = await _fetch_realty_data(client, params)
    ads = response_data.get("ads", [])

    new_announcements: list[Announcement] = []
    current_limit = int(datetime.now(timezone.utc).timestamp() - DELAY)

    for order_data in ads:
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
                f"Не удлалось распарсить объявление (ad_id: {ad_id}): {e.errors()[0]['msg']}"
            )
            continue
    return new_announcements


async def _fetch_realty_data(client: httpx.AsyncClient, params: dict):
    try:
        response = await client.get(url=KUFAR_URL, headers=HEADERS, params=params)
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
        logger.error(f"Ошибка запроса к API Kufar: {e}")
        return {}
