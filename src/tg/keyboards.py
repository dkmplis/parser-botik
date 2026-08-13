import logging

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from src.deal_type import DealType
from src.kufar.regions_cache import KUFAR_REGIONS, TOP_CITIES

logger = logging.getLogger(__name__)


def build_deal_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Покупка", callback_data=DealType.BUY.value)
    builder.button(text="Снять", callback_data=DealType.RENTAL.value)
    builder.adjust(1)
    return builder.as_markup()


def build_rooms_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="1", callback_data="room_1")
    builder.button(text="2", callback_data="room_2")
    builder.button(text="3", callback_data="room_3")
    builder.button(text="4", callback_data="room_4")
    builder.button(text="5+", callback_data="room_5")
    builder.button(text="Любое количество", callback_data="room_any")
    builder.adjust(5, 1)
    return builder.as_markup()


def build_skip_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Пропустить", callback_data="skip_step")
    return builder.as_markup()


def build_realty_cities_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _build_citites_button(builder)
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def build_kufar_cities_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _build_citites_button(builder)
    builder.button(text="Вся Беларусь", callback_data="city_all")
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup()


def _build_citites_button(builder: InlineKeyboardBuilder):
    for city in TOP_CITIES:
        city_key = city.lower()
        city_data = KUFAR_REGIONS.get(city_key, {})
        gtsy_value = city_data.get("gtsy")

        if not gtsy_value:
            logger.warning(f"Не найден gtsy для города {city}")
            continue

        builder.button(text=city, callback_data=f"city_{city_key}")
    builder.button(text="Поиск города", callback_data="city_other")


def build_realty_districts_keyboard(districts: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d_name in districts:
        builder.button(text=d_name.title(), callback_data="rdist_" + d_name)
    builder.button(text="Весь город", callback_data="rdist_all")
    builder.adjust(1)
    return builder.as_markup()


def build_registry_platform_keyboard(action: str) -> InlineKeyboardMarkup:
    from src.platforms import PLATFORMS_REGISTRY

    builder = InlineKeyboardBuilder()
    for platform_id, data in PLATFORMS_REGISTRY.items():
        builder.button(text=data["title"], callback_data=f"{action}_{platform_id}")
    builder.adjust(2)
    return builder.as_markup()


def build_registry_subscription_keyboard(
    subs: list, platform_id: str, format_func: callable
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sub in subs:
        btn_text = f"{format_func(sub)}"
        builder.button(text=btn_text, callback_data=f"del_{platform_id}_{sub.id}")
    builder.adjust(1)
    return builder.as_markup()


def build_main_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Добавить"),
    builder.button(text="📋 Список")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, is_persistent=True)
