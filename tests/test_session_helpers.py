"""Unit tests for the pure helpers added in the 4.0.0 work.

These cover logic that previously had no committed coverage:
- firmware version parsing / chip-suffix stripping (snapshot gate + update entity)
- build_entity_id (the drop-dongle-id naming scheme)
- migration._desired_entity_id (history-preserving rename)
- StatusFieldSensor-style nested /status field extraction

They deliberately avoid the full Home Assistant test harness — the conftest stubs
HA just enough to import the coordinator, and we exercise the static/pure logic.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# parse_fw_version / _needs_snapshot (coordinator)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("version,expected", [
    ("4.3.0.111S3", (4, 3, 0)),
    ("4.3.0", (4, 3, 0)),
    ("4.2.9.50S3", (4, 2, 9)),
    ("5.0.1.0", (5, 0, 1)),
    ("4.10.0.1", (4, 10, 0)),   # numeric, not lexical
    ("3.9.9", (3, 9, 9)),
    ("", None),                 # unparseable -> None
    ("garbage", None),
    ("4.3", None),              # < 3 segments
    ("4.x.0", None),            # non-numeric segment
])
def test_parse_fw_version(coordinator, version, expected):
    assert coordinator.parse_fw_version(version) == expected


@pytest.mark.parametrize("version,needs", [
    ("4.3.0.111S3", True),
    ("4.3.0", True),
    ("4.2.9.50S3", False),
    ("5.0.1.0", True),
    ("4.10.0.1", True),
    ("3.9.9", False),
    ("", True),        # fail-open: request anyway when unparseable
    ("garbage", True),
])
def test_needs_snapshot(coordinator, version, needs):
    assert coordinator._needs_snapshot(version) is needs


# ---------------------------------------------------------------------------
# _strip_chip_suffix (update entity) — kept as a free function copy of the logic
# so we don't need to import the UpdateEntity (which pulls in HA update component)
# ---------------------------------------------------------------------------

def _strip_chip_suffix(version):
    if not version:
        return version
    parts = version.split(".")
    last = parts[-1]
    trimmed = ""
    for ch in last:
        if ch.isdigit():
            trimmed += ch
        else:
            break
    parts[-1] = trimmed
    while parts and parts[-1] == "":
        parts.pop()
    return ".".join(parts)


@pytest.mark.parametrize("version,expected", [
    ("4.3.0.111S3", "4.3.0.111"),
    ("4.3.0C6", "4.3.0"),
    ("4.3.0", "4.3.0"),
    ("4.10.2.55S3", "4.10.2.55"),
    ("4.3.0.0C6", "4.3.0.0"),
])
def test_strip_chip_suffix(version, expected):
    assert _strip_chip_suffix(version) == expected


def test_strip_chip_suffix_matches_update_entity():
    """The free copy above must match the real implementation if importable."""
    try:
        from custom_components.monitormysolar.update import DongleFirmwareUpdate
    except Exception:
        pytest.skip("update entity not importable without full HA")
    for v in ("4.3.0.111S3", "4.3.0C6", "4.3.0", "4.10.2.55S3"):
        assert DongleFirmwareUpdate._strip_chip_suffix(v) == _strip_chip_suffix(v)


# ---------------------------------------------------------------------------
# build_entity_id (coordinator) — the drop-dongle-id scheme
# ---------------------------------------------------------------------------

def test_build_entity_id_keeps_prefix_by_default(coordinator):
    coordinator._drop_dongle_id = False
    coordinator._dongle_ids = ["dongle-AA:BB:CC:DD:EE:01"]
    eid = coordinator.build_entity_id("sensor", "dongle-AA:BB:CC:DD:EE:01", "Battery_SOC")
    assert eid == "sensor.dongle_aa_bb_cc_dd_ee_01_battery_soc"


def test_build_entity_id_drops_prefix_single_dongle(coordinator):
    coordinator._drop_dongle_id = True
    coordinator._dongle_ids = ["dongle-AA:BB:CC:DD:EE:01"]
    eid = coordinator.build_entity_id("sensor", "dongle-AA:BB:CC:DD:EE:01", "Battery_SOC")
    assert eid == "sensor.battery_soc"


def test_build_entity_id_keeps_prefix_multi_dongle_even_when_dropping(coordinator):
    """Multi-dongle must keep the prefix to avoid collisions, even with the flag."""
    coordinator._drop_dongle_id = True
    coordinator._dongle_ids = ["dongle-AA", "dongle-BB"]
    eid = coordinator.build_entity_id("sensor", "dongle-AA", "battery_soc")
    assert eid == "sensor.dongle_aa_battery_soc"


def test_build_entity_id_safe_without_flag_attribute(coordinator):
    """build_entity_id must not crash if _drop_dongle_id was never assigned."""
    if hasattr(coordinator, "_drop_dongle_id"):
        del coordinator._drop_dongle_id
    coordinator._dongle_ids = ["dongle-AA"]
    eid = coordinator.build_entity_id("sensor", "dongle-AA", "x")
    assert eid == "sensor.dongle_aa_x"


# ---------------------------------------------------------------------------
# migration._desired_entity_id
# ---------------------------------------------------------------------------

def test_desired_entity_id():
    from custom_components.monitormysolar.migration import _desired_entity_id

    fdid = "dongle_aa_bb_cc_dd_ee_01"
    fdids = [fdid]

    # drop=True strips the dongle prefix
    assert _desired_entity_id(f"sensor.{fdid}_battery_soc", True, fdids) == "sensor.battery_soc"
    assert _desired_entity_id(f"sensor.{fdid}_battery_1_voltage", True, fdids) == "sensor.battery_1_voltage"
    # drop=False re-adds it (single dongle)
    assert _desired_entity_id("sensor.battery_soc", False, fdids) == f"sensor.{fdid}_battery_soc"
    # combined/no-prefix entity untouched when dropping
    assert _desired_entity_id("sensor.combined_sync_status", True, fdids) is None
    # already in desired form -> no change
    assert _desired_entity_id(f"sensor.{fdid}_battery_soc", False, fdids) is None
    assert _desired_entity_id("sensor.battery_soc", True, fdids) is None


# ---------------------------------------------------------------------------
# Nested /status field extraction (StatusFieldSensor logic)
# ---------------------------------------------------------------------------

def _extract(blob, path):
    value = blob
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def test_status_field_extraction():
    blob = {
        "version": "4.3.0.111S3",
        "chipType": "ESP32-S3",
        "memory": {"heap_free": 15457272, "heap_frag_pct": 1},
        "mqtt": {"ha_state": "Connected"},
        "boot": {"count": 116},
        "Last_Reset_Reason": "Software reset via esp_restart",
    }
    assert _extract(blob, "version") == "4.3.0.111S3"
    assert _extract(blob, "memory.heap_free") == 15457272
    assert _extract(blob, "mqtt.ha_state") == "Connected"
    assert _extract(blob, "boot.count") == 116
    assert _extract(blob, "Last_Reset_Reason").startswith("Software reset")
    # missing path -> None, no crash
    assert _extract(blob, "memory.nonexistent") is None
    assert _extract(blob, "nothere.at.all") is None
