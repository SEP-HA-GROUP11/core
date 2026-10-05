"""Test for the open meteo weather entity."""

import json
from unittest.mock import AsyncMock

from open_meteo import Forecast as OpenMeteoForecast
import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.open_meteo.const import DOMAIN
from homeassistant.components.weather import (
    DOMAIN as WEATHER_DOMAIN,
    SERVICE_GET_FORECASTS,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, async_load_json_object_fixture


@pytest.mark.freeze_time("2021-11-24T03:00:00+00:00")
async def test_forecast_service(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_open_meteo: AsyncMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test forecast service."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {ATTR_ENTITY_ID: "weather.home", "type": "daily"},
        blocking=True,
        return_response=True,
    )
    assert response == snapshot(name="forecast_daily")

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {ATTR_ENTITY_ID: "weather.home", "type": "hourly"},
        blocking=True,
        return_response=True,
    )
    assert response == snapshot(name="forecast_hourly")


@pytest.mark.freeze_time("2021-11-24T03:00:00+00:00")
async def test_missing_current_weather(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_open_meteo: AsyncMock,
) -> None:
    """Missing observations leave the entity unknown without failing setup."""
    payload = await async_load_json_object_fixture(hass, "forecast.json", DOMAIN)
    payload["current_weather"] = None
    mock_open_meteo.forecast.return_value = OpenMeteoForecast.from_json(
        json.dumps(payload)
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("weather.home")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("temperature") is None
    assert state.attributes.get("wind_speed") is None
    assert state.attributes.get("wind_bearing") is None


@pytest.mark.freeze_time("2021-11-24T03:00:00+00:00")
@pytest.mark.parametrize("forecast_type", ["daily", "hourly"])
async def test_forecast_missing_section(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_open_meteo: AsyncMock,
    forecast_type: str,
) -> None:
    """A missing forecast section produces an empty public service response."""
    payload = await async_load_json_object_fixture(hass, "forecast.json", DOMAIN)
    payload[forecast_type] = None
    mock_open_meteo.forecast.return_value = OpenMeteoForecast.from_json(
        json.dumps(payload)
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {ATTR_ENTITY_ID: "weather.home", "type": forecast_type},
        blocking=True,
        return_response=True,
    )
    assert response == {"weather.home": {"forecast": []}}


@pytest.mark.freeze_time("2021-11-24T03:00:00+00:00")
@pytest.mark.parametrize(
    ("forecast_type", "source_field"),
    [("daily", "precipitation_sum"), ("hourly", "precipitation")],
)
async def test_forecast_missing_precipitation(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_open_meteo: AsyncMock,
    forecast_type: str,
    source_field: str,
) -> None:
    """An absent precipitation series is omitted rather than reported as zero."""
    payload = await async_load_json_object_fixture(hass, "forecast.json", DOMAIN)
    payload[forecast_type][source_field] = None
    mock_open_meteo.forecast.return_value = OpenMeteoForecast.from_json(
        json.dumps(payload)
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {ATTR_ENTITY_ID: "weather.home", "type": forecast_type},
        blocking=True,
        return_response=True,
    )
    forecasts = response["weather.home"]["forecast"]
    assert forecasts
    assert all("precipitation" not in forecast for forecast in forecasts)
    assert all("temperature" in forecast for forecast in forecasts)


@pytest.mark.freeze_time("2021-11-24T03:00:00+00:00")
@pytest.mark.parametrize(
    ("forecast_type", "source_field"),
    [("daily", "precipitation_sum"), ("hourly", "precipitation")],
)
async def test_forecast_zero_precipitation(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_open_meteo: AsyncMock,
    forecast_type: str,
    source_field: str,
) -> None:
    """A valid zero precipitation value remains present in every forecast."""
    payload = await async_load_json_object_fixture(hass, "forecast.json", DOMAIN)
    payload[forecast_type][source_field] = [0.0] * len(payload[forecast_type]["time"])
    mock_open_meteo.forecast.return_value = OpenMeteoForecast.from_json(
        json.dumps(payload)
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {ATTR_ENTITY_ID: "weather.home", "type": forecast_type},
        blocking=True,
        return_response=True,
    )
    forecasts = response["weather.home"]["forecast"]
    assert forecasts
    assert all(forecast["precipitation"] == 0 for forecast in forecasts)
