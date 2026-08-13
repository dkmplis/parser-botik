from unittest.mock import patch

import pytest

from src.db.kufar_requests import add_kufar_sub
from src.db.kufar_requests import get_subs_by_user_id as get_kufar_subs
from src.db.realty_kufar_requests import add_realty_subscription, get_subs_by_user_id
from src.db.user_requests import check_user_exists, create_user
from src.deal_type import DealType
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
@patch("src.db.user_requests.AsyncSessionLocal", new=TestingSessionLocal)
async def test_user_creation():
    test_tg_id = 12345

    exists_before = await check_user_exists(tg_id=test_tg_id)
    assert exists_before is False

    await create_user(tg_id=test_tg_id)

    exists_after = await check_user_exists(tg_id=test_tg_id)
    assert exists_after is True


@pytest.mark.asyncio
@patch("src.db.realty_kufar_requests.AsyncSessionLocal", new=TestingSessionLocal)
@patch("src.db.user_requests.AsyncSessionLocal", new=TestingSessionLocal)
async def test_add_realty_subscription():
    test_tg_id = 777888

    await create_user(tg_id=test_tg_id)

    valid_deal_type_str = list(DealType)[0].value

    is_added = await add_realty_subscription(
        tg_id=test_tg_id,
        deal_type_str=valid_deal_type_str,
        rooms="2",
        price_min=15000,
        price_max=30000,
        gtsy="minsk"
    )

    assert is_added is True, "Функция add_realty_subscription вернула False!"

    subs = await get_subs_by_user_id(user_id=test_tg_id)

    assert len(subs) == 1
    assert subs[0].rooms == "2"
    assert subs[0].price_min == 15000
    assert subs[0].gtsy == "minsk"
    assert subs[0].user_id == test_tg_id


@pytest.mark.asyncio
@patch("src.db.kufar_requests.AsyncSessionLocal", new=TestingSessionLocal)
@patch("src.db.user_requests.AsyncSessionLocal", new=TestingSessionLocal)
async def test_add_kufar_subscription():
    test_tg_id = 111222333

    await create_user(tg_id=test_tg_id)

    is_added = await add_kufar_sub(
        tg_id=test_tg_id,
        query="iphone 15",
        region_id=1,
        area_id=None
    )

    assert is_added is True, "Функция add_kufar_sub вернула False!"

    subs = await get_kufar_subs(user_id=test_tg_id)

    assert len(subs) == 1
    assert subs[0].query == "iphone 15"
    assert subs[0].region_id == 1
    assert subs[0].area_id is None
    assert subs[0].user_id == test_tg_id
