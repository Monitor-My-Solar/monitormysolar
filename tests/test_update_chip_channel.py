"""The firmware update entity must check the update channel for the dongle's own
chip. The bare /version endpoint is the ESP32-C6 channel, so an ESP32-S3 dongle
checked against it was offered the C6 build and never saw its own."""
import asyncio

import pytest

from custom_components.monitormysolar.const import dongle_chip_key


@pytest.mark.parametrize("chip_type,version,expected", [
    ("ESP32-S3", None, "s3"),
    ("esp32s3", None, "s3"),
    ("ESP32-C6", None, "c6"),
    (None, "4.5.0.87S3", "s3"),
    (None, "4.3.3.2C6", "c6"),
    ("", "4.3.3.2C6", "c6"),
    (None, "4.2.0", "c6"),      # pre-chip-suffix firmware is C6
    (None, None, "c6"),         # legacy units never report a chip
    ("ESP32-C6", "4.5.0.87S3", "c6"),  # /status wins over the version suffix
])
def test_dongle_chip_key(chip_type, version, expected):
    assert dongle_chip_key(chip_type, version) == expected


def test_status_records_chip_and_version(coordinator, monkeypatch):
    from unittest.mock import AsyncMock, MagicMock

    coordinator.current_fw_versions = {}
    coordinator.dongle_chip_types = {}
    coordinator._dongle_boot_count = {}
    coordinator._dongle_availability = {}
    coordinator.entities = {}
    coordinator.hass = MagicMock()
    monkeypatch.setattr(coordinator, "request_snapshot", AsyncMock())
    monkeypatch.setattr(coordinator, "request_recovery_snapshot", AsyncMock())
    monkeypatch.setattr(coordinator, "async_set_updated_data", MagicMock())
    asyncio.run(coordinator.process_status_message(
        "dongle-A",
        '{"Serialnumber": "SN1", "payload": {"version": "4.5.0.87S3", "chipType": "ESP32-S3", "boot": {"count": 3}}}',
    ))
    assert coordinator.dongle_chip_types["dongle-A"] == "ESP32-S3"
    assert coordinator.dongle_chip("dongle-A") == "s3"

    asyncio.run(coordinator.process_status_message(
        "dongle-B", '{"version": "4.3.3.2C6", "boot": {"count": 1}}'  # legacy flat format
    ))
    assert "dongle-B" not in coordinator.dongle_chip_types
    assert coordinator.dongle_chip("dongle-B") == "c6"
    assert coordinator.dongle_chip("dongle-never-seen") == "c6"


def test_pick_status_chip_type_spellings(coordinator):
    pick = coordinator._pick_status_chip_type
    assert pick({"chipType": "ESP32-S3"}) == "ESP32-S3"
    assert pick({"chip_type": "ESP32-C6"}) == "ESP32-C6"
    assert pick({"system": {"chip_type": "ESP32-S3"}}) == "ESP32-S3"
    assert pick({"version": "4.3.0"}) == ""
