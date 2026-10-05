# GA1 — Open-Meteo Behavior Trace

## Scope

Behavior: configure Open-Meteo for an existing zone, initialize weather
retrieval, and obtain daily/hourly forecasts through Home Assistant.

Source baseline: ddcdfbf148ffd1ab43efc39d0476c802677b8b9d

Integration files referenced below are under
homeassistant/components/open_meteo/.

Test files referenced below are under tests/components/open_meteo/.

## Comprehension approach

We used systematic code reading to identify responsibilities, calls, and
data flow. We complemented this with targeted execution of existing tests
to check configuration, integration lifecycle, failure handling, and
forecast responses.

Code inspection explains the implementation; test execution checks
selected expectations under controlled conditions.

## Trace

### 1. Select a zone

File: config_flow.py
Symbol: OpenMeteoFlowHandler.async_step_user

The configuration form presents an entity selector restricted to zones.
On submission, the flow uses the selected zone entity ID as its unique ID
and checks whether that ID is already configured.

It creates a configuration entry containing CONF_ZONE. The title comes
from the zone's state name, with "Open-Meteo" as a fallback.

Evidence: test_config_flow.py::test_full_user_flow passed, checking the
form and resulting entry. Integration setup is mocked in this test.
The duplicate-entry check was inspected in source but is not tested by
this particular test.

### 2. Initialize the integration

File: __init__.py
Symbol: async_setup_entry

Core connection: In homeassistant/config_entries.py,
ConfigEntry.__async_setup_with_context() invokes the integration through
component.async_setup_entry(hass, self).

Open-Meteo creates OpenMeteoDataUpdateCoordinator and awaits
async_config_entry_first_refresh().

In homeassistant/helpers/update_coordinator.py,
DataUpdateCoordinator.async_config_entry_first_refresh() delegates to
_async_config_entry_first_refresh(). That method checks the configuration
entry's setup state, runs the coordinator setup hook, and calls
_async_refresh().

The refresh invokes Open-Meteo's overridden _async_update_data() and
stores its successful result in coordinator.data. Step 3 describes that
retrieval.

After the initial refresh succeeds, Open-Meteo stores the coordinator in
entry.runtime_data and awaits
hass.config_entries.async_forward_entry_setups(entry, PLATFORMS), where
PLATFORMS contains Platform.WEATHER.

This ordering makes the initial weather retrieval a prerequisite for
reaching weather-platform setup on that attempt.

### 3. Retrieve weather data

File: coordinator.py
Symbols: OpenMeteoDataUpdateCoordinator.__init__, _async_update_data

The coordinator uses Home Assistant's shared HTTP client session to
construct an OpenMeteo client. It configures its update interval using
SCAN_INTERVAL, defined in const.py as 30 minutes.

During an update, it looks up the configured zone and reads its latitude
and longitude. It awaits the client's forecast() method, requesting
current weather plus selected daily and hourly fields.

The request specifies Celsius, millimeters, kilometers per hour, and UTC.
The returned forecast object becomes coordinator.data through Core's
_async_refresh() method.

A missing zone raises UpdateFailed. OpenMeteoError is caught and converted
to UpdateFailed with an API communication error message.

The external client's internal HTTP implementation was not traced.
The configured interval was inspected in source; periodic timing was not
verified by the executed tests.

### 4. Register the weather entity

File: weather.py
Symbol: async_setup_entry

The weather platform retrieves entry.runtime_data and passes the
coordinator to one OpenMeteoWeatherEntity through async_add_entities.

The entity inherits from SingleCoordinatorWeatherEntity. Its current
weather properties read coordinator.data. Weather codes are translated
using WMO_TO_HA_CONDITION_MAP from const.py.

The entity declares support for daily and hourly forecasts. Data retrieval
is handled by the coordinator, while the entity handles weather
representation.

### 5. Produce forecast responses

Integration file: weather.py
Symbols: _async_forecast_daily, _async_forecast_hourly

