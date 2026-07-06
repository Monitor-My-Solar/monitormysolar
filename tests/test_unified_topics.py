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


# ---------------------------------------------------------------------------
# Cross-brand parity — Deye and GridBoss field names match Lux for the
# common keys, so HA's entity dispatch is brand-agnostic on those keys.
# ---------------------------------------------------------------------------

def test_deye_input_routes_canonical_keys(coordinator, monkeypatch):
    """Deye unified /input uses the same Vpv1/Ppv1/SOC keys as Lux."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))
    # Switch the fixture to a Deye brand so determine_entity_type behaves
    # consistently — but the routing logic itself doesn't gate by brand
    # for the per-key entity update.
    coordinator.entry.data = {"inverter_brand": "deye_standard"}
    payload = _make_unified_payload("input_state", {
        "Vpv1": 720.0,        # Deye PV strings are higher voltage
        "Ppv1": 2200,
        "SOC": 87,
        "Vbat": 52.3,
        "Pload": 1900,
    })
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/input", payload))
    assert coordinator.entities["sensor.dongle_test_vpv1"] == 720.0
    assert coordinator.entities["sensor.dongle_test_ppv1"] == 2200
    assert coordinator.entities["sensor.dongle_test_soc"] == 87
    assert coordinator.entities["sensor.dongle_test_pload"] == 1900


def test_deye_entities_catalog_consistency():
    """The Deye ENTITIES entry stays structurally consistent with the catalog.

    Guards against regressions in the Deye brand registry: it must be a
    dict-of-entity-types (matching the Lux shape so _create_entities_for_dongle
    can walk it), every entity must carry a unique_id, and no unique_id may be
    duplicated within the brand (duplicates collide on entity_id).
    """
    from custom_components.monitormysolar.const import ENTITIES

    assert "Deye" in ENTITIES, "Deye brand entry missing"
    deye = ENTITIES["Deye"]
    assert isinstance(deye, dict)

    seen = []
    for entity_type, banks in deye.items():
        # Mirrors the dict-of-lists shape the coordinator expects.
        assert isinstance(banks, dict), f"{entity_type} must be a dict of banks"
        for bank_name, entities in banks.items():
            for ent in entities:
                assert "unique_id" in ent, f"{entity_type}/{bank_name} missing unique_id"
                assert "type" in ent
                # source must never masquerade as a GridBoss entity, or the
                # GridBoss gating would hide every Deye entity.
                assert not ent.get("source", "").startswith("gridboss_")
                seen.append(ent["unique_id"])

    dupes = {u for u in seen if seen.count(u) > 1}
    assert not dupes, f"duplicate Deye unique_ids: {sorted(dupes)}"
    # Sanity: the catalog has 100+ keys; make sure we actually populated them.
    assert len(seen) > 100


def test_deye_hold_routes_settings_keys(coordinator, monkeypatch):
    """Deye unified /hold settings keys route by their exact catalog names."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="number"))
    coordinator.entry.data = {"inverter_brand": "Deye"}
    payload = _make_unified_payload("hold_state", {
        "ChargeCurr": 100,
        "DischgCurr": 120,
        "ACChgStartSOC": 40,
        "GenChgStartSOC": 30,
    })
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/hold", payload))
    assert coordinator.entities["number.dongle_test_chargecurr"] == 100
    assert coordinator.entities["number.dongle_test_dischgcurr"] == 120
    assert coordinator.entities["number.dongle_test_acchgstartsoc"] == 40
    assert coordinator.entities["number.dongle_test_genchgstartsoc"] == 30


