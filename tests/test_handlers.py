from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Chat, Message, User

from src.tg.handlers.handlers import add_tracking, command_start_handler, process_list


@pytest.mark.asyncio
@patch("src.tg.handlers.handlers.check_user_exists")
@patch("src.tg.handlers.handlers.create_user")
async def test_command_start_handler(mock_create_user, mock_check_user):
    mock_check_user.return_value = False

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = User(
        id=123456789, is_bot=False, first_name="Тест")
    mock_message.chat = Chat(id=123456789, type="private")

    mock_message.answer = AsyncMock()
    mock_message.delete = AsyncMock()

    mock_state = AsyncMock(spec=FSMContext)
    mock_state.get_data = AsyncMock(return_value={})

    mock_message.bot = AsyncMock()
    mock_message.bot.delete_message = AsyncMock()

    await command_start_handler(mock_message, mock_state)

    mock_check_user.assert_called_once_with(123456789)
    mock_create_user.assert_called_once_with(123456789)

    mock_message.answer.assert_called_once()
    args, kwargs = mock_message.answer.call_args
    assert "Привет! Я помогу отслеживать" in args[0]

    mock_message.delete.assert_called_once()


@pytest.mark.asyncio
@patch("src.tg.handlers.handlers.build_registry_platform_keyboard")
async def test_add_tracking_handler(mock_build_kb):
    mock_message = AsyncMock(spec=Message)
    mock_state = AsyncMock(spec=FSMContext)

    mock_state.get_data = AsyncMock(return_value={})
    mock_state.clear = AsyncMock()
    mock_state.update_data = AsyncMock()

    mock_message.delete = AsyncMock()
    mock_message.bot = AsyncMock()
    mock_message.bot.delete_message = AsyncMock()

    mock_sent_message = MagicMock()
    mock_sent_message.message_id = 999
    mock_message.answer = AsyncMock(return_value=mock_sent_message)

    await add_tracking(mock_message, mock_state)

    mock_state.clear.assert_called_once()

    mock_message.answer.assert_called_once()
    args, kwargs = mock_message.answer.call_args
    assert "Давай начнем слежку" in args[0]

    mock_state.update_data.assert_called_once_with(last_menu_msg_id=999)
    mock_message.delete.assert_called_once()


@pytest.mark.asyncio
@patch("src.tg.handlers.handlers.build_registry_platform_keyboard")
async def test_process_list_handler(mock_build_kb):
    mock_message = AsyncMock(spec=Message)
    mock_state = AsyncMock(spec=FSMContext)

    mock_state.get_data = AsyncMock(return_value={})
    mock_state.clear = AsyncMock()
    mock_state.update_data = AsyncMock()

    mock_message.delete = AsyncMock()
    mock_message.bot = AsyncMock()
    mock_message.bot.delete_message = AsyncMock()

    mock_sent_message = MagicMock()
    mock_sent_message.message_id = 777
    mock_message.answer = AsyncMock(return_value=mock_sent_message)

    await process_list(mock_message, mock_state)

    mock_state.clear.assert_called_once()

    mock_message.answer.assert_called_once()
    args, kwargs = mock_message.answer.call_args
    assert "Выберите платформу" in kwargs["text"]

    mock_state.update_data.assert_called_once_with(last_menu_msg_id=777)

    mock_message.delete.assert_called_once()
