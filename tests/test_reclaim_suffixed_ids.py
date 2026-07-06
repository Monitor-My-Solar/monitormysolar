"""Reclaim clean entity_ids for correct entities stuck on `_2` (Shape B).

After a downgrade (3.1.x, dongle-less unique_ids) -> upgrade (4.0.x, dongle-scoped
unique_ids), some correct entities end up on a `sensor.._t5_2` entity_id because
the base id was taken when they were created. async_reclaim_suffixed_entity_ids
renames the live dongle-scoped entity back down to the clean id, removing a stale
dongle-less orphan first if one is squatting the base id.

Fake entity registry — no HA runtime.
"""
import asyncio
import types


ENTRY_ID = "01kwmzdg0qc52m0kyqyzj8hwz6"
DONGLE = "dongle-40:4c:ca:4e:90:00"


class _RegEntry:
    def __init__(self, entity_id, unique_id):
        self.entity_id = entity_id
        self.unique_id = unique_id


class _FakeReg:
    def __init__(self, entries):
        self._by_id = {e.entity_id: e for e in entries}

    def async_get(self, entity_id):
        return self._by_id.get(entity_id)

    def async_remove(self, entity_id):
        self._by_id.pop(entity_id, None)

    def async_update_entity(self, entity_id, new_entity_id=None, new_unique_id=None):
        e = self._by_id.pop(entity_id)
        if new_entity_id:
            if new_entity_id in self._by_id:
                raise ValueError(f"{new_entity_id} already registered")
            e.entity_id = new_entity_id
        if new_unique_id:
            e.unique_id = new_unique_id
        self._by_id[e.entity_id] = e
        return e

    def entries(self):
        return list(self._by_id.values())


class _Entry:
    entry_id = ENTRY_ID


class _Coord:
    def __init__(self):
        self._dongle_ids = [DONGLE]


def _patch(monkeypatch, reg):
    from custom_components.monitormysolar import migration
    fake_er = types.SimpleNamespace(
        async_get=lambda hass: reg,
        async_entries_for_config_entry=lambda r, entry_id: reg.entries(),
    )
    monkeypatch.setattr(migration, "er", fake_er)
    return migration


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_shape_b_base_free_renames_down(monkeypatch):
    # t5: only the `_2` entity exists, holding the correct dongle-scoped uid;
    # base sensor.dongle_..._t5 is FREE. Should rename down.
    reg = _FakeReg([
        _RegEntry(f"sensor.{DONGLE.replace(':','_').replace('-','_')}_t5_2",
                  f"{ENTRY_ID}_{DONGLE}_t5"),
    ])
    migration = _patch(monkeypatch, reg)
    n = _run(migration.async_reclaim_suffixed_entity_ids(None, _Entry(), _Coord()))
    assert n == 1
    ids = {e.entity_id for e in reg.entries()}
    base = f"sensor.{DONGLE.replace(':','_').replace('-','_')}_t5"
    assert base in ids
    assert f"{base}_2" not in ids


def test_shape_b_orphan_squatting_base_is_removed_then_reclaimed(monkeypatch):
    # base id held by a dongle-less orphan; `_2` holds the correct uid.
    dev = DONGLE.replace(':','_').replace('-','_')
    reg = _FakeReg([
        _RegEntry(f"sensor.{dev}_t5",   f"{ENTRY_ID}_t5"),            # dongle-less orphan
        _RegEntry(f"sensor.{dev}_t5_2", f"{ENTRY_ID}_{DONGLE}_t5"),   # correct, stuck on _2
    ])
    migration = _patch(monkeypatch, reg)
    n = _run(migration.async_reclaim_suffixed_entity_ids(None, _Entry(), _Coord()))
    assert n == 1
    remaining = {e.entity_id: e.unique_id for e in reg.entries()}
    assert remaining == {f"sensor.{dev}_t5": f"{ENTRY_ID}_{DONGLE}_t5"}  # only the correct one, clean id


