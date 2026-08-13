from aiogram.fsm.state import State, StatesGroup


class AddKufarSubscriptionState(StatesGroup):
    waiting_for_query = State()
    waiting_for_city = State()
    waiting_for_city_typing = State()


class AddRealtyKufarSubscriptionState(StatesGroup):
    waiting_for_deal_type = State()
    waiting_for_rooms = State()
    waiting_for_price_min = State()
    waiting_for_price_max = State()
    waiting_for_city = State()
    waiting_for_city_typing = State()
    waiting_for_district = State()
