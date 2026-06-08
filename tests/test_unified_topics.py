"""Regression tests for the unified /input + /hold MQTT topic dispatch.

Goals:
  * Per-bank topics (inputbank1, holdbank2, gridboss_holdbank1, etc.)
    still route correctly — pre-4.3.0 firmware must keep working.
  * Unified topics (/input, /hold) route the same keys to the same
    entities, regardless of which topic delivered them.
  * Delta payloads update only the included keys and leave others alone.
  * Same key arriving on both old and new topics converges to the latest
    value (last-writer-wins on self.entities[key]).
  * GridBoss-shaped payloads land in the GridBoss processor and entities.

We exercise process_message() directly with crafted JSON payloads. The
coordinator's MQTT subscription and HA-side wiring is mocked out — only
the dispatch logic is under test.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import pytest


def _run(coro):
    """Tiny event-loop runner so each test can call async process_message."""
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def _new_event_loop():
    """Ensure each test gets a fresh event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


def _make_per_bank_payload(values: dict) -> str:
    """Wrap values in the legacy {Serialnumber, payload, events} envelope."""
    return json.dumps({
        "Serialnumber": "TEST1234567",
        "payload": values,
        "events": {},
    })


def _make_unified_payload(event: str, values: dict, ts: int = 1717000000) -> str:
    """Wrap values in the new {event, ts, payload} envelope."""
    return json.dumps({"event": event, "ts": ts, "payload": values})


# ---------------------------------------------------------------------------
# Per-bank backward compatibility — these must keep working on old firmware
# ---------------------------------------------------------------------------

def test_per_bank_input_still_routes(coordinator, monkeypatch):
    """Legacy inputbank1 topic routes its payload keys to entities."""
    # Avoid the real determine_entity_type heavy lookup; assume "sensor".
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))

    payload = _make_per_bank_payload({"Vpv1": 235.0, "Ppv1": 2462})
    _run(coordinator.process_message("dongle-test",
                                     "dongle-test/inputbank1", payload))

    assert coordinator.entities["sensor.dongle_test_vpv1"] == 235.0
    assert coordinator.entities["sensor.dongle_test_ppv1"] == 2462


def test_per_bank_hold_still_routes(coordinator, monkeypatch):
    """Legacy holdbank1 topic still drives settings entities."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="number"))
    payload = _make_per_bank_payload({"ChargePowerPercentCMD": 80})
    _run(coordinator.process_message("dongle-test",
                                     "dongle-test/holdbank1", payload))
    assert coordinator.entities["number.dongle_test_chargepowerpercentcmd"] == 80


# ---------------------------------------------------------------------------
# Unified topics — the new path
# ---------------------------------------------------------------------------

def test_unified_input_routes_all_keys(coordinator, monkeypatch):
    """Unified /input payload routes every key to its entity."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))
    payload = _make_unified_payload("input_state", {
        "Vpv1": 235.0,
        "Ppv1": 2462,
        "SOC": 99,
        "Vbat": 55.2,
    })
    _run(coordinator.process_message("dongle-test",
                                     "dongle-test/input", payload))
    assert coordinator.entities["sensor.dongle_test_vpv1"] == 235.0
    assert coordinator.entities["sensor.dongle_test_ppv1"] == 2462
    assert coordinator.entities["sensor.dongle_test_soc"] == 99
    assert coordinator.entities["sensor.dongle_test_vbat"] == 55.2