def test_does_not_touch_correct_orphan_left_for_uid_migration(monkeypatch):
    # A `_2` entity that holds a DONGLE-LESS uid is NOT reclaimed here (that's
    # the uid-migration's job); leave it alone.
    dev = DONGLE.replace(':','_').replace('-','_')
    reg = _FakeReg([
        _RegEntry(f"sensor.{dev}_tbat",   f"{ENTRY_ID}_{DONGLE}_tbat"),  # correct, clean
        _RegEntry(f"sensor.{dev}_tbat_2", f"{ENTRY_ID}_tbat"),           # dongle-less orphan on _2
    ])
    migration = _patch(monkeypatch, reg)
    n = _run(migration.async_reclaim_suffixed_entity_ids(None, _Entry(), _Coord()))
    assert n == 0  # untouched
    ids = {e.entity_id for e in reg.entries()}
    assert f"sensor.{dev}_tbat_2" in ids  # still there for uid migration to remove


def test_base_held_by_another_correct_entity_is_not_clobbered(monkeypatch):
    # If the base id is held by a DIFFERENT correct (dongle-scoped) entity, do
    # not remove or overwrite it.
    dev = DONGLE.replace(':','_').replace('-','_')
    reg = _FakeReg([
        _RegEntry(f"sensor.{dev}_t5",   f"{ENTRY_ID}_{DONGLE}_t5"),      # legit occupant
        _RegEntry(f"sensor.{dev}_t5_2", f"{ENTRY_ID}_{DONGLE}_t5other"), # different key, on _2
    ])
    migration = _patch(monkeypatch, reg)
    n = _run(migration.async_reclaim_suffixed_entity_ids(None, _Entry(), _Coord()))
    assert n == 0
    ids = {e.entity_id for e in reg.entries()}
    assert f"sensor.{dev}_t5" in ids and f"sensor.{dev}_t5_2" in ids


def test_multi_dongle_still_reclaims(monkeypatch):
    # A duplicate is always wrong — a dongle in a GB/FB combo is no different
    # from a standalone one. Multi-dongle must NOT be skipped.
    dev = DONGLE.replace(':','_').replace('-','_')
    reg = _FakeReg([
        _RegEntry(f"sensor.{dev}_t5_2", f"{ENTRY_ID}_{DONGLE}_t5"),  # dongle 00, stuck on _2
    ])
    migration = _patch(monkeypatch, reg)
    coord = _Coord(); coord._dongle_ids = [DONGLE, "dongle-aa:bb:cc:dd:ee:ff"]
    n = _run(migration.async_reclaim_suffixed_entity_ids(None, _Entry(), coord))
    assert n == 1
    ids = {e.entity_id for e in reg.entries()}
    assert f"sensor.{dev}_t5" in ids and f"sensor.{dev}_t5_2" not in ids


def test_multi_dongle_only_reclaims_matching_dongle(monkeypatch):
    # Two dongles, each with a stuck _2 — both reclaimed to their own base id.
    dev0 = DONGLE.replace(':','_').replace('-','_')
    d1 = "dongle-aa:bb:cc:dd:ee:ff"; dev1 = d1.replace(':','_').replace('-','_')
    reg = _FakeReg([
        _RegEntry(f"sensor.{dev0}_t5_2", f"{ENTRY_ID}_{DONGLE}_t5"),
        _RegEntry(f"sensor.{dev1}_t5_2", f"{ENTRY_ID}_{d1}_t5"),
    ])
    migration = _patch(monkeypatch, reg)
    coord = _Coord(); coord._dongle_ids = [DONGLE, d1]
    n = _run(migration.async_reclaim_suffixed_entity_ids(None, _Entry(), coord))
    assert n == 2
    ids = {e.entity_id for e in reg.entries()}
    assert ids == {f"sensor.{dev0}_t5", f"sensor.{dev1}_t5"}
