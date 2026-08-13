from enum import Enum

from src.db.kufar_requests import delete_kufar_sub_by_id, get_subs_by_user_id
from src.db.realty_kufar_requests import (
    delete_sub_by_id as delete_realty_sub_by_id,
)
from src.db.realty_kufar_requests import (
    get_subs_by_user_id as get_realty_subs_by_user_id,
)
from src.deal_type import DealType
from src.kufar.regions_cache import KUFAR_REGIONS
from src.tg.keyboards import build_deal_type_keyboard
from src.tg.states import AddKufarSubscriptionState, AddRealtyKufarSubscriptionState


class Platforms(str, Enum):
    KUFAR = "platform_kufar"
    KUFAR_REALTY = "platform_kufar_realty"


def _format_realty_sub(sub) -> str:
    deal = "🏠 Аренда" if sub.deal_type == DealType.RENTAL else "💵 Покупка"

    rooms = f"{sub.rooms}-к" if sub.rooms else "Любая комн."

    p_min = sub.price_min // 100 if sub.price_min else None
    p_max = sub.price_max // 100 if sub.price_max else None

    if p_min and p_max:
        price = f"{p_min}-{p_max} BYN"
    elif p_min:
        price = f"от {p_min} BYN"
    elif p_max:
        price = f"до {p_max} BYN"
    else:
        price = "Любая цена"

    location = "Вся Беларусь"
    if sub.gtsy:
        found = False
        for city_name, city_data in KUFAR_REGIONS.items():
            if city_data.get("gtsy") == sub.gtsy:
                location = city_name.title()
                break

            for dist_name, dist_gtsy in city_data.get("districts", {}).items():
                if dist_gtsy == sub.gtsy:
                    location = f"{city_name.title()} ({dist_name})"
                    found = True
                    break

            if found:
                break

    return f"{deal} | {location} | {rooms} | {price}"


PLATFORMS_REGISTRY = {
    Platforms.KUFAR.value: {
        "title": "Куфар",
        "func_list": get_subs_by_user_id,
        "func_delete": delete_kufar_sub_by_id,
        "add_state": AddKufarSubscriptionState.waiting_for_query,
        "format_item": lambda sub: f"{sub.query}",
        "add_text": "Введите название товара для отслеживания 🔍",
        "add_kb": None,
    },
    Platforms.KUFAR_REALTY.value: {
        "title": "Куфар Недвижимость",
        "func_list": get_realty_subs_by_user_id,
        "func_delete": delete_realty_sub_by_id,
        "add_state": AddRealtyKufarSubscriptionState.waiting_for_deal_type,
        "format_item": _format_realty_sub,
        "add_text": "Выберите тип сделки 💼",
        "add_kb": build_deal_type_keyboard,
    },
}
