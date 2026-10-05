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
    ("forecast_type", "source_field", "output_field"),
    [
        pytest.param(
            "daily",
            "weathercode",
            "condition",
            id="daily-condition",
        ),
        pytest.param(
            "daily",
            "apparent_temperature_max",
            "apparent_temperature",
            id="daily-apparent_temperature",
        ),
        pytest.param(
            "daily",
            "precipitation_sum",
            "precipitation",
            id="daily-precipitation",
        ),
        pytest.param(
            "daily",
            "temperature_2m_max",
            "temperature",
            id="daily-temperature",
        ),
        pytest.param(
            "daily",
            "temperature_2m_min",
            "templow",
            id="daily-templow",
        ),
        pytest.param(
            "daily",
            "winddirection_10m_dominant",
            "wind_bearing",
            id="daily-wind_bearing",
        ),
        pytest.param(
            "daily",
            "windgusts_10m_max",
            "wind_gust_speed",
            id="daily-wind_gust_speed",
        ),
        pytest.param(
            "daily",
            "windspeed_10m_max",
            "wind_speed",
            id="daily-wind_speed",
        ),
        pytest.param(
            "hourly",
            "weathercode",
            "condition",
            id="hourly-condition",
        ),
        pytest.param(
            "hourly",
            "apparent_temperature",
            "apparent_temperature",
            id="hourly-apparent_temperature",
        ),
        pytest.param(
            "hourly",
            "cloudcover",
            "cloud_coverage",
            id="hourly-cloud_coverage",
        ),
        pytest.param(
            "hourly",
            "dewpoint_2m",
            "dew_point",
            id="hourly-dew_point",
        ),
        pytest.param(
            "hourly",
            "precipitation",
            "precipitation",
            id="hourly-precipitation",
        ),
        pytest.param(
            "hourly",
            "pressure_msl",
            "pressure",
            id="hourly-pressure",
        ),
        pytest.param(
            "hourly",
            "relativehumidity_2m",
            "humidity",
            id="hourly-humidity",
        ),
        pytest.param(
            "hourly",
            "temperature_2m",
            "temperature",
            id="hourly-temperature",
        ),
        pytest.param(
            "hourly",
            "winddirection_10m",
            "wind_bearing",
            id="hourly-wind_bearing",
        ),
        pytest.param(
            "hourly",
            "windgusts_10m",
            "wind_gust_speed",
            id="hourly-wind_gust_speed",
        ),
        pytest.param(
            "hourly",
            "windspeed_10m",
            "wind_speed",
            id="hourly-wind_speed",
        ),
    ],
)
async def test_forecast_missing_optional_field(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_open_meteo: AsyncMock,
    forecast_type: str,
    source_field: str,
    output_field: str,
) -> None:
    """Omit absent optional fields while preserving the remaining forecast."""
    payload = await async_load_json_object_fixture(hass, "forecast.json", DOMAIN)
    payload[forecast_type][source_field] = None
    missing_data = OpenMeteoForecast.from_json(json.dumps(payload))

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
    assert all(output_field in forecast for forecast in forecasts)
    expected = [forecast.copy() for forecast in forecasts]
    for forecast in expected:
        del forecast[output_field]
        # The weather platform always includes the temperature key.
        forecast.setdefault("temperature", None)

    mock_config_entry.runtime_data.async_set_updated_data(missing_data)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {ATTR_ENTITY_ID: "weather.home", "type": forecast_type},
        blocking=True,
        return_response=True,
    )
    assert response == {"weather.home": {"forecast": expected}}
    assert mock_open_meteo.forecast.call_count == 1


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


@pytest.mark.freeze_time("2021-11-24T03:00:00+00:00")
@pytest.mark.parametrize(
    ("timestamps", "expected_times"),
    [
        pytest.param(
            ["2021-11-24T02:00", "2021-11-24T03:00", "2021-11-24T04:00"],
            ["2021-11-24T03:00:00+00:00", "2021-11-24T04:00:00+00:00"],
            id="naive-assumed-utc",
        ),
        pytest.param(
            [
                "2021-11-24T02:00+00:00",
                "2021-11-24T03:00+00:00",
                "2021-11-24T04:00+00:00",
            ],
            ["2021-11-24T03:00:00+00:00", "2021-11-24T04:00:00+00:00"],
            id="aware-utc",
        ),
        pytest.param(
            [
                "2021-11-24T04:00+02:00",
                "2021-11-24T05:00+02:00",
                "2021-11-24T06:00+02:00",
            ],
            ["2021-11-24T05:00:00+02:00", "2021-11-24T06:00:00+02:00"],
            id="aware-positive-offset",
        ),
    ],
)
async def test_hourly_forecast_time_boundary(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_open_meteo: AsyncMock,
    timestamps: list[str],
    expected_times: list[str],
) -> None:
    """Exclude past hours, retain the current hour and preserve value alignment."""
    payload = await async_load_json_object_fixture(hass, "forecast.json", DOMAIN)
    payload["hourly"] = {key: values[:3] for key, values in payload["hourly"].items()}
    payload["hourly"]["time"] = timestamps
    mock_open_meteo.forecast.return_value = OpenMeteoForecast.from_json(
        json.dumps(payload)
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {ATTR_ENTITY_ID: "weather.home", "type": "hourly"},
        blocking=True,
        return_response=True,
    )
    forecasts = response["weather.home"]["forecast"]
    assert [forecast["datetime"] for forecast in forecasts] == expected_times
    assert [forecast["temperature"] for forecast in forecasts] == payload["hourly"][
        "temperature_2m"
    ][1:]
    assert mock_open_meteo.forecast.call_count == 1
