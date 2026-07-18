from aiogram.fsm.state import State, StatesGroup


class AddKufarSubscriptionState(StatesGroup):
    waiting_for_platformn = State()
    waiting_for_query = State()
    waiting_for_regions = State()
    waiting_for_regions = State()
