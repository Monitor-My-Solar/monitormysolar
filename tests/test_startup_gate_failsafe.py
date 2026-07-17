"""Tests for the startup-gate failsafe.

Data messages (/input, /hold, banks) are deliberately dropped for ~30s after
setup (_hass_startup_complete gate). The gate is opened by a timer; if that
timer ever fails to fire, every data message would be dropped silently forever
(entities populate once from the snapshot, then flatline). The failsafe forces
the gate open when a data message arrives past the deadline.
"""
import asyncio
import json
import time
from unittest.mock import MagicMock


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_msg(topic, payload):
    msg = MagicMock()
    msg.topic = topic
    msg.payload = payload
    return msg


def _prep(coordinator):
    coordinator._hass_startup_complete = False
    coordinator._dongle_last_seen = {}
    coordinator._last_recovery_snapshot = {}
    coordinator._dongle_stale_after = 90.0
    processed = []

    async def fake_process_message(dongle_id, topic, payload):
        processed.append(topic)

    coordinator.process_message = fake_process_message
    return processed


def test_gate_drops_before_deadline(coordinator):
    processed = _prep(coordinator)
    coordinator._gate_opened_deadline = time.monotonic() + 60
    coordinator._startup_dropped_count = 0

    msg = _make_msg("dongle-A/input", json.dumps({"soc": 55}))
    _run(coordinator._async_handle_mqtt_message(msg))

    assert processed == []
    assert coordinator._hass_startup_complete is False
    assert coordinator._startup_dropped_count == 1


def test_gate_forced_open_past_deadline(coordinator):
    processed = _prep(coordinator)
    coordinator._gate_opened_deadline = time.monotonic() - 1  # deadline passed
    coordinator._startup_dropped_count = 5

    msg = _make_msg("dongle-A/input", json.dumps({"soc": 55}))
    _run(coordinator._async_handle_mqtt_message(msg))

    # The message that hit the failsafe is processed, not dropped, and the
    # gate stays open for everything after it.
    assert processed == ["dongle-A/input"]
    assert coordinator._hass_startup_complete is True

    msg2 = _make_msg("dongle-A/hold", json.dumps({"ACChgStart": "01:00"}))
    _run(coordinator._async_handle_mqtt_message(msg2))
    assert processed == ["dongle-A/input", "dongle-A/hold"]


def test_gate_without_deadline_attr_keeps_dropping(coordinator):
    """__new__-built coordinators (and pre-deadline messages) keep old semantics."""
    processed = _prep(coordinator)
    # No _gate_opened_deadline attribute at all.
    if hasattr(coordinator, "_gate_opened_deadline"):
        del coordinator._gate_opened_deadline

    msg = _make_msg("dongle-A/input", json.dumps({"soc": 55}))
    _run(coordinator._async_handle_mqtt_message(msg))

    assert processed == []
    assert coordinator._hass_startup_complete is False
