"""Dongle-less unique_id migration — Shape A of the _2 duplicate bug.

3.1.x registered TemperatureSensor/CalculatedSensor with a dongle-LESS uid
(`{entry}_tbat`); 4.0.x uses `{entry}_{dongle}_tbat`. The mismatch spawns a `_2`.
This migration removes the dongle-less orphan when the correct entity exists, or
renames it to the dongle-scoped form otherwise. Must work for ANY dongle count —
a duplicate is always wrong — resolving the owning dongle from the entity_id.
"""
import asyncio
import types

ENTRY_ID = "01kwmzdg0qc52m0kyqyzj8hwz6"
D0 = "dongle-40:4C:CA:4E:90:00"
D1 = "dongle-40:4C:CA:4E:90:01"


def _fmt(d):
    return d.lower().replace("-", "_").replace(":", "_")


class _RegEntry:
    def __init__(self, entity_id, unique_id):
        self.entity_id = entity_id
        self.unique_id = unique_id


class _FakeReg:
    def __init__(self, entries):
        self._by_id = {e.entity_id: e for e in entries}

    def async_entries(self):
        return list(self._by_id.values())

    def async_get(self, entity_id):
        return self._by_id.get(entity_id)

    def async_get_entity_id(self, domain, platform, unique_id):
        for e in self._by_id.values():
            if e.unique_id == unique_id and e.entity_id.startswith(f"{domain}."):
                return e.entity_id
        return None

    def async_remove(self, entity_id):
        self._by_id.pop(entity_id, None)

    def async_update_entity(self, entity_id, new_entity_id=None, new_unique_id=None):
        e = self._by_id.pop(entity_id)
        if new_entity_id:
            e.entity_id = new_entity_id
        if new_unique_id:
            e.unique_id = new_unique_id
        self._by_id[e.entity_id] = e
        return e


class _Entry:
    entry_id = ENTRY_ID


class _Coord:
    def __init__(self, dongles):
        self._dongle_ids = dongles

    def get_formatted_dongle_id(self, d):
        return _fmt(d)


def _patch(monkeypatch, reg):
    from custom_components.monitormysolar import migration
    fake_er = types.SimpleNamespace(
        async_get=lambda hass: reg,
        async_entries_for_config_entry=lambda r, entry_id: reg.async_entries(),
    )
    monkeypatch.setattr(migration, "er", fake_er)
    return migration


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_single_dongle_removes_orphan(monkeypatch):
    dev = _fmt(D0)
    reg = _FakeReg([
        _RegEntry(f"sensor.{dev}_tbat",   f"{ENTRY_ID}_{D0}_tbat".lower()),  # correct
        _RegEntry(f"sensor.{dev}_tbat_2", f"{ENTRY_ID}_tbat"),       # dongle-less orphan
    ])
    migration = _patch(monkeypatch, reg)
    n = _run(migration.async_migrate_dongleless_unique_ids(None, _Entry(), _Coord([D0])))
    assert n == 1
    ids = {e.entity_id for e in reg.async_entries()}
    assert ids == {f"sensor.{dev}_tbat"}  # orphan gone


def test_single_dongle_renames_lonely_dongleless(monkeypatch):
    # No correct entity exists yet — rename the dongle-less one up in place.
    dev = _fmt(D0)
    reg = _FakeReg([_RegEntry(f"sensor.{dev}_tbat", f"{ENTRY_ID}_tbat")])
    migration = _patch(monkeypatch, reg)
    n = _run(migration.async_migrate_dongleless_unique_ids(None, _Entry(), _Coord([D0])))
    assert n == 1
    e = reg.async_get(f"sensor.{dev}_tbat")
    assert e.unique_id == f"{ENTRY_ID}_{D0}_tbat".lower()


def test_multi_dongle_resolves_owner_from_entity_id(monkeypatch):
    # Two dongles; a dongle-less orphan on each dongle's entity_id. Each is
    # removed against its OWN dongle's correct entity — resolved via entity_id.
    dev0, dev1 = _fmt(D0), _fmt(D1)
    reg = _FakeReg([
        _RegEntry(f"sensor.{dev0}_tbat",   f"{ENTRY_ID}_{D0}_tbat".lower()),
        _RegEntry(f"sensor.{dev0}_tbat_2", f"{ENTRY_ID}_tbat"),      # orphan -> dongle 00
        _RegEntry(f"sensor.{dev1}_tbat",   f"{ENTRY_ID}_{D1}_tbat".lower()),
        _RegEntry(f"sensor.{dev1}_tbat_2", f"{ENTRY_ID}_tbat"),      # orphan -> dongle 01
    ])
    migration = _patch(monkeypatch, reg)
    n = _run(migration.async_migrate_dongleless_unique_ids(None, _Entry(), _Coord([D0, D1])))
    assert n == 2
    ids = {e.entity_id for e in reg.async_entries()}
    assert ids == {f"sensor.{dev0}_tbat", f"sensor.{dev1}_tbat"}  # both orphans gone


def test_combined_uid_skipped(monkeypatch):
    dev = _fmt(D0)
    reg = _FakeReg([_RegEntry(f"sensor.{dev}_combined_x", f"{ENTRY_ID}_combined_x")])
    migration = _patch(monkeypatch, reg)
    n = _run(migration.async_migrate_dongleless_unique_ids(None, _Entry(), _Coord([D0])))
    assert n == 0  # combined/aggregate uids are legitimately dongle-less
