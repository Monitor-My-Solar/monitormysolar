"""Pytest fixtures for monitormysolar tests.

These tests avoid the full Home Assistant test framework — we exercise the
coordinator's payload-processing logic in isolation with lightweight mocks.
The goal is regression protection on the per-bank → unified-topic transition
without dragging in `homeassistant`.
"""
from __future__ import annotations

import json
import logging
import sys
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


# Path setup so we can import custom_components.monitormysolar.* directly
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _make_stub_module(name: str, attrs: dict[str, Any] | None = None) -> types.ModuleType:
    """Create a stub module with the given attributes and register it in sys.modules."""
    mod = types.ModuleType(name)
    for k, v in (attrs or {}).items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


# Stub Home Assistant modules just enough for coordinator.py to import.
# The tests don't actually call HA-level functions; they exercise
# process_message() directly with crafted payloads.
@pytest.fixture(scope="session", autouse=True)
def _stub_homeassistant_modules():
    """Insert minimal HA stubs into sys.modules before coordinator import."""
    if "homeassistant" in sys.modules:
        return

    ha = _make_stub_module("homeassistant")
    _make_stub_module("homeassistant.core", {
        "HomeAssistant": MagicMock,
        "callback": lambda f: f,
    })
    _make_stub_module("homeassistant.config_entries", {
        "ConfigEntry": MagicMock,
    })
    _make_stub_module("homeassistant.helpers")
    _make_stub_module("homeassistant.helpers.update_coordinator", {
        "DataUpdateCoordinator": MagicMock,
    })
    _make_stub_module("homeassistant.helpers.event", {
        "async_call_later": MagicMock,
    })
    _make_stub_module("homeassistant.helpers.dispatcher", {
        "async_dispatcher_send": MagicMock,
    })
    _make_stub_module("homeassistant.components")
    _make_stub_module("homeassistant.components.mqtt", {
        "async_subscribe": MagicMock(),
        "async_publish": MagicMock(),
    })
    _make_stub_module("homeassistant.const", {
        "STATE_OFF": "off",
        "STATE_ON": "on",
    })
    _make_stub_module("homeassistant.util")


@pytest.fixture
def coordinator():
    """Return a minimally-initialised coordinator instance.

    We don't run __init__ in full — we just need an object whose
    process_message logic can be exercised. Most attributes are mocked or
    seeded with empty dicts/sets.
    """
    # Import inside the fixture so the HA stubs are in place first.
    from custom_components.monitormysolar.coordinator import MonitorMySolar

    # Bypass __init__ by allocating directly.
    coord = MonitorMySolar.__new__(MonitorMySolar)
    coord.hass = MagicMock()
    coord.hass.bus.async_fire = MagicMock()
    coord.entities = {}
    coord._last_fault_warning_data = {}
    coord._ignored_entity_suffixes = set()
    coord._firmware_codes = {}    # is_gridboss_dongle reads this
    coord.current_fw_versions = {}
    coord.current_ui_versions = {}
    # inverter_brand is a property that reads from entry.data — mock it.
    entry = MagicMock()
    entry.data = {"inverter_brand": "lux"}
    coord.entry = entry
    coord._dongle_ids = ["dongle-test"]
    coord._dongle_data = []
    coord._mqtt_unsubscribe_callbacks = {}
    coord.data = {}
    coord.async_set_updated_data = MagicMock()
    # Default to non-GridBoss for the standard fixture; the gridboss
    # fixture overrides this with its own MagicMock.
    coord.is_gridboss_dongle = MagicMock(return_value=False)
    return coord


@pytest.fixture
def gridboss_coordinator(coordinator):
    """Coordinator pre-configured as a GridBoss instance."""
    coordinator.entry.data = {"inverter_brand": "eg4_gridboss"}
    # Force is_gridboss_dongle to return True for our test dongle.
    coordinator.is_gridboss_dongle = MagicMock(return_value=True)
    return coordinator
