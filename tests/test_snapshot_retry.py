"""Snapshot requests are verified and retried until the reply arrives.

Publishing a snapshot request is not the same as delivering one: the recovery
triggers fire while a dongle is still reconnecting, so a request can go out
before it has resubscribed. On FW >= 4.3.0 nothing re-sends hold registers, so
a single lost request leaves every setting entity empty for the session.

The coordinator arms a timer on each successful publish and disarms it when
<dongle>/snap/hold arrives.
"""
import asyncio


def _run(coro):
    return asyncio.run(coro)


def _fire(timers):
    """Fire the oldest armed timer, one-shot: a fired handle is spent."""
    _delay, cb = timers.pop(0)
    return _run(cb(None))


def _prep(coordinator, monkeypatch):
    """Wire a coordinator with a captured async_call_later and no real publish."""
    from custom_components.monitormysolar import coordinator as coord_mod

    published = []

    async def fake_publish(hass, topic, payload, **kwargs):
        published.append(topic)

    monkeypatch.setattr(coord_mod.mqtt, "async_publish", fake_publish)

    timers = []  # (delay, callback)

    def fake_call_later(hass, delay, cb):
        timers.append((delay, cb))
        cancelled = {"done": False}

        def _cancel():
            cancelled["done"] = True
            for i, (d, c) in enumerate(timers):
                if c is cb:
                    timers.pop(i)
                    break

        return _cancel

    monkeypatch.setattr(coord_mod, "async_call_later", fake_call_later)

    coordinator._snapshot_requested = set()
    coordinator._snapshot_retry = {}
    coordinator._snapshot_retry_attempts = {}
    coordinator._snapshot_retry_delay = 20.0
    coordinator._snapshot_max_retries = 3
    return published, timers


def test_successful_publish_arms_a_retry(coordinator, monkeypatch):
    published, timers = _prep(coordinator, monkeypatch)

    _run(coordinator.request_snapshot("dongle-A", "4.3.1.1C6", force=True))
    assert published == ["dongle-A/snapshot/request"]
    assert len(timers) == 1 and timers[0][0] == 20.0
    assert "dongle-A" in coordinator._snapshot_retry


def test_snap_hold_disarms_the_retry(coordinator, monkeypatch):
    published, timers = _prep(coordinator, monkeypatch)

    _run(coordinator.request_snapshot("dongle-A", "4.3.1.1C6", force=True))
    coordinator._note_snapshot_delivered("dongle-A")

    assert coordinator._snapshot_retry == {}
    assert timers == []  # cancelled, so it can never re-request


def test_input_only_reply_does_not_disarm(coordinator, monkeypatch):
    """/snap/input carries no settings, so it must not count as delivery."""
    published, timers = _prep(coordinator, monkeypatch)

    _run(coordinator.request_snapshot("dongle-A", "4.3.1.1C6", force=True))
    # Only _note_snapshot_delivered() disarms, and the dispatcher calls it for
    # /snap/hold alone -- an input-only reply leaves the timer armed.
    assert "dongle-A" in coordinator._snapshot_retry


def test_unanswered_request_is_retried(coordinator, monkeypatch):
    published, timers = _prep(coordinator, monkeypatch)

    _run(coordinator.request_snapshot("dongle-A", "4.3.1.1C6", force=True))
    # Reply never arrives -> the timer fires.
    _fire(timers)

    assert published == ["dongle-A/snapshot/request"] * 2
    assert coordinator._snapshot_retry_attempts["dongle-A"] == 1


def test_retries_are_bounded(coordinator, monkeypatch):
    published, timers = _prep(coordinator, monkeypatch)

    _run(coordinator.request_snapshot("dongle-A", "4.3.1.1C6", force=True))
    for _ in range(10):
        if not timers:
            break
        _fire(timers)

    # Initial publish + at most _snapshot_max_retries retries, then it gives up.
    assert len(published) == 1 + 3
    assert coordinator._snapshot_retry == {}


def test_retry_suppressed_during_ota(coordinator, monkeypatch):
    """An OTA'ing dongle has no snapshot queue: a request reboot-loops it."""
    published, timers = _prep(coordinator, monkeypatch)

    _run(coordinator.request_snapshot("dongle-A", "4.3.1.1C6", force=True))
    coordinator.set_ota_in_progress("dongle-A", True)
    _fire(timers)

    assert published == ["dongle-A/snapshot/request"]  # no second request
