# Tests

Regression protection for the per-bank → unified-topic dispatch transition.

## Coverage

- **Per-bank backward compatibility** — old firmware (< 4.3.0) keeps working
  when HA upgrades. `inputbank1`, `holdbank1`, `gridboss_holdbank1` all
  continue routing payload keys to entities.
- **Unified topics** (`/input`, `/hold`) — new firmware ≥ 4.3.0 emits flat
  payloads on these and HA routes them through the same per-key dispatcher.
- **Per-key delta** — `input_delta` envelopes update only their keys; other
  entities stay at their last value.
- **Same-key convergence** — when both the per-bank and unified topic carry
  the same key (transition window where both are emitted), last-writer wins
  on `self.entities[key]`.
- **GridBoss path** — unified `/hold` routes through `_process_gridboss_nested_data`
  and legacy `gridboss_holdbank1` keeps working.
- **Flat payload (oldest format)** — `{key: value}` without any wrapping still
  works for pre-payload-envelope firmware.

## Running

```bash
cd ~/Documents/monitormysolar
python3 -m venv .venv
.venv/bin/pip install pytest pytest-asyncio homeassistant
.venv/bin/python -m pytest
```

## Architecture

`conftest.py` builds a minimally-stubbed coordinator via `__new__` (bypassing
`__init__`) so tests don't have to spin up a full HA instance. Real
`homeassistant` package is installed in the venv to satisfy module imports;
HA's heavy lifecycle is mocked at the boundaries we care about (MQTT bus,
async_set_updated_data, async_call_later).

The tests exercise `process_message()` directly with crafted JSON payloads
and assert on the resulting `self.entities` map. This catches regressions
in the dispatch logic without needing live MQTT or a HA test harness.
