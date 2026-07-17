"""Tests for the raw (un-prefixed) entity_id singleton guard.

Raw entity_ids (sensor.soc) can only be owned by ONE config entry: a second
entry computing the same ids gets _2-deduped by the registry and its entities
never receive data. The config flow must detect an existing raw owner and
force the dongle-id prefix on any later install.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock


def _hass_with_entries(entries):
    hass = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=entries)
    return hass


def _entry(entry_id="e1", **data):
    return SimpleNamespace(entry_id=entry_id, data=data)


def _import_guard():
    from custom_components.monitormysolar.config_flow import _raw_entity_ids_in_use
    return _raw_entity_ids_in_use


def test_no_entries_raw_free():
    guard = _import_guard()
    assert guard(_hass_with_entries([])) is False


def test_explicit_empty_prefix_counts_as_raw():
    guard = _import_guard()
    entries = [_entry(dongle_data=[{"dongle_id": "dongle-A", "entity_prefix": ""}])]
    assert guard(_hass_with_entries(entries)) is True


def test_explicit_prefix_not_raw():
    guard = _import_guard()
    entries = [_entry(dongle_data=[{"dongle_id": "dongle-A", "entity_prefix": "dongle-A"}])]
    assert guard(_hass_with_entries(entries)) is False


def test_legacy_entry_drop_flag_counts_as_raw():
    guard = _import_guard()
    # Legacy single-dongle entry: no entity_prefix key, drop_dongle_id set.
    entries = [_entry(
        dongle_data=[{"dongle_id": "dongle-A"}],
        drop_dongle_id=True,
    )]
    assert guard(_hass_with_entries(entries)) is True


def test_legacy_entry_without_drop_flag_not_raw():
    guard = _import_guard()
    entries = [_entry(dongle_data=[{"dongle_id": "dongle-A"}])]
    assert guard(_hass_with_entries(entries)) is False


def test_pre_dongle_data_entry_with_drop_flag_counts_as_raw():
    guard = _import_guard()
    entries = [_entry(drop_dongle_id=True)]
    assert guard(_hass_with_entries(entries)) is True


def test_exclude_entry_id_skips_own_entry():
    guard = _import_guard()
    entries = [_entry(
        entry_id="me",
        dongle_data=[{"dongle_id": "dongle-A", "entity_prefix": ""}],
    )]
    # The options flow excludes the entry being edited: its own raw ids
    # don't block it from keeping raw ids.
    assert guard(_hass_with_entries(entries), exclude_entry_id="me") is False
    assert guard(_hass_with_entries(entries), exclude_entry_id="other") is True
