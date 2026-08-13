import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.db.user_requests import check_user_exists, create_user
from src.platforms import PLATFORMS_REGISTRY
from src.tg.keyboards import (
    build_main_reply_keyboard,
    build_registry_platform_keyboard,
    build_registry_subscription_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext):
    await delete_previos_menu(message, state)
    tg_id = message.from_user.id
    if not await check_user_exists(tg_id):
        await create_user(tg_id)
    await message.answer(
        "👋 **Привет! Я помогу отслеживать новые объявления.**\n\n"
        "Вы можете управлять ботом с помощью **кнопок меню внизу экрана** 👇\n\n"
        "Или использовать быстрые команды:\n"
        "🔹 /add — добавить новый товар для отслеживания\n"
        "🔹 /list — посмотреть или удалить ваши подписки\n",
        parse_mode="Markdown",
        reply_markup=build_main_reply_keyboard(),
    )
    await delete_message(message)


@router.message(Command("add"))
@router.message(F.text == "➕ Добавить")
async def add_tracking(message: Message, state: FSMContext):
    await delete_previos_menu(message, state)
    await state.clear()
    sent_message = await message.answer(
        "Давай начнем слежку, выбери интересующую платформу",
        reply_markup=build_registry_platform_keyboard("add"),
    )
    await state.update_data(last_menu_msg_id=sent_message.message_id)
    await delete_message(message)


@router.message(Command("list"))
@router.message(F.text == "📋 Список")
async def process_list(message: Message, state: FSMContext):
    await delete_previos_menu(message, state)
    await state.clear()
    sent_message = await message.answer(
        text="Выберите платформу", reply_markup=build_registry_platform_keyboard("list")
    )
    await state.update_data(last_menu_msg_id=sent_message.message_id)
    await delete_message(message)


@router.callback_query(StateFilter(None), F.data.startswith("add_"))
async def process_add_start(callback: CallbackQuery, state: FSMContext):
    platform_id = callback.data.replace("add_", "")
    platform_data = PLATFORMS_REGISTRY.get(platform_id)
    if not platform_data:
        return await callback.answer("Платформа не найдена", show_alert=True)

    await state.set_state(platform_data["add_state"])
    kb_func = platform_data["add_kb"]
    await callback.message.edit_text(
        text=platform_data["add_text"], reply_markup=kb_func(
        ) if kb_func else None
    )


@router.callback_query(StateFilter(None), F.data.startswith("list_"))
async def process_list_show(callback: CallbackQuery, state: FSMContext):
    platform_id = callback.data.replace("list_", "")
    platform_data = PLATFORMS_REGISTRY.get(platform_id)
    if not platform_data:
        return await callback.answer("Ошибка платформы", show_alert=True)

    subs = await platform_data["func_list"](callback.from_user.id)
    if not subs:
        return await callback.answer(
            "У вас нет подписок в этой категории", show_alert=True
        )

    await callback.message.edit_text(
        text=f"{platform_data['title']} (нажмите что бы удалить)",
        reply_markup=build_registry_subscription_keyboard(
            subs, platform_id, platform_data["format_item"]
        ),
    )


@router.callback_query(StateFilter(None), F.data.startswith("del_"))
async def process_delete_sub(callback: CallbackQuery):
    parts = callback.data.split("_")
    sub_id = int(parts[-1])
    platform_id = "_".join(parts[1:-1])
    platform_data = PLATFORMS_REGISTRY.get(platform_id)

    if platform_data:
        await platform_data["func_delete"](sub_id)
        subs = await platform_data["func_list"](callback.from_user.id)
        if not subs:
            await callback.message.edit_text(
                "У вас нет подписок в этой категории", show_alert=True
            )
            return await callback.answer()
        await callback.message.edit_text(
            f"{platform_data['title']} (нажмите что бы удалить)",
            reply_markup=build_registry_subscription_keyboard(
                subs, platform_id, platform_data["format_item"]
            ),
        )
    else:
        await callback.answer("Ошибка при удалении", show_alert=True)


async def delete_previos_menu(message: Message, state: FSMContext):
    state_data = await state.get_data()
    last_msg_id = state_data.get("last_menu_msg_id")

    if last_msg_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id, message_id=last_msg_id
            )
        except TelegramBadRequest as e:
            logger.warning(f"Ошибка при удалении сообщения: {e}")


async def delete_message(message: Message):
    try:
        await message.delete()
    except TelegramBadRequest as e:
        logger.warning(f"Ошибка при удалении сообщения: {e}")
