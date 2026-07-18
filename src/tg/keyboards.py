from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from src.platforms import Platforms


def build_subscriptions_keyboard(
        subscriptions: list[str]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, item in enumerate(subscriptions):
        builder.button(
            text=str(item),
            callback_data=f"del_{index}"
        )
    builder.adjust(1)
    return builder.as_markup()


def build_platform_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for platform in Platforms:
        builder.button(text=platform, callback_data=platform.value)
