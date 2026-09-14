# GA1 — Open-Meteo Behavior Trace

## Scope
Behavior: configure Open-Meteo for an existing zone, initialize weather
retrieval, and obtain daily/hourly forecasts through Home Assistant.

Source baseline: ddcdfbf148ffd1ab43efc39d0476c802677b8b9d

Integration files below are under homeassistant/components/open_meteo/.

## Trace

### 1. Select a zone
File: config_flow.py
Symbol: OpenMeteoFlowHandler.async_step_user

The configuration form presents an entity selector restricted to zones.
On submission, the flow uses the selected zone entity ID as its unique ID
and checks whether that ID is already configured.

It creates an entry containing CONF_ZONE. The title comes from the zone's
state name, with "Open-Meteo" as a fallback.

Evidence: test_config_flow.py::test_full_user_flow passed, checking the form
and resulting entry. Integration setup is mocked in this test.

### 2. Initialize the integration
File: __init__.py
Symbol: async_setup_entry

Setup creates OpenMeteoDataUpdateCoordinator and awaits
async_config_entry_first_refresh(). After this completes, it stores the
coordinator in entry.runtime_data and forwards setup to Platform.WEATHER.

The ordering means weather-platform setup follows the initial refresh.

### 3. Retrieve weather data
File: coordinator.py
Symbols: OpenMeteoDataUpdateCoordinator.__init__, _async_update_data

The coordinator uses Home Assistant's shared HTTP client session to
construct an OpenMeteo client. It configures its update interval using
SCAN_INTERVAL, defined in const.py as 30 minutes.

During an update, it looks up the configured zone and reads its latitude
and longitude. It awaits the client's forecast() method, requesting
current weather plus selected daily and hourly fields.

A missing zone raises UpdateFailed. OpenMeteoError is caught and converted
to UpdateFailed with an API communication error message.

The internal HTTP implementation of the external client was not traced.

### 4. Register the weather entity
File: weather.py
Symbol: async_setup_entry

The weather platform retrieves entry.runtime_data and passes the
coordinator to one OpenMeteoWeatherEntity through async_add_entities.

The entity inherits from SingleCoordinatorWeatherEntity. Its current
weather properties read coordinator.data. Weather codes are translated
using WMO_TO_HA_CONDITION_MAP from const.py.

### 5. Produce forecast responses
File: weather.py
Symbols: _async_forecast_daily, _async_forecast_hourly

These methods convert coordinator forecast data into Home Assistant
forecast records. The hourly conversion skips timestamps earlier than
the current time and treats timezone-naive timestamps as UTC.

In test_weather.py::test_forecast_service, the test sets up a pre-created
configuration entry and calls weather.get_forecasts for weather.home,
first with type daily and then hourly.

Both responses matched their stored snapshots. This is the observable
result verified by execution.

## Failure-path evidence
- test_init.py::test_config_entry_not_ready passed:
  a simulated initial connection error resulted in SETUP_RETRY.
- test_init.py::test_config_entry_zone_removed passed:
  a missing zone resulted in SETUP_RETRY and an explanatory log.
- test_init.py::test_load_unload_config_entry passed:
  the entry reached LOADED and subsequently NOT_LOADED after unloading.

These results concern initial setup and lifecycle behavior. They do not
establish recovery behavior after a later polling failure.

## Evidence boundaries
This trace combines integration source inspection with separate tests.
The configuration-flow test mocks integration setup; the forecast test
starts from a pre-created entry and mocks the external client.

Therefore, the work verifies portions of the path rather than one
continuous browser-to-live-API execution. Core's internal dispatch and
coordinator scheduling still require source inspection for a deeper trace.

See verification.md for commands, environment, results, and limitations.
See test-output.txt for the original execution output.