"""Tests for dongle-recovery snapshot re-requests.

When a dongle restarts and comes back, entities must repopulate. The coordinator
re-requests the full snapshot on: any /availability 'online' (after the first),
a boot.count change, or data resuming after a silent gap — all debounced so a
burst of triggers only sends one request.
"""
import asyncio
from unittest.mock import MagicMock


def _run(coro):
    return asyncio.run(coro)


def _prep(coordinator, monkeypatch, published=True):
    # Capture request_snapshot calls without publishing. `published` models its
    # return value: True = the request actually went out, False = the publish
    # failed or was suppressed.
    calls = []

    async def fake_request_snapshot(dongle_id, version="", force=False):
        calls.append((dongle_id, force))
        return published

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


def test_failed_publish_does_not_burn_debounce(coordinator, monkeypatch):
    """A request that never went out must not suppress the follow-up triggers.

    Recovery triggers fire while the dongle is still rebooting, so the first
    attempt can be published before it has resubscribed and is then lost. If
    the debounce window were stamped regardless, the follow-up triggers would
    be swallowed and — because FW >= 4.3.0 only streams change-data — the
    dongle's settings entities would stay empty for the rest of the session.

    This is the same rule the OTA-suppression path already follows; it just
    also has to apply when the publish itself fails.
    """
    calls = _prep(coordinator, monkeypatch, published=False)
    coordinator._last_recovery_snapshot = {}
    coordinator._recovery_snapshot_debounce = 30.0

    _run(coordinator.request_recovery_snapshot("dongle-A", "reboot detected"))
    _run(coordinator.request_recovery_snapshot("dongle-A", "availability online"))
    assert calls == [("dongle-A", True), ("dongle-A", True)]
    assert "dongle-A" not in coordinator._last_recovery_snapshot


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
