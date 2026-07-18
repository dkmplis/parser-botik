import httpx

KUFAR_REGIONS: dict[str, dict[str, int]] = {}
URL = 'https://api.kufar.by/yandex-geocoder/static/regions'
TARGET_TYPES = {'city', 'urban_settlement', 'working_village'}


async def init_regions_cache():
    async with httpx.AsyncClient() as client:
        response = await client.get(URL)
        response.raise_for_status()
        data = response.json()
    for region_info in data:
        region_type = region_info.get('type')
        if region_type in TARGET_TYPES:
            city_name = region_info.get('labels').get('ru')
            city_key = city_name.lower()
            rgn = region_info.get('region')
            area = region_info.get('area')
            KUFAR_REGIONS[city_key] = {
                'rgn': int(rgn),
                'area': int(area) if area is not None else None
            }


async def search_kufar_region_area(query: str) -> dict[str, dict]:
    query = query.lower().strip()
    return {
        name.title(): data
        for name, data in KUFAR_REGIONS.items()
        if query in name
    }
