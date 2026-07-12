"""Tests for snapshot suppression during an MQTT OTA update.

While a dongle is in OTA mode it has no snapshot queue allocated, so a
{"what":"all"} request crashes it into a reboot loop. The coordinator must
suppress every snapshot path (bootstrap, forced, and recovery) while the
update entity has marked the dongle as mid-OTA, and must not burn the
recovery debounce window while suppressed so the post-OTA refresh still
goes through.
"""
import asyncio
from unittest.mock import MagicMock


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_request_snapshot_suppressed_during_ota(coordinator, monkeypatch):
    from custom_components.monitormysolar import coordinator as coord_mod

    publishes = []

    async def fake_publish(hass, topic, payload, **kwargs):
        publishes.append((topic, payload))

    monkeypatch.setattr(coord_mod.mqtt, "async_publish", fake_publish)
    coordinator._snapshot_requested = set()

    coordinator.set_ota_in_progress("dongle-A", True)
    _run(coordinator.request_snapshot("dongle-A", "4.3.0.111S3", force=True))
    assert publishes == []
    # Suppression must not mark the snapshot as already-requested.
    assert "dongle-A" not in coordinator._snapshot_requested

    coordinator.set_ota_in_progress("dongle-A", False)
    _run(coordinator.request_snapshot("dongle-A", "4.3.0.111S3", force=True))
    assert publishes == [("dongle-A/snapshot/request", '{"what":"all"}')]


def test_recovery_snapshot_suppressed_and_debounce_not_burned(coordinator, monkeypatch):
    calls = []

    async def fake_request_snapshot(dongle_id, version="", force=False):
        calls.append((dongle_id, force))

    monkeypatch.setattr(coordinator, "request_snapshot", fake_request_snapshot)
    coordinator.current_fw_versions = {}
    coordinator._last_recovery_snapshot = {}
    coordinator._recovery_snapshot_debounce = 30.0

    coordinator.set_ota_in_progress("dongle-A", True)
    # Reconnect trigger fires mid-OTA (e.g. availability 'online').
    _run(coordinator.request_recovery_snapshot("dongle-A", "availability online"))
    assert calls == []
    # The debounce window must not have been consumed by the suppressed call.
    assert coordinator._last_recovery_snapshot == {}

    coordinator.set_ota_in_progress("dongle-A", False)
    _run(coordinator.request_recovery_snapshot("dongle-A", "post-ota"))
    assert calls == [("dongle-A", True)]


def test_ota_flag_is_per_dongle(coordinator):
    coordinator.set_ota_in_progress("dongle-A", True)
    assert coordinator.is_ota_in_progress("dongle-A")
    assert not coordinator.is_ota_in_progress("dongle-B")
    # Clearing an unset dongle is a no-op, not an error.
    coordinator.set_ota_in_progress("dongle-B", False)
    coordinator.set_ota_in_progress("dongle-A", False)
    assert not coordinator.is_ota_in_progress("dongle-A")