def test_deye_input_routes_family_specific_keys(coordinator, monkeypatch):
    """Deye-specific input keys (split-phase, gen, meter) route to entities."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))
    coordinator.entry.data = {"inverter_brand": "Deye"}
    payload = _make_unified_payload("input_state", {
        "VacR": 121.0,
        "VacS": 120.5,
        "PgridL1": 800,
        "EgenDay": 3.2,
        "Pmeter": -450,
        "Tradiator1": 41.0,
    })
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/input", payload))
    assert coordinator.entities["sensor.dongle_test_vacr"] == 121.0
    assert coordinator.entities["sensor.dongle_test_pgridl1"] == 800
    assert coordinator.entities["sensor.dongle_test_egenday"] == 3.2
    assert coordinator.entities["sensor.dongle_test_pmeter"] == -450


def test_gridboss_input_routes_state_and_codes(gridboss_coordinator, monkeypatch):
    """GridBoss unified /input includes State + FaultCode + WarningCode."""
    monkeypatch.setattr(gridboss_coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))
    payload = _make_unified_payload("input_state", {
        "State": "0x02",
        "FaultCode": 0,
        "WarningCode": 0,
        "gridRMSVoltage": 240,
    })
    _run(gridboss_coordinator.process_message(
        "dongle-test", "dongle-test/input", payload))
    assert gridboss_coordinator.entities["sensor.dongle_test_state"] == "0x02"
    assert gridboss_coordinator.entities["sensor.dongle_test_faultcode"] == 0
    assert gridboss_coordinator.entities["sensor.dongle_test_gridrmsvoltage"] == 240


# ---------------------------------------------------------------------------
# Retained snapshot bootstrap — input_state with every key (force_full)
# behaves identically to an initial fresh subscribe.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# setting/updated — durable write-confirmation envelope
# ---------------------------------------------------------------------------

def test_setting_updated_routes_to_entity(coordinator, monkeypatch):
    """<dongle>/setting/updated immediately mirrors the new value to its entity."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="number"))
    payload = json.dumps({
        "setting": "ChargePowerPercentCMD",
        "value": 75,
        "reg": 64,
        "from": "MMS",
        "ts": 1717000000,
    })
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated", payload))
    assert coordinator.entities["number.dongle_test_chargepowerpercentcmd"] == 75


def test_setting_updated_bitfield_per_bit_event(coordinator, monkeypatch):
    """Each changed bit on a packed BITFIELD register arrives as its own event.

    The dongle resolves a write to a packed register (e.g. Lux reg 21 holds
    EPS, OVFLoadDerate, ACCharge, AntiIsland, ...) by xor-diffing pre vs new
    and emitting one setting/updated per changed bit with the bit's symbolic
    name and 0/1 state. HA routes each one independently — same dispatch
    code, no special handling needed.
    """
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="switch"))

    # ACCharge bit flipped on.
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated",
        json.dumps({
            "setting": "ACCharge",
            "value":   "1",
            "from":    "MMS",
            "ts":      1717000000,
        }),
    ))
    # Value is normalized from the string "1" to the switch's native bit 1.
    assert coordinator.entities["switch.dongle_test_accharge"] == 1

    # EPS bit flipped on (a separate event for the same write that toggled it).
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated",
        json.dumps({
            "setting": "EPS",
            "value":   "1",
            "from":    "MMS",
            "ts":      1717000000,
        }),
    ))
    assert coordinator.entities["switch.dongle_test_eps"] == 1


def test_setting_updated_envelope_without_reg_field(coordinator, monkeypatch):
    """HA-shaped envelope (no `reg` field) still routes correctly.

    Dongle v4.3+ omits the raw register number from the HA-bound envelope
    because HA addresses entities by symbolic name only. The handler must
    not require `reg` to be present.
    """
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="number"))
    payload = json.dumps({
        "setting": "ChargePowerPercentCMD",
        "value":   "60",
        "from":    "HA",
        "ts":      1717000000,
        # no `reg` field — HA envelope omits it
    })
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated", payload))
    # "60" is normalized to the number's native int 60.
    assert coordinator.entities["number.dongle_test_chargepowerpercentcmd"] == 60


def test_setting_updated_handles_missing_fields(coordinator):
    """Malformed setting/updated envelopes are silently ignored, not crashing."""
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated", '{"from":"MMS"}'))
    # No entities should be created — incomplete envelope is non-fatal.
    assert not coordinator.entities


def test_input_state_treated_as_full_snapshot(coordinator, monkeypatch):
    """input_state envelope updates all keys regardless of prior values."""
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value="sensor"))

    # Seed an old value via a delta.
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/input",
        _make_unified_payload("input_delta", {"Vpv1": 100.0}),
    ))
    assert coordinator.entities["sensor.dongle_test_vpv1"] == 100.0

    # input_state arrives (full retained snapshot) — overwrites everything.
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/input",
        _make_unified_payload("input_state", {
            "Vpv1": 250.0,
            "Ppv1": 3000,
            "SOC": 95,
        }),
    ))
    assert coordinator.entities["sensor.dongle_test_vpv1"] == 250.0
    assert coordinator.entities["sensor.dongle_test_ppv1"] == 3000
    assert coordinator.entities["sensor.dongle_test_soc"] == 95
