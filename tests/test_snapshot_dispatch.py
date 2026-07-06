"""Tests for the MQTT dispatch gating — specifically that the snapshot reply
(<dongle>/snap/input and <dongle>/snap/hold) is processed even before the ~30s
startup window closes.

Regression: the snapshot is requested during start_mqtt_subscription (well within
the 30s startup window), but the dispatcher dropped every non-status/availability
message while `_hass_startup_complete` was False — so the snap reply was silently
discarded and entities stayed empty. On FW >= 4.3.0 (change-data only) that meant
no data appeared until the next sparse change.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def _new_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


def _make_msg(topic: str, payload: str):
    msg = MagicMock()
    msg.topic = topic
    msg.payload = payload
    return msg


def _snap_payload(values: dict) -> str:
    # Snapshot replies use the same envelope as the unified /input + /hold topics.
    return json.dumps({"event": "input_state", "ts": 1717000000, "payload": values})


def _prep(coordinator, monkeypatch, startup_complete: bool):
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))
    coordinator._hass_startup_complete = startup_complete
    # mqtt_handler is only touched on /response topics; stub it to be safe.
    coordinator.mqtt_handler = MagicMock()


def test_snap_input_processed_during_startup(coordinator, monkeypatch):
    """snap/input must populate entities even while startup is still pending."""
    _prep(coordinator, monkeypatch, startup_complete=False)

    msg = _make_msg("dongle-test/snap/input", _snap_payload({"Vpv1": 235.0, "SOC": 99}))
    _run(coordinator._async_handle_mqtt_message(msg))

    assert coordinator.entities["sensor.dongle_test_vpv1"] == 235.0
    assert coordinator.entities["sensor.dongle_test_soc"] == 99


def test_snap_hold_processed_during_startup(coordinator, monkeypatch):
    """snap/hold must populate settings entities even while startup is pending."""
    _prep(coordinator, monkeypatch, startup_complete=False)

    msg = _make_msg("dongle-test/snap/hold", _snap_payload({"ChargePowerPercentCMD": 80}))
    _run(coordinator._async_handle_mqtt_message(msg))

    assert coordinator.entities["sensor.dongle_test_chargepowerpercentcmd"] == 80


def test_plain_input_still_dropped_during_startup(coordinator, monkeypatch):
    """Sanity: a plain /input change-data message is still gated during startup
    (only the snapshot reply is exempted). This documents current behavior."""
    _prep(coordinator, monkeypatch, startup_complete=False)

    msg = _make_msg("dongle-test/input", _snap_payload({"Vpv1": 1.0}))
    _run(coordinator._async_handle_mqtt_message(msg))

    assert "sensor.dongle_test_vpv1" not in coordinator.entities


def test_snap_input_processed_after_startup(coordinator, monkeypatch):
    """After startup, snap/input still routes (covered by the generic else too)."""
    _prep(coordinator, monkeypatch, startup_complete=True)

    msg = _make_msg("dongle-test/snap/input", _snap_payload({"Vpv1": 12.0}))
    _run(coordinator._async_handle_mqtt_message(msg))

    assert coordinator.entities["sensor.dongle_test_vpv1"] == 12.0
