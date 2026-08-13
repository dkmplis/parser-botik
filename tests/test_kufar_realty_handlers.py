from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from src.tg.handlers.realty_kufar_handlers import (
    procces_district_choice,
    process_deal_type,
    process_min_price,
)
from src.tg.states import AddRealtyKufarSubscriptionState


@pytest.mark.asyncio
@patch("src.tg.handlers.realty_kufar_handlers.DealType")
@patch("src.tg.handlers.realty_kufar_handlers.build_rooms_keyboard")
async def test_process_deal_type(mock_kb, mock_deal_type_enum):
    mock_deal_value = MagicMock()
    mock_deal_value.value = "rent"
    mock_deal_type_enum.return_value = mock_deal_value

    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.data = "deal_rent"

    mock_callback.message = AsyncMock()
    mock_callback.message.edit_text = AsyncMock()

    mock_state = AsyncMock(spec=FSMContext)
    mock_state.update_data = AsyncMock()
    mock_state.set_state = AsyncMock()

    await process_deal_type(mock_callback, mock_state)

    mock_state.update_data.assert_called_once_with(deal_type="rent")
    mock_state.set_state.assert_called_once_with(
        AddRealtyKufarSubscriptionState.waiting_for_rooms)
    mock_callback.message.edit_text.assert_called_once()
    assert "Выберите количество комнат" in mock_callback.message.edit_text.call_args.kwargs[
        "text"]


@pytest.mark.asyncio
@patch("src.tg.handlers.realty_kufar_handlers.delete_previos_menu")
async def test_process_min_price_invalid_input(mock_del_prev):
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "дорого"
    mock_message.answer = AsyncMock()

    mock_state = AsyncMock(spec=FSMContext)
    mock_state.update_data = AsyncMock()

    await process_min_price(mock_message, mock_state)

    mock_message.answer.assert_called_once_with("Введите цифры!")
    mock_state.update_data.assert_not_called()


@pytest.mark.asyncio
@patch("src.tg.handlers.realty_kufar_handlers.search_city")
@patch("src.tg.handlers.realty_kufar_handlers.add_realty_subscription")
async def test_procces_district_choice_all(mock_add_sub, mock_search_city):
    mock_callback = AsyncMock(spec=CallbackQuery)
    # Имитируем выбор \"Все районы\"
    mock_callback.data = "rdist_all"
    mock_callback.from_user = User(id=777, is_bot=False, first_name="Тест")

    mock_callback.message = AsyncMock()
    mock_callback.message.delete = AsyncMock()
    mock_callback.answer = AsyncMock()

    mock_state = AsyncMock(spec=FSMContext)
    mock_state.get_data = AsyncMock(return_value={
        "city": "минск",
        "deal_type": "rent",
        "rooms": "2",
        "price_min": 15000,
        "price_max": 50000
    })
    mock_state.clear = AsyncMock()

    mock_search_city.return_value = {
        "gtsy": "minsk-gtsy-code",
        "districts": {"sovetsky": "dist-1", "leninsky": "dist-2"}
    }

    await procces_district_choice(mock_callback, mock_state)

    mock_add_sub.assert_called_once_with(
        777,
        deal_type_str="rent",
        rooms="2",
        price_min=15000,
        price_max=50000,
        gtsy="minsk-gtsy-code"
    )

    mock_state.clear.assert_called_once()
    mock_callback.answer.assert_called_once()
    assert "✅Подписка добавлена" in mock_callback.answer.call_args.args[0]
