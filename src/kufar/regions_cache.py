import logging

import httpx

from src.schemas.kufar import KufarRegionItem

logger = logging.getLogger(__name__)

KUFAR_REGIONS: dict[str, dict] = {}
URL = "https://api.kufar.by/yandex-geocoder/static/regions"
TARGET_TYPES = {"city", "urban_settlement", "working_village"}
TOP_CITIES = ["Минск", "Гомель", "Гродно", "Брест", "Витебск", "Могилев"]


async def init_regions_cache():
    logger.info("Инициализация кеша городов для Куфара")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(URL)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as ex:
            logger.error(
                f"Ошибка выполнения запроса для формирования кеша городов Куфар: {ex}"
            )
            return
    cities_map = {}
    new_regions_data = {}
    parsed_items = [KufarRegionItem.model_validate(item) for item in data]
    for item in parsed_items:
        if item.type in TARGET_TYPES and item.ru_name:
            city_key = item.ru_name.lower().replace("ё", "е")
            cities_map[str(item.id)] = city_key
            new_regions_data[city_key] = {
                "rgn": item.region,
                "ar": item.area,
                "gtsy": item.tag,
                "districts": {},
            }

    for item in parsed_items:
        if item.type in "district" and item.ru_name and item.tag:
            parent_city_name = cities_map.get(str(item.pid))
            if parent_city_name and parent_city_name in new_regions_data:
                new_regions_data[parent_city_name]["districts"][item.ru_name] = item.tag

    KUFAR_REGIONS.clear()
    KUFAR_REGIONS.update(new_regions_data)
    logger.info(
        f"Инициализация кеша городов Куфар завершена успешно. Количество городов: {len(KUFAR_REGIONS)}"
    )


async def search_city(city_name: str) -> dict | None:
    city_key = city_name.lower().strip().replace("ё", "е")
    return KUFAR_REGIONS.get(city_key)
