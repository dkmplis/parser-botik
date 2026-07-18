from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from src.tg.config_manager import load_config, save_config
from src.tg.keyboards import build_subscriptions_keyboard
from src.db.user_requests import check_user_exists, create_user

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message):
    tg_id = message.from_user.id
    if not check_user_exists(tg_id):
        create_user(tg_id)
    await message.answer(
        "Привет! Я помогу отслеживать новые объявления.\n\n"
        "Добавьте товары для поиска с помощью команды /add\n"
        "Для просмотра списка отслеживаемых товаров и их удаления используйте /list")


@router.message(Command('list'))
async def list_orders_handler(message: Message):
    config = load_config()
    user_id = str(message.from_user.id)
    user_orders_list = config.get(user_id, [])
    if not user_orders_list:
        await message.answer(
            "У вас пока нет активных подписок. Для добавления используйте команду /add"
        )
        return
    response_text = "Ваши активные подписки:\n\nНажмите на товар, который хотите удалить из поиска:"

    await message.answer(
        text=response_text,
        reply_markup=build_subscriptions_keyboard(user_orders_list)
    )


@router.message(Command('add'))
async def orders_handler(message: Message):
    config = load_config()
    orders_str = message.text[4:].strip()
    if not orders_str:
        await message.answer("Введите интересующие товары. Пример \"/add iphone, рыба\"")
        return
    orders_new = [item.strip().lower() for item in orders_str.split(",")]
    user_id = str(message.from_user.id)
    existing_orders = set(config.get(user_id, []))
    new_unique_orders = [
        item for item in orders_new if item not in existing_orders]
    if not new_unique_orders:
        await message.answer("Все эти товары отслеживаются!")
        return

    unique_orders = [*existing_orders, *new_unique_orders]
    config[user_id] = unique_orders

    save_config(config)

    response_text = "В ваш список добавлены позиции:\n" + \
        "\n".join(f"- {item}" for item in new_unique_orders)

    await message.answer(response_text)


@router.callback_query(F.data.startswith("del_"))
async def delete_order_callback(callback: CallbackQuery):
    index_for_delete = int(callback.data.split('_')[1])
    user_id = str(callback.from_user.id)
    config = load_config()
    orders_list = config[user_id]
    removed_item = orders_list.pop(index_for_delete)
    config[user_id] = orders_list
    save_config(config)
    await callback.answer(f"Удаленно: {removed_item}")
    if orders_list:
        response_text = (
            "Ваши активные подписки:\n\n"
            "Нажмите на товар, который хотите удалить из поиска:"
        )
        await callback.message.edit_text(
            text=response_text,
            reply_markup=build_subscriptions_keyboard(orders_list))
    else:
        await callback.message.edit_text("Все подписки удаленны")
