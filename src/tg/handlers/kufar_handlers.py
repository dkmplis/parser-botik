from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.db.kufar_requests import add_kufar_sub
from src.kufar.regions_cache import search_city
from src.tg.handlers.handlers import delete_message, delete_previos_menu
from src.tg.keyboards import build_kufar_cities_keyboard
from src.tg.states import AddKufarSubscriptionState

router = Router()


@router.message(AddKufarSubscriptionState.waiting_for_query)
async def process_order_name(message: Message, state: FSMContext):
    await delete_message(message)
    await delete_previos_menu(message, state)
    await state.update_data(query=message.text)
    await state.set_state(AddKufarSubscriptionState.waiting_for_city)
    sent_message = await message.answer(
        text="Выберите интересующий город", reply_markup=build_kufar_cities_keyboard()
    )
    await state.update_data(last_menu_msg_id=sent_message.message_id)


@router.callback_query(
    AddKufarSubscriptionState.waiting_for_city, F.data.startswith("city_")
)
async def process_city_choice(callback: CallbackQuery, state: FSMContext):
    city_action = callback.data.split("_")[1]
    if city_action == "all":
        state_data = await state.get_data()
        await add_kufar_sub(
            tg_id=callback.from_user.id,
            query=state_data["query"],
            region_id=None,
            area_id=None,
        )
        await state.clear()
        await callback.message.delete()
        await callback.answer(
            f"✅Подписка на {state_data['query']} по всей Беларуси добавлена",
            show_alert=True,
        )
    elif city_action == "other":
        await state.set_state(AddKufarSubscriptionState.waiting_for_city_typing)
        await callback.message.edit_text("Введите название города")
    else:
        succes_text = await _process_selected_city(
            callback.from_user.id, state, city_action
        )
        if succes_text:
            await callback.message.delete()
            await callback.answer(succes_text, show_alert=True)
        else:
            await callback.answer(
                "❌Город не найден. Попробуйте написать инчае", show_alert=True
            )


@router.message(AddKufarSubscriptionState.waiting_for_city_typing)
async def process_typed_city(message: Message, state: FSMContext):
    await delete_message(message)
    await delete_previos_menu(message, state)
    user_id = message.from_user.id
    city_name = message.text.strip()
    succes_text = await _process_selected_city(user_id, state, city_name)
    if succes_text:
        sent_message = await message.answer(succes_text)
    else:
        sent_message = await message.answer(
            "❌Город не найден. Попробуйте написать инчае"
        )
    await state.update_data(last_menu_msg_id=sent_message.message_id)


async def _process_selected_city(
    user_id: int, state: FSMContext, city_name: str
) -> str | None:
    cached_data = await search_city(city_name)
    if not cached_data:
        return None
    state_data = await state.get_data()
    await add_kufar_sub(
        tg_id=user_id,
        query=state_data.get("query"),
        region_id=cached_data.get("rgn"),
        area_id=cached_data.get("area"),
    )
    await state.clear()
    return f"✅Подписка на {state_data.get('query')} в г. {city_name.title()} добавлена"
