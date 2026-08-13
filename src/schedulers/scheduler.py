import asyncio
import logging
from collections.abc import Awaitable, Callable

import httpx

from src.db.kufar_requests import get_all_kufar_subs
from src.db.models import Base, KufarRealtySubscription, KufarSubscription
from src.db.realty_kufar_requests import get_all_realty_kufar_subs
from src.services.kufar_service import get_valid_data
from src.services.realty_kufar_service import get_valid_realty_data
from src.tg.notifier import enqueue_notifications

logger = logging.getLogger(__name__)

CURRENCY_KUFAR = 7
CURRENCY_IMAGE = 10
TG_SEND_DELAY = 0.5


async def tick_realty_kufar(client: httpx.AsyncClient) -> None:
    all_subs = await get_all_realty_kufar_subs()
    if not all_subs:
        return
    unique_requests = _get_unique_requests(all_subs, _build_params_for_realty)
    await _process_kufar_batch(client, unique_requests, get_valid_realty_data)


async def tick_kufar(client: httpx.AsyncClient) -> None:
    all_subs = await get_all_kufar_subs()
    if not all_subs:
        return
    unique_req = _get_unique_requests(all_subs, _build_params_for_kufar)
    await _process_kufar_batch(client, unique_req, get_valid_data)


def _get_unique_requests(
    all_subs: list, func_for_params: Callable[[Base], dict]
) -> dict:
    unique_req = {}
    for sub in all_subs:
        params = func_for_params(sub)
        query_key = frozenset(params.items())
        if query_key not in unique_req:
            unique_req[query_key] = {"subs": [], "ads": []}
        unique_req[query_key]["subs"].append(sub)
    return unique_req


async def _process_kufar_batch(
    client: httpx.AsyncClient,
    unique_req: dict,
    fetch_func: Callable[[httpx.AsyncClient, dict], Awaitable[list]],
):
    semaphore = asyncio.Semaphore(CURRENCY_KUFAR)

    async def fetch_req(query_key):
        async with semaphore:
            params_dict = dict(query_key)
            ads = await fetch_func(client, params_dict)
            unique_req[query_key]["ads"] = ads

    await asyncio.gather(*(fetch_req(k) for k in unique_req))
    await enqueue_notifications(unique_req)


def _build_params_for_realty(sub: KufarRealtySubscription) -> dict:
    deal_str = str(sub.deal_type).lower()
    type_param = "let" if "rental" in deal_str else "sell"
    params = {
        "cat": "1010",
        "cur": "BYN",
        "lang": "ru",
        "size": "10",
        "typ": type_param,
        "gtsy": sub.gtsy,
    }
    if sub.rooms:
        params["rms"] = f"v.or:{sub.rooms}"

    if sub.price_min is not None or sub.price_max is not None:
        price_min = sub.price_min if sub.price_min is not None else 0
        price_max = sub.price_max if sub.price_max is not None else 100000000000
        params["prc"] = f"r:{price_min},{price_max}"

    return params


def _build_params_for_kufar(sub: KufarSubscription) -> dict:
    params = {"cmp": "0", "lang": "ru", "ot": "1", "size": "10", "sort": "lst.d"}
    if sub.region_id:
        params["rgn"] = sub.region_id
        params["ar"] = sub.area_id if sub.area_id else None
    params["query"] = sub.query
    return params
