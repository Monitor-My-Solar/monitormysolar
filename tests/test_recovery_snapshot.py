"""Tests for dongle-recovery snapshot re-requests.

When a dongle restarts and comes back, entities must repopulate. The coordinator
re-requests the full snapshot on: any /availability 'online' (after the first),
a boot.count change, or data resuming after a silent gap — all debounced so a
burst of triggers only sends one request.
"""
import asyncio
from unittest.mock import MagicMock


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _prep(coordinator, monkeypatch):
    # Capture request_snapshot calls without publishing.
    calls = []

    async def fake_request_snapshot(dongle_id, version="", force=False):
        calls.append((dongle_id, force))

    monkeypatch.setattr(coordinator, "request_snapshot", fake_request_snapshot)
    coordinator.current_fw_versions = {}
    return calls


def test_recovery_snapshot_debounced(coordinator, monkeypatch):
    calls = _prep(coordinator, monkeypatch)
    coordinator._last_recovery_snapshot = {}
    coordinator._recovery_snapshot_debounce = 30.0

    # Two recovery requests in quick succession -> only one snapshot.
    _run(coordinator.request_recovery_snapshot("dongle-A", "test1"))
    _run(coordinator.request_recovery_snapshot("dongle-A", "test2"))
    assert calls == [("dongle-A", True)]


def test_recovery_snapshot_per_dongle(coordinator, monkeypatch):
    calls = _prep(coordinator, monkeypatch)
    coordinator._last_recovery_snapshot = {}
    coordinator._recovery_snapshot_debounce = 30.0

    _run(coordinator.request_recovery_snapshot("dongle-A", "x"))
    _run(coordinator.request_recovery_snapshot("dongle-B", "x"))
    # Debounce is per-dongle: both fire.
    assert ("dongle-A", True) in calls and ("dongle-B", True) in calls


def test_mark_dongle_seen_gap_triggers_recovery(coordinator, monkeypatch):
    calls = _prep(coordinator, monkeypatch)
    coordinator._last_recovery_snapshot = {}
    coordinator._recovery_snapshot_debounce = 30.0
    coordinator._dongle_stale_after = 90.0
    # Simulate: last seen 200s ago (gone dark), now a message arrives.
    import time
    coordinator._dongle_last_seen = {"dongle-A": time.monotonic() - 200}

    _run(coordinator.mark_dongle_seen("dongle-A"))
    assert calls == [("dongle-A", True)]  # gap recovery fired


def test_mark_dongle_seen_no_gap_no_recovery(coordinator, monkeypatch):
    calls = _prep(coordinator, monkeypatch)
    coordinator._last_recovery_snapshot = {}
    coordinator._dongle_stale_after = 90.0
    import time
    # Seen 5s ago -> not stale -> no recovery.
    coordinator._dongle_last_seen = {"dongle-A": time.monotonic() - 5}

    _run(coordinator.mark_dongle_seen("dongle-A"))
    assert calls == []


def test_first_sighting_no_recovery(coordinator, monkeypatch):
    calls = _prep(coordinator, monkeypatch)
    coordinator._last_recovery_snapshot = {}
    coordinator._dongle_last_seen = {}  # never seen before

    _run(coordinator.mark_dongle_seen("dongle-A"))
    assert calls == []  # first message doesn't trigger recovery