def test_unified_input_delta_only_updates_changed(coordinator, monkeypatch):
    """input_delta payload updates only its keys; others stay untouched."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))

    # Initial full state.
    full = _make_unified_payload("input_state", {
        "Vpv1": 235.0,
        "Ppv1": 2462,
        "SOC": 99,
    })
    _run(coordinator.process_message("dongle-test",
                                     "dongle-test/input", full))

    # Delta — only Ppv1 changes.
    delta = _make_unified_payload("input_delta", {"Ppv1": 2510})
    _run(coordinator.process_message("dongle-test",
                                     "dongle-test/input", delta))

    assert coordinator.entities["sensor.dongle_test_ppv1"] == 2510
    # Untouched entities keep their prior values.
    assert coordinator.entities["sensor.dongle_test_vpv1"] == 235.0
    assert coordinator.entities["sensor.dongle_test_soc"] == 99


def test_unified_hold_routes(coordinator, monkeypatch):
    """Unified /hold routes settings keys to number/select/switch entities."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="number"))
    payload = _make_unified_payload("hold_state", {
        "ChargePowerPercentCMD": 80,
        "DischgPowerPercentCMD": 50,
        "ACChgPowerCMD": 100,
    })
    _run(coordinator.process_message("dongle-test",
                                     "dongle-test/hold", payload))
    assert coordinator.entities["number.dongle_test_chargepowerpercentcmd"] == 80
    assert coordinator.entities["number.dongle_test_dischgpowerpercentcmd"] == 50
    assert coordinator.entities["number.dongle_test_acchgpowercmd"] == 100


def test_same_key_on_both_topics_last_writer_wins(coordinator, monkeypatch):
    """Per-bank + unified topics on the same dongle converge to latest value."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))

    # Old firmware emit
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/inputbank1",
        _make_per_bank_payload({"Vpv1": 235.0}),
    ))
    assert coordinator.entities["sensor.dongle_test_vpv1"] == 235.0

    # New firmware emit a moment later — overwrites
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/input",
        _make_unified_payload("input_delta", {"Vpv1": 240.0}),
    ))
    assert coordinator.entities["sensor.dongle_test_vpv1"] == 240.0

    # Old emit again (broker fanout) — overwrites again
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/inputbank1",
        _make_per_bank_payload({"Vpv1": 238.0}),
    ))
    assert coordinator.entities["sensor.dongle_test_vpv1"] == 238.0


# ---------------------------------------------------------------------------
# GridBoss
# ---------------------------------------------------------------------------

def test_unified_hold_routes_gridboss(gridboss_coordinator, monkeypatch):
    """Unified /hold on a GridBoss dongle goes through the nested processor."""
    monkeypatch.setattr(gridboss_coordinator, "determine_entity_type",
                        MagicMock(return_value="number"))

    payload = _make_unified_payload("hold_state", {
        "Generator_enable": 1,
        "Generator_Warmup": 120,
    })
    _run(gridboss_coordinator.process_message(
        "dongle-test", "dongle-test/hold", payload))

    # GridBoss flatten happens via _process_gridboss_nested_data — flat keys
    # still land on entities.
    assert gridboss_coordinator.entities["number.dongle_test_generator_enable"] == 1
    assert gridboss_coordinator.entities["number.dongle_test_generator_warmup"] == 120


def test_legacy_gridboss_holdbank_still_routes(gridboss_coordinator, monkeypatch):
    """Old gridboss_holdbank1 topic still works for pre-4.3 firmware."""
    monkeypatch.setattr(gridboss_coordinator, "determine_entity_type",
                        MagicMock(return_value="number"))

    payload = _make_per_bank_payload({"Generator_enable": 1})
    _run(gridboss_coordinator.process_message(
        "dongle-test", "dongle-test/gridboss_holdbank1", payload))
    assert gridboss_coordinator.entities["number.dongle_test_generator_enable"] == 1


# ---------------------------------------------------------------------------
# Envelope variants — make sure legacy "flat" payloads still parse
# ---------------------------------------------------------------------------

def test_flat_payload_no_envelope(coordinator, monkeypatch):
    """The oldest format — flat {key: value} without any wrapping — works."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))
    payload = json.dumps({"Vpv1": 235.0, "Ppv1": 2462})
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/inputbank1", payload))
    assert coordinator.entities["sensor.dongle_test_vpv1"] == 235.0
    assert coordinator.entities["sensor.dongle_test_ppv1"] == 2462
