from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.services.kufar_service import _fetch_data, get_valid_data


@pytest.mark.asyncio
async def test_fetch_data_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ads": [{"ad_id": 12345, "subject": "Test"}]}

    mock_client.get.return_value = mock_response

    params = {"query": "iphone 15"}
    result = await _fetch_data(mock_client, params)

    assert result == {"ads": [{"ad_id": 12345, "subject": "Test"}]}
    mock_client.get.assert_called_once()


@pytest.mark.asyncio
@patch("src.services.kufar_service._fetch_data")
@patch("src.services.kufar_service.KufarAd")
async def test_get_valid_data_time_filter(mock_kufar_ad_class, mock_fetch):
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    mock_fetch.return_value = {
        "ads": [{"fake": "data_1"}, {"fake": "data_2"}]
    }

    current_time = int(datetime.now(timezone.utc).timestamp())

    fresh_ad = MagicMock()
    fresh_ad.ad_id = 111
    fresh_ad.subject = "Свежий Айфон"
    fresh_ad.ad_link = "http://link1"
    fresh_ad.timestamp = current_time - 10
    fresh_ad.parsed_price = "1500"
    fresh_ad.image_path = "img1.jpg"

    old_ad = MagicMock()
    old_ad.ad_id = 222
    old_ad.timestamp = current_time - 300

    mock_kufar_ad_class.model_validate.side_effect = [fresh_ad, old_ad]

    result = await get_valid_data(mock_client, {"query": "iphone"})

    assert len(result) == 1

    assert result[0].id == "111"
    assert result[0].name == "Свежий Айфон"
