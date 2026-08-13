from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.db.realty_kufar_requests import add_realty_subscription
from src.deal_type import DealType
from src.kufar.regions_cache import search_city
from src.tg.handlers.handlers import delete_message, delete_previos_menu
from src.tg.keyboards import (
    build_realty_cities_keyboard,
    build_realty_districts_keyboard,
    build_rooms_keyboard,
    build_skip_keyboard,
)
from src.tg.states import AddRealtyKufarSubscriptionState

router = Router()


@router.callback_query(
    AddRealtyKufarSubscriptionState.waiting_for_deal_type, F.data.startswith(
        "deal_")
)
async def process_deal_type(callback: CallbackQuery, state: FSMContext):
    deal_value = DealType(callback.data)
    await state.update_data(deal_type=deal_value.value)
    await state.set_state(AddRealtyKufarSubscriptionState.waiting_for_rooms)
    await callback.message.edit_text(
        text="Выберите количество комнат", reply_markup=build_rooms_keyboard()
    )


@router.callback_query(
    AddRealtyKufarSubscriptionState.waiting_for_rooms, F.data.startswith(
        "room_")
)
async def process_rooms(callback: CallbackQuery, state: FSMContext):
    rooms_value = callback.data.split("_")[1]
    if rooms_value == "any":
        rooms_value = None
    await state.update_data(rooms=rooms_value)
    await state.set_state(AddRealtyKufarSubscriptionState.waiting_for_price_min)
    sent_message = await callback.message.edit_text(
        text="Введите минимальную цену в BYN или пропустите этот шаг",
        reply_markup=build_skip_keyboard(),
    )
    state.update_data(last_menu_msg_id=sent_message.message_id)


@router.message(
    AddRealtyKufarSubscriptionState.waiting_for_price_min,
)
async def process_min_price(message: Message, state: FSMContext):
    await delete_previos_menu(message, state)
    if not message.text.isdigit():
        await message.answer("Введите цифры!")
        return
    await state.update_data(price_min=int(message.text) * 100)
    await state.set_state(AddRealtyKufarSubscriptionState.waiting_for_price_max)
    await message.delete()
    sent_message = await message.answer(
        "Введите максимальную цену или пропустите шаг",
        reply_markup=build_skip_keyboard(),
    )
    await state.update_data(last_menu_msg_id=sent_message.message_id)


@router.message(
    AddRealtyKufarSubscriptionState.waiting_for_price_max,
)
async def process_max_price(message: Message, state: FSMContext):
    await delete_previos_menu(message, state)
    if not message.text.isdigit():
        await message.answer("Введите цифры!")
        return
    await state.update_data(price_max=int(message.text) * 100)
    await state.set_state(AddRealtyKufarSubscriptionState.waiting_for_city)
    await message.delete()
    sent_message = await message.answer(
        text="Выберите город из списка или поищите другой",
        reply_markup=build_realty_cities_keyboard(),
    )
    await state.update_data(last_menu_msg_id=sent_message.message_id)


@router.callback_query(
    AddRealtyKufarSubscriptionState.waiting_for_price_min, F.data == "skip_step"
)
async def process_skip_price_min(callback: CallbackQuery, state: FSMContext):
    await state.update_data(price_min=None)
    await state.set_state(AddRealtyKufarSubscriptionState.waiting_for_price_max)
    await callback.message.edit_text(
        "Введите максимальную суммму или пропустите шаг",
        reply_markup=build_skip_keyboard(),
    )


@router.callback_query(
    AddRealtyKufarSubscriptionState.waiting_for_price_max, F.data == "skip_step"
)
async def process_skip_price_max(callback: CallbackQuery, state: FSMContext):
    await state.update_data(price_max=None)
    await state.set_state(AddRealtyKufarSubscriptionState.waiting_for_city)
    await callback.message.edit_text(
        text="Выберите город из списка или поищите другой",
        reply_markup=build_realty_cities_keyboard(),
    )


@router.callback_query(
    AddRealtyKufarSubscriptionState.waiting_for_city, F.data.startswith(
        "city_")
)
async def process_city_choice(callback: CallbackQuery, state: FSMContext):
    city_action = callback.data.split("_")[1]
    if city_action == "other":
        await state.set_state(AddRealtyKufarSubscriptionState.waiting_for_city_typing)
        await callback.message.edit_text(text="Введите название города")
    else:
        text, kb, is_error = await _process_selected_city(
            callback.from_user.id, state, city_action
        )
        if is_error:
            await callback.answer(text, show_alert=True)
        else:
            sent_message = await callback.message.edit_text(text=text, reply_markup=kb)
            await state.update_data(last_menu_msg_id=sent_message.message_id)


@router.message(AddRealtyKufarSubscriptionState.waiting_for_city_typing)
async def process_typed_city(message: Message, state: FSMContext):
    await delete_message(message)
    await delete_previos_menu(message, state)
    city_name = message.text.strip()
    text, kb, is_error = await _process_selected_city(
        message.from_user.id, state, city_name
    )
    if is_error:
        sent_message = await message.answer(text)
    else:
        sent_message = await message.answer(text=text, reply_markup=kb)
    await state.update_data(last_menu_msg_id=sent_message.message_id)


@router.callback_query(
    AddRealtyKufarSubscriptionState.waiting_for_district, F.data.startswith(
        "rdist_")
)
async def procces_district_choice(callback: CallbackQuery, state: FSMContext):
    dist_name = callback.data.split("_")[1]
    state_data = await state.get_data()
    city = state_data.get("city")
    cached_data = await search_city(city)
    if dist_name == "all":
        gtsy_string = cached_data.get("gtsy")
        dist_allert = "все районы"
    else:
        gtsy_string = cached_data.get("districts")[dist_name]
        dist_allert = dist_name
    await state.clear()
    await add_realty_subscription(
        callback.from_user.id,
        deal_type_str=state_data.get("deal_type"),
        rooms=state_data.get("rooms"),
        price_min=state_data.get("price_min"),
        price_max=state_data.get("price_max"),
        gtsy=gtsy_string,
    )
    await callback.message.delete()
    await callback.answer(
        f"✅Подписка добавлена\nГород: {city.title()}\nРайон: {dist_allert} ",
        show_alert=True,
    )


async def _process_selected_city(
    user_id: int, state: FSMContext, city_name: str
) -> tuple[str, any, bool]:
    cached_data = await search_city(city_name)

    if not cached_data:
        return "❌Город не найден. Попробуйте написать инчае", None, True
    print(f"ДАННЫЕ ИЗ КЭША ДЛЯ {city_name}: {cached_data}")
    await state.update_data(city=city_name.lower())
    districts = cached_data.get("districts")

    if not districts:
        gtsy_string = cached_data.get("gtsy")
        state_data = await state.get_data()
        await state.clear()
        await add_realty_subscription(
            user_id,
            deal_type_str=state_data.get("deal_type"),
            rooms=state_data.get("rooms"),
            price_min=state_data.get("price_min"),
            price_max=state_data.get("price_max"),
            gtsy=gtsy_string,
        )
        return f"✅Подписка добавлена\nГород: {state_data['city'].title()}", None, False

    else:
        await state.set_state(AddRealtyKufarSubscriptionState.waiting_for_district)
        return "Выберите район", build_realty_districts_keyboard(districts), False
