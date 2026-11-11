# GA3 daily forecast limit: verification

## Recorded revisions

- Integration: Open-Meteo.
- Branch: `ga3/forecast-days`.
- Recorded upstream baseline:
  `ddcdfbf148ffd1ab43efc39d0476c802677b8b9d`.
- GA2 starting commit:
  `24818a3e6619273ea382333d706f1d636ac1e08e`.
- GA3 implementation commit:
  `1e9ea9ba74fad0e78e0238cd996ebf1b75d88c1e`.

## Implemented behaviour

Users can select "All available" or "3 days" through the integration's
options flow. Saving changed options reloads the integration.

The daily forecast service returns the first three available entries when
"3 days" is selected. If fewer entries exist, only those entries are
returned. Selecting "All available" restores the complete daily forecast.

Missing or invalid stored settings fall back to all available entries.
Unsupported form submissions are rejected.

The implementation reuses the GA2 daily forecast builder. It does not
change the API request, the client dependency, the hourly forecast mapping,
or the coordinator's original forecast data.

## Verification results

- GA2 regression baseline: 32 passing test cases and two passing snapshots.
- Extended integration suite: 46 passing test cases and two passing snapshots.
- The 14 additional cases cover option changes and restoration, invalid
  input and correction, invalid stored values, empty and short forecasts,
  and options-form defaults.
- The service test compares complete retained daily entries and checks
  unchanged hourly output under fixed time and mocked data.
- In the successful reload test, client calls increase once per changed
  option. Forecast-service calls do not add client calls.
- Applicable checks passed: Ruff linting and formatting, codespell, JSON
  validation, branch protection, Prettier, mypy, Pylint and hassfest.

## Evidence

- `evidence/implementation-commit.txt`: implementation revision.
- `evidence/integration-tests.txt`: test results and coverage summary.
- `evidence/coverage.json`: machine-readable coverage results.
- `evidence/checks.txt`: checks run on the selected changed files.

## Scope and limitations

Tests use a mocked Open-Meteo client. They verify Home Assistant integration
behaviour, not the live provider or a browser-based interaction.

The limit changes the returned daily forecast, not the downloaded payload.
A changed option triggers a reload and a fresh initial fetch. Failed fetches
may follow the existing retry behaviour.

The full Home Assistant test suite was not run.

## GA4 handover

- Add further forecast-length choices and selection during initial setup.
- Evaluate the future-change scenario by adding a five-day choice in a
  bounded experiment and recording the affected files and test results.
- Extend verification to restart persistence, multiple-entry isolation
  and reload failure/recovery as appropriate to the completed feature.
- Complete user documentation and evaluate the two quality scenarios.