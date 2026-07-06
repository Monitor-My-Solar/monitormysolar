"""Options-flow entity restore: list + restore of deleted/disabled entities.

When a user deletes an entity from the UI, HA remembers its unique_id in the
registry's deleted set and won't recreate it on reload. list_restorable_entities
surfaces both deleted and disabled entities for the config entry; async_restore_
entities clears the blocking records so the next setup recreates them.

These exercise the helpers against a fake entity registry (no HA runtime).
"""
import sys
import types
from unittest.mock import MagicMock


# --- Fake HA entity_registry ------------------------------------------------

class _RegEntry:
    def __init__(self, entity_id, config_entry_id, disabled_by=None, name=None):
        self.entity_id = entity_id
        self.config_entry_id = config_entry_id
        self.disabled_by = disabled_by
        self.name = name
        self.original_name = name


class _DeletedEntry:
    def __init__(self, config_entry_id, name=None):
        self.config_entry_id = config_entry_id
        self.name = name
        self.original_name = name


class _FakeRegistry:
    def __init__(self, entries, deleted):
        self._entries = {e.entity_id: e for e in entries}
        self.deleted_entities = deleted  # {entity_id: _DeletedEntry}
        self.saved = False

    def async_get(self, entity_id):
        return self._entries.get(entity_id)

    def async_update_entity(self, entity_id, **kw):
        e = self._entries[entity_id]
        for k, v in kw.items():
            setattr(e, k, v)
        return e

    def async_schedule_save(self):
        self.saved = True


def _install_er(monkeypatch, registry, entries_for_entry):
    """Patch migration.er with a fake module bound to `registry`."""
    from custom_components.monitormysolar import migration
    fake_er = types.SimpleNamespace(
        async_get=lambda hass: registry,
        async_entries_for_config_entry=lambda reg, entry_id: entries_for_entry,
    )
    monkeypatch.setattr(migration, "er", fake_er)
    return migration


class _Entry:
    entry_id = "cfg1"


def test_list_restorable_reports_disabled_and_deleted(monkeypatch):
    entries = [
        _RegEntry("sensor.a", "cfg1"),                       # active -> not listed
        _RegEntry("sensor.b", "cfg1", disabled_by="user", name="B"),  # disabled
        _RegEntry("sensor.other", "other"),                  # different entry
    ]
    deleted = {
        "sensor.gone": _DeletedEntry("cfg1", name="Gone"),   # deleted, this entry
        "sensor.gone_other": _DeletedEntry("other"),         # deleted, other entry
    }
    reg = _FakeRegistry(entries, deleted)
    migration = _install_er(monkeypatch, reg, [entries[0], entries[1]])

    items = migration.list_restorable_entities(MagicMock(), _Entry())
    keys = {i["key"] for i in items}
    assert keys == {"disabled:sensor.b", "deleted:sensor.gone"}
    states = {i["entity_id"]: i["state"] for i in items}
    assert states == {"sensor.b": "disabled", "sensor.gone": "deleted"}


def test_restore_reenables_disabled(monkeypatch):
    entries = [_RegEntry("sensor.b", "cfg1", disabled_by="user", name="B")]
    reg = _FakeRegistry(entries, {})
    migration = _install_er(monkeypatch, reg, entries)

    import asyncio
    n = asyncio.get_event_loop().run_until_complete(
        migration.async_restore_entities(MagicMock(), _Entry(), ["disabled:sensor.b"]))
    assert n == 1
    assert reg.async_get("sensor.b").disabled_by is None


def test_restore_purges_deleted(monkeypatch):
    deleted = {"sensor.gone": _DeletedEntry("cfg1", name="Gone")}
    reg = _FakeRegistry([], deleted)
    migration = _install_er(monkeypatch, reg, [])

    import asyncio
    n = asyncio.get_event_loop().run_until_complete(
        migration.async_restore_entities(MagicMock(), _Entry(), ["deleted:sensor.gone"]))
    assert n == 1
    assert "sensor.gone" not in reg.deleted_entities  # record cleared
    assert reg.saved is True                            # persisted


def test_restore_ignores_unknown_keys(monkeypatch):
    reg = _FakeRegistry([], {})
    migration = _install_er(monkeypatch, reg, [])
    import asyncio
    n = asyncio.get_event_loop().run_until_complete(
        migration.async_restore_entities(MagicMock(), _Entry(),
                                         ["deleted:sensor.nope", "bogus", "disabled:"]))
    assert n == 0