Core file: homeassistant/components/weather/__init__.py
Symbols: async_setup, async_get_forecasts_service,
CoordinatorWeatherEntity.async_forecast_daily,
CoordinatorWeatherEntity.async_forecast_hour_hourly,
CoordinatorWeatherEntity._async_forecast

The Core weather component registers weather.get_forecasts with
async_get_forecasts_service().

The handler reads the requested forecast type, checks the entity's
supported features, and calls async_forecast_daily() or
async_forecast_hourly().

The inherited CoordinatorWeatherEntity methods delegate through
_async_forecast() to OpenMeteoWeatherEntity's corresponding
_async_forecast_daily() or _async_forecast_hourly() implementation.

Those implementations convert the shared coordinator's existing data
into Home Assistant forecast records. The hourly conversion treats
timezone-naive timestamps as UTC and skips timestamps earlier than the
current time.

For this integration, the service path does not itself request a fresh
forecast from the external API.

The service handler converts the native forecast records through
_convert_forecast() and returns a response containing forecast data.
If the entity returns None, the handler returns an empty forecast list.

#### Observable result

In test_weather.py::test_forecast_service, the test sets up a pre-created
configuration entry and calls weather.get_forecasts for weather.home,
first with type daily and then hourly.

The external Open-Meteo client is mocked and supplies stored forecast
data. Both service responses matched their expected snapshots:
one test passed and two snapshots passed.

This verifies forecast-service output under the test conditions, not
browser rendering or live API connectivity.

## Failure-path evidence

The following existing tests passed:

- test_init.py::test_config_entry_not_ready:
  a simulated initial connection error resulted in SETUP_RETRY.
- test_init.py::test_config_entry_zone_removed:
  a missing zone resulted in SETUP_RETRY and an explanatory log.
- test_init.py::test_load_unload_config_entry:
  the entry reached LOADED and subsequently NOT_LOADED after unloading.

### Core handling of an initial setup failure

When Open-Meteo's _async_update_data() raises UpdateFailed, Core's
DataUpdateCoordinator._async_refresh() records the exception and marks
the refresh unsuccessful.

The first-refresh method then raises ConfigEntryNotReady, retaining the
underlying cause. Because Open-Meteo awaits this refresh before forwarding
weather-platform setup, the failed attempt does not reach that forwarding
call.

In homeassistant/config_entries.py,
ConfigEntry.__async_setup_with_context() catches ConfigEntryNotReady,
sets the entry to SETUP_RETRY, and arranges another setup attempt.

When Home Assistant is running, it schedules a delayed callback.
Otherwise, it listens for EVENT_HOMEASSISTANT_STARTED.

This setup-retry mechanism is separate from the integration's configured
30-minute weather-update interval.

The executed tests confirm the SETUP_RETRY state for the two tested
failure cases. They do not verify execution or success of a later retry,
or recovery from a failure during ongoing polling.

Not every setup error follows this path: Core handles configuration and
authentication errors separately.

## Key takeaway

Open-Meteo supplies integration-specific configuration, retrieval, and
weather-data conversion. Home Assistant Core supplies the surrounding
setup lifecycle, coordinator error handling, and forecast-service
dispatch.

This separation explains how a relatively small integration participates
in a larger framework, and why understanding its behavior requires
inspecting both integration code and selected Core functions.

## Evidence boundaries

This trace combines integration and Core source inspection with separate
test executions.

The configuration-flow test mocks integration setup. The forecast test
starts from a pre-created entry and mocks the external client. Together,
the tests verify portions of the path rather than one continuous
browser-to-live-API execution.

Core integration-setup dispatch, initial-failure handling, and weather
forecast-service dispatch were inspected in source. Browser interaction,
live API connectivity, periodic scheduling, and successful recovery after
a setup failure were not verified by execution.

Five selected tests passed across two commands, including two forecast
snapshots. These results do not establish correctness of the entire
integration or Home Assistant.

See verification.md for commands, execution environment, results, and
limitations. See test-output.txt for the original execution output.