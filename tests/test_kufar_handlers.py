from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from src.tg.handlers.kufar_handlers import (
    process_city_choice,
    process_order_name,
    process_typed_city,
)
from src.tg.states import AddKufarSubscriptionState


@pytest.mark.asyncio
@patch("src.tg.handlers.kufar_handlers.delete_message")
@patch("src.tg.handlers.kufar_handlers.delete_previos_menu")
@patch("src.tg.handlers.kufar_handlers.build_kufar_cities_keyboard")
async def test_process_order_name(mock_kb, mock_del_prev, mock_del_msg):
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "iphone 15"

    mock_sent_msg = MagicMock()
    mock_sent_msg.message_id = 999
    mock_message.answer = AsyncMock(return_value=mock_sent_msg)

    mock_state = AsyncMock(spec=FSMContext)

    await process_order_name(mock_message, mock_state)

    mock_state.update_data.assert_any_call(query="iphone 15")
    mock_state.set_state.assert_called_once_with(
        AddKufarSubscriptionState.waiting_for_city)

    kwargs = mock_message.answer.call_args.kwargs
    assert "Выберите интересующий город" in kwargs["text"]

    mock_state.update_data.assert_called_with(last_menu_msg_id=999)


@pytest.mark.asyncio
@patch("src.tg.handlers.kufar_handlers.add_kufar_sub")
async def test_process_city_choice_all(mock_add_kufar_sub):
    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.data = "city_all"
    mock_callback.from_user = User(id=111222, is_bot=False, first_name="Тест")

    mock_callback.message = AsyncMock()
    mock_callback.message.delete = AsyncMock()
    mock_callback.answer = AsyncMock()

    mock_state = AsyncMock(spec=FSMContext)
    mock_state.get_data = AsyncMock(return_value={"query": "iphone 15"})
    mock_state.clear = AsyncMock()

    await process_city_choice(mock_callback, mock_state)

    mock_add_kufar_sub.assert_called_once_with(
        tg_id=111222, query="iphone 15", region_id=None, area_id=None
    )
    mock_state.clear.assert_called_once()
    mock_callback.message.delete.assert_called_once()
    mock_callback.answer.assert_called_once()
    assert "добавлена" in mock_callback.answer.call_args.args[0]


@pytest.mark.asyncio
@patch("src.tg.handlers.kufar_handlers.search_city")
@patch("src.tg.handlers.kufar_handlers.add_kufar_sub")
@patch("src.tg.handlers.kufar_handlers.delete_message")
@patch("src.tg.handlers.kufar_handlers.delete_previos_menu")
async def test_process_typed_city_success(mock_del_prev, mock_del_msg, mock_add_sub, mock_search_city):
    mock_search_city.return_value = {"rgn": 1, "area": 2}

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = User(id=333444, is_bot=False, first_name="Тест")
    mock_message.text = "   минск   "

    mock_sent_msg = MagicMock()
    mock_sent_msg.message_id = 777
    mock_message.answer = AsyncMock(return_value=mock_sent_msg)

    mock_state = AsyncMock(spec=FSMContext)
    mock_state.get_data = AsyncMock(return_value={"query": "ps5"})

    await process_typed_city(mock_message, mock_state)

    mock_search_city.assert_called_once_with("минск")

    mock_add_sub.assert_called_once_with(
        tg_id=333444, query="ps5", region_id=1, area_id=2
    )

    mock_state.clear.assert_called_once()

    mock_message.answer.assert_called_once()
    assert "добавлена" in mock_message.answer.call_args.args[0]
