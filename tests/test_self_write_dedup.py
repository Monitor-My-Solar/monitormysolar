"""Dedup the dual FW >= 4.3.0 write confirmation.

A HA write is acked on BOTH <dongle>/response and <dongle>/setting/updated.
Both carry the same value, so the /setting/updated echo of OUR OWN write must
be suppressed (the /response path already applied it). Echoes for writes we did
NOT make (Lux server, web UI, HA TCP) have no ledger entry and must still apply.

The ledger is keyed by (dongle_id, setting_suffix) and matches on the NORMALIZED
value, so "1.00" over /setting/updated matches the index 1 we recorded.
"""
import json
import time
from unittest.mock import MagicMock


def _run(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


def _prep(coordinator, monkeypatch, entity_type="number"):
    coordinator._self_write_ledger = {}
    coordinator._self_write_dedup_window = 10.0
    # Route unknown settings to a known type; catalog lookup returns (None, None).
    monkeypatch.setattr(coordinator, "determine_entity_type",
                        MagicMock(return_value=entity_type))
    # Capture refreshes so we can assert whether the echo was applied.
    refreshes = []
    monkeypatch.setattr(coordinator, "async_set_updated_data",
                        lambda data: refreshes.append(1))
    return refreshes


def test_own_write_echo_is_deduped(coordinator, monkeypatch):
    refreshes = _prep(coordinator, monkeypatch, "number")
    # HA writes ChargePowerPercentCMD=60.
    coordinator.record_self_write("dongle-test", "ChargePowerPercentCMD", 60)
    # The /setting/updated echo arrives as the string "60".
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated",
        json.dumps({"setting": "ChargePowerPercentCMD", "value": "60", "from": "HA"})))
    # Deduped: no redundant refresh, ledger entry consumed.
    assert refreshes == []
    assert coordinator._self_write_ledger == {}


def test_external_write_still_applies(coordinator, monkeypatch):
    refreshes = _prep(coordinator, monkeypatch, "number")
    # No self-write recorded — this echo is from the Lux server / web UI.
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated",
        json.dumps({"setting": "ChargePowerPercentCMD", "value": "42", "from": "Lux"})))
    assert refreshes == [1]  # applied
    assert coordinator.entities["number.dongle_test_chargepowerpercentcmd"] == 42


def test_different_value_not_deduped(coordinator, monkeypatch):
    refreshes = _prep(coordinator, monkeypatch, "number")
    # We wrote 60, but the echo reports a DIFFERENT value (a competing write
    # landed). It must apply, not be swallowed by our ledger entry.
    coordinator.record_self_write("dongle-test", "ChargePowerPercentCMD", 60)
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated",
        json.dumps({"setting": "ChargePowerPercentCMD", "value": "70", "from": "HA"})))
    assert refreshes == [1]
    assert coordinator.entities["number.dongle_test_chargepowerpercentcmd"] == 70


def test_stale_ledger_entry_not_deduped(coordinator, monkeypatch):
    refreshes = _prep(coordinator, monkeypatch, "number")
    coordinator.record_self_write("dongle-test", "ChargePowerPercentCMD", 60)
    # Age the ledger entry past the window.
    key = ("dongle-test", "chargepowerpercentcmd")
    val, _ = coordinator._self_write_ledger[key]
    coordinator._self_write_ledger[key] = (val, time.monotonic() - 60)
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated",
        json.dumps({"setting": "ChargePowerPercentCMD", "value": "60", "from": "HA"})))
    assert refreshes == [1]  # window expired -> applied, not deduped


def test_dedup_consumes_only_once(coordinator, monkeypatch):
    refreshes = _prep(coordinator, monkeypatch, "number")
    coordinator.record_self_write("dongle-test", "ChargePowerPercentCMD", 60)
    echo = json.dumps({"setting": "ChargePowerPercentCMD", "value": "60", "from": "HA"})
    _run(coordinator.process_message("dongle-test", "dongle-test/setting/updated", echo))
    # A SECOND identical echo (e.g. a genuine later external re-write) is NOT
    # deduped — the ledger entry was consumed by the first.
    _run(coordinator.process_message("dongle-test", "dongle-test/setting/updated", echo))
    assert refreshes == [1]  # first deduped, second applied


def test_select_echo_deduped_against_index(coordinator, monkeypatch):
    # The real-world case: PortMode select. We record index 1; the echo says
    # "1.00". Normalization makes them match -> deduped.
    refreshes = _prep(coordinator, monkeypatch, "select")
    portmode = {"unique_id": "SmartLoad3_PortMode",
                "options": ["Does Not Operate", "Smart Load", "Ac Coupled"]}
    monkeypatch.setattr(coordinator, "find_catalog_entry",
                        MagicMock(return_value=("select", portmode)))
    coordinator.record_self_write("dongle-test", "SmartLoad3_PortMode", 1)
    _run(coordinator.process_message(
        "dongle-test", "dongle-test/setting/updated",
        json.dumps({"setting": "SmartLoad3_PortMode", "value": "1.00", "from": "HA"})))
    assert refreshes == []  # deduped
