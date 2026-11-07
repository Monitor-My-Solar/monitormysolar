"""OTA acknowledgement: progress on the OTA topics counts as the ACK.

The dongle ACKs on the admin response topic and reboots straight away, so that
reply can be missed; the install must not raise "did not acknowledge" while
progress is streaming. Exercises the inner callbacks of async_install by
driving the MQTT subscriptions with fakes.
"""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

update = pytest.importorskip("custom_components.monitormysolar.update")


class _Subs:
    """Captures the three subscriptions and lets a test publish into them."""

    def __init__(self):
        self.handlers = {}

    async def subscribe(self, hass, topic, handler):
        self.handlers[topic] = handler
        return lambda: None

    def publish(self, topic, payload, retain=False):
        self.handlers[topic](SimpleNamespace(payload=json.dumps(payload), retain=retain))


def _entity():
    e = update.DongleFirmwareUpdate.__new__(update.DongleFirmwareUpdate)
    e._dongle_id = "dongle-A"
    e._track = "prod"
    e._attr_in_progress = False
    e._attr_progress = None
    e.async_write_ha_state = MagicMock()
    e._refresh_firmware_version = AsyncMock()
    coord = MagicMock()
    coord.entry.data = {}
    coord.request_snapshot = AsyncMock()
    coord.current_fw_versions = {"dongle-A": "4.3.3.1S3"}
    e.coordinator = coord
    return e


def _run_install(monkeypatch, script):
    """Run async_install with `script(subs)` fired once the command is published."""
    subs = _Subs()
    published = []

    async def fake_publish(hass, topic, payload, **kw):
        published.append((topic, json.loads(payload)))
        script(subs)

    monkeypatch.setattr(update.mqtt, "async_subscribe", subs.subscribe)
    monkeypatch.setattr(update.mqtt, "async_publish", fake_publish)
    monkeypatch.setattr(update, "OTA_ACK_TIMEOUT", 0.2)
    monkeypatch.setattr(update, "OTA_OVERALL_TIMEOUT", 0.5)
    e = _entity()
    e.hass = SimpleNamespace(loop=None)

    async def go():
        e.hass.loop = asyncio.get_running_loop()
        await e.async_install(None, False)

    asyncio.run(go())
    return e, published


def test_progress_counts_as_ack_and_result_finishes(monkeypatch):
    def script(subs):
        # No reply on admin/response at all: only progress, then the result.
        subs.publish("dongle-A/ota/progress", {"progress": 35})
        subs.publish("dongle-A/ota/result", {"status": "success", "version": "4.3.3.2S3"})

    e, published = _run_install(monkeypatch, script)
    assert published[0][0] == "dongle-A/admin"
    assert published[0][1]["args"] == {"track": "prod"}
    e._refresh_firmware_version.assert_awaited()
    e.coordinator.set_ota_in_progress.assert_any_call("dongle-A", False)


def test_reply_without_id_is_accepted(monkeypatch):
    def script(subs):
        subs.publish("dongle-A/admin/response", {"cmd": "ota", "status": "ok", "detail": "queued"})
        subs.publish("dongle-A/ota/result", {"status": "success"})

    e, _ = _run_install(monkeypatch, script)
    e._refresh_firmware_version.assert_awaited()


def test_rejection_still_raises(monkeypatch):
    def script(subs):
        subs.publish(
            "dongle-A/admin/response",
            {"cmd": "ota", "status": "error", "detail": "busy"},
        )

    with pytest.raises(Exception, match="rejected"):
        _run_install(monkeypatch, script)


def test_silence_still_raises(monkeypatch):
    with pytest.raises(Exception, match="did not acknowledge"):
        _run_install(monkeypatch, lambda subs: None)
