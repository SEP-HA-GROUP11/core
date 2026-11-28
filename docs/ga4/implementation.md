# GA4 implementation record: Open-Meteo daily forecast limit

Items marked **TODO** are filled in when the underlying work is merged.

## Revisions

| Record | Revision |
|---|---|
| Upstream baseline | `ddcdfbf148ffd1ab43efc39d0476c802677b8b9d` |
| GA3 submission (Phase 4 starting commit) | `ee69693fb7d` |
| GA3 feature and tests | `1e9ea9ba74f` |
| Group branch | `ga4/main` |
| Final submission commit | **TODO**: `git rev-parse --short HEAD` on `ga4/main` after the last merge |

## GA3 remaining-work list

| GA3 item | Status | Reason and evidence |
|---|---|---|
| Selection during initial setup | Completed | Setup form has the daily forecast limit dropdown. Choice is stored in entry options and shares one selector with the options flow. PR: **TODO**. Tests: `test_full_user_flow`, `test_user_flow_forecast_days`, `test_user_flow_invalid_forecast_days`. |
| Restart persistence | **TODO** | **TODO** |
| Multiple-entry isolation | **TODO** | **TODO** |
| Reload failure and recovery | **TODO** | **TODO** |
| Additional forecast-length choices | Deferred | Optional in GA3. Not needed for the acceptance criteria, and GA4 allows no new scope. Consequence: only "All available" and "3 days" exist. |
| User documentation | **TODO** | **TODO** |
| Evaluation of the two quality scenarios | **TODO** | **TODO** |

## IA3 recommendation

- Recommendation: **TODO**
- Contributor: **TODO**
- Why selected: **TODO**
- Outcome (implemented, adapted or rejected): **TODO**
- Evidence: **TODO**

## Initial-setup change

- Setup form (`config_flow.py`): optional `forecast_days` dropdown, default `all`.
- Storage: the choice goes into `options`; `data` still holds only the zone. This is where `weather.py` already reads it, so `weather.py`, `coordinator.py` and `const.py` are unchanged.
- Shared selector: `_forecast_days_selector()` is used by the setup and options forms, so the choices cannot drift apart.
- Labels: `strings.json` gains the setup-step field label. `translations/en.json` is regenerated.
- Existing entries: unaffected. They have no option and keep returning all available days. No migration, `VERSION` stays 1.

## Verification of the setup change

Commands, run from the repository root with `.venv` active:

```
python3 -m pytest -q tests/components/open_meteo
uv run --no-sync prek run --files \
  homeassistant/components/open_meteo/config_flow.py \
  homeassistant/components/open_meteo/strings.json \
  tests/components/open_meteo/test_config_flow.py
```

Results on commit `74119279fca`:

- `tests/components/open_meteo`: 51 passed (46 GA3 baseline plus 5 new cases) and 2 snapshots passed.
- `prek`: ruff check and format, codespell, JSON check, Prettier, mypy, Pylint and hassfest passed. Hooks with no files to check were skipped.
- Not run: the full Home Assistant test suite.

## Pull requests and review evidence

| Change | Author | PR | Reviewer | Review link |
|---|---|---|---|---|
| Initial-setup forecast limit | Hussein | **TODO** | **TODO** | **TODO** |
| This record | Hussein | **TODO** | **TODO** | **TODO** |
