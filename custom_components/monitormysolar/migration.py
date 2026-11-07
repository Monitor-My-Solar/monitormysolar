"""Entity-ID scheme migration for Monitor My Solar.

History (states + long-term statistics) is anchored to an entity's unique_id, which
this integration NEVER changes. Home Assistant (2023.4+) automatically migrates both
states history and statistics when an entity_id is renamed *through the entity
registry*. A code-only change of self.entity_id does NOT migrate — it orphans history.

So when the user toggles the drop_dongle_id flag (or reconnects an existing system),
we rename the affected entities via the registry here, before platforms are set up,
and HA carries the history across for us.
"""
from __future__ import annotations

import logging
import queue
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, LOGGER, CONF_DROP_DONGLE_ID

# ---------------------------------------------------------------------------
# Dedicated migration audit log — <config>/monitormysolar_migration.log
# ---------------------------------------------------------------------------
# A standalone, human-readable record of exactly what the migrations did to the
# entity registry each setup: what was renamed, removed, reclaimed. It survives
# HA's log rotation (its own rotating file) so a downgrade→upgrade run can be
# audited after the fact — which the main HA log couldn't give us.
_AUDIT_LOGGER_NAME = "monitormysolar.migration_audit"
_audit_logger: logging.Logger | None = None
_audit_listener: QueueListener | None = None  # keep a ref so it isn't GC'd


def _get_audit_logger(hass: HomeAssistant) -> logging.Logger:
    """Lazily build a file-backed audit logger in the HA config directory.

    audit() is called from the event loop, so no file I/O may happen there:
    the logger emits into a queue (non-blocking) and a QueueListener thread
    does the actual file writes. delay=True on the file handler defers even
    the open() to the first write — which runs on the listener thread.
    """
    global _audit_logger, _audit_listener
    if _audit_logger is not None:
        return _audit_logger

    logger = logging.getLogger(_AUDIT_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # don't spam the main HA log

    # Only attach the queue handler once.
    if not logger.handlers:
        try:
            path = hass.config.path("monitormysolar_migration.log")
            file_handler = RotatingFileHandler(
                path, maxBytes=1_000_000, backupCount=3, encoding="utf-8",
                delay=True,  # open on first write, on the listener thread
            )
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S")
            )
            log_queue: queue.SimpleQueue = queue.SimpleQueue()
            logger.addHandler(QueueHandler(log_queue))
            _audit_listener = QueueListener(log_queue, file_handler)
            _audit_listener.start()  # daemon thread; won't block HA shutdown
        except Exception as err:  # pragma: no cover - fs edge cases
            LOGGER.warning("Could not open migration audit log: %s", err)

    _audit_logger = logger
    return logger


def audit(hass: HomeAssistant, message: str) -> None:
    """Write one line to the migration audit log (and echo to the main log)."""
    try:
        _get_audit_logger(hass).info(message)
    except Exception:  # pragma: no cover
        pass
    LOGGER.info("[migration] %s", message)


def audit_session(hass: HomeAssistant, entry, coordinator, phase: str) -> None:
    """Write a session header so runs are easy to tell apart in the log."""
    dongles = ", ".join(getattr(coordinator, "_dongle_ids", []) or [])
    audit(
        hass,
        f"===== {phase} | entry={entry.entry_id} | dongles=[{dongles}] =====",
    )


def _desired_entity_id(entity_id: str, drop: bool, formatted_dongle_ids: list[str]) -> str | None:
    """Compute the entity_id this entity should have under the current scheme.

    Returns the new entity_id, or None if it already matches / can't be derived.
    Works purely on the string form so it is independent of which platform class
    produced it. entity_id looks like '<platform>.<formatted_dongle_id>_<type>' when
    the dongle id is present, or '<platform>.<type>' when dropped.
    """
    platform, _, object_id = entity_id.partition(".")
    if not object_id:
        return None

    # Find a dongle prefix currently embedded in the object_id (if any).
    present_prefix = None
    for fdid in formatted_dongle_ids:
        if object_id == fdid or object_id.startswith(f"{fdid}_"):
            present_prefix = fdid
            break

    if drop:
        # Want NO dongle prefix.
        if present_prefix is None:
            return None  # already prefix-free
        bare = object_id[len(present_prefix) + 1 :]  # strip 'prefix_'
        if not bare:
            return None
        return f"{platform}.{bare}"
    else:
        # Want the dongle prefix present.
        if present_prefix is not None:
            return None  # already prefixed
        # Single-dongle only path: re-add the one dongle prefix.
        if len(formatted_dongle_ids) != 1:
            return None
        return f"{platform}.{formatted_dongle_ids[0]}_{object_id}"


async def async_migrate_entity_ids(hass: HomeAssistant, entry, coordinator) -> None:
    """Rename registry entities to match the current drop_dongle_id scheme.

    Lookup is by config-entry, so this doubles as reinstall auto-detection: if the
    registry survived a reinstall, the user's existing entities are found and renamed
    in place (history preserved). If the registry was wiped, there is simply nothing
    to migrate and fresh entities are created under the active scheme.
    """
    # Multi-dongle installs never drop the dongle id, so there is nothing to migrate.
    if len(coordinator._dongle_ids) != 1:
        return

    drop = entry.data.get(CONF_DROP_DONGLE_ID, False)
    formatted_dongle_ids = [
        coordinator.get_formatted_dongle_id(d) for d in coordinator._dongle_ids
    ]

    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)

    migrated = 0
    for reg_entry in entries:
        desired = _desired_entity_id(reg_entry.entity_id, drop, formatted_dongle_ids)
        if not desired or desired == reg_entry.entity_id:
            continue

        # Collision guard: don't rename onto an entity_id already taken by something else.
        existing = ent_reg.async_get(desired)
        if existing is not None and existing.entity_id != reg_entry.entity_id:
            LOGGER.warning(
                "Skipping entity_id migration %s -> %s: target already in use by %s",
                reg_entry.entity_id,
                desired,
                existing.unique_id,
            )
            continue

        try:
            ent_reg.async_update_entity(reg_entry.entity_id, new_entity_id=desired)
            audit(hass, f"RENAME {reg_entry.entity_id} -> {desired} (uid {reg_entry.unique_id})")
        except ValueError as err:
            # HA raises if the target entity_id is already in use (registry or state
            # machine). Skip this one entity rather than aborting the whole migration.
            audit(hass, f"RENAME FAIL {reg_entry.entity_id} -> {desired}: {err}")
            continue
        migrated += 1

    if migrated:
        audit(hass, f"entity_id scheme migration: {migrated} change(s)")


async def async_transfer_dongle_entities(
    hass: HomeAssistant, entry, old_dongle_id: str, new_dongle_id: str
) -> int:
    """Transfer all entities (and their history) from one dongle to another.

    Used when a user replaces a physical dongle: the new dongle has a new MAC, so
    its entities would get brand-new unique_ids and the old dongle's history would
    be orphaned. Instead we rewrite the dongle segment of each existing entity's
    unique_id (and its entity_id prefix) from old -> new, in place. Because history
    is anchored to unique_id and we change it via the entity registry, HA carries
    states + statistics across to the new dongle automatically.

    Both dongles live in the same config entry, so the entry_id portion of the
    unique_id is identical and only the dongle segment changes — collision-free.

    Returns the number of entities transferred.
    """
    if not old_dongle_id or not new_dongle_id or old_dongle_id == new_dongle_id:
        return 0

    ent_reg = er.async_get(hass)

    # unique_id uses the raw dongle id, lowercased: '{entry_id}_{dongle_id}_{type}'.
    old_uid_seg = old_dongle_id.lower()
    new_uid_seg = new_dongle_id.lower()
    # entity_id uses the formatted dongle id: 'dongle_aa_bb_...'.
    old_eid_seg = old_dongle_id.lower().replace("-", "_").replace(":", "_")
    new_eid_seg = new_dongle_id.lower().replace("-", "_").replace(":", "_")

    transferred = 0
    for reg_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        uid = reg_entry.unique_id
        # Match the dongle segment bounded by underscores to avoid partial hits.
        token = f"_{old_uid_seg}_"
        if token not in uid:
            continue

        new_uid = uid.replace(token, f"_{new_uid_seg}_", 1)
        if new_uid == uid:
            continue

        # Guard: don't collide with an entity that already uses the new unique_id.
        existing_eid = ent_reg.async_get_entity_id(
            reg_entry.entity_id.split(".")[0], DOMAIN, new_uid
        )
        if existing_eid and existing_eid != reg_entry.entity_id:
            LOGGER.warning(
                "Skipping dongle transfer for %s: new unique_id %s already in use by %s",
                reg_entry.entity_id,
                new_uid,
                existing_eid,
            )
            continue

        # Also move the entity_id's dongle prefix so it reads as the new dongle.
        new_entity_id = reg_entry.entity_id
        platform, _, object_id = reg_entry.entity_id.partition(".")
        if object_id == old_eid_seg or object_id.startswith(f"{old_eid_seg}_"):
            new_object_id = object_id.replace(old_eid_seg, new_eid_seg, 1)
            candidate = f"{platform}.{new_object_id}"
            taken = ent_reg.async_get(candidate)
            if taken is None or taken.entity_id == reg_entry.entity_id:
                new_entity_id = candidate

        update_kwargs = {"new_unique_id": new_uid}
        if new_entity_id != reg_entry.entity_id:
            update_kwargs["new_entity_id"] = new_entity_id

        LOGGER.info(
            "Transferring entity %s -> unique_id %s, entity_id %s (history preserved)",
            reg_entry.entity_id,
            new_uid,
            new_entity_id,
        )
        try:
            ent_reg.async_update_entity(reg_entry.entity_id, **update_kwargs)
        except ValueError as err:
            LOGGER.warning(
                "Could not transfer %s to %s: %s", reg_entry.entity_id, new_dongle_id, err
            )
            continue
        transferred += 1

    if transferred:
        LOGGER.info(
            "Monitor My Solar: transferred %d entit(ies) from %s to %s",
            transferred,
            old_dongle_id,
            new_dongle_id,
        )
    return transferred


async def async_cleanup_orphan_devices(hass: HomeAssistant, entry) -> int:
    """Remove this entry's devices that no longer have any entities.

    Device-grouping sub-devices ("<dongle> - PV", "- Battery", …) are created
    implicitly by HA when an entity reports its device_info. When the user turns
    device grouping OFF, entities move back to the main dongle device and the
    sub-devices become empty — but HA does not delete them on its own, so they
    linger as stale devices. This prunes any device under this config entry that
    has zero entities left (which is exactly the emptied sub-devices), while never
    touching the main dongle device (it always keeps entities).

    Runs after platforms are set up, so the entity registry reflects the current
    grouping state. Returns the number of devices removed.
    """
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    devices = dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
    removed = 0
    for device in devices:
        entities = er.async_entries_for_device(
            ent_reg, device.id, include_disabled_entities=True
        )
        if entities:
            continue
        # No entities remain on this device — it's an orphaned (e.g. grouping-off)
        # sub-device. Detach it from this config entry; HA deletes the device once
        # it has no remaining config entries.
        audit(hass, f"REMOVE empty device {device.name!r} ({device.identifiers})")
        dev_reg.async_update_device(device.id, remove_config_entry_id=entry.entry_id)
        removed += 1

    if removed:
        audit(hass, f"orphan device cleanup: {removed} device(s) removed")
    return removed


async def async_migrate_dongleless_unique_ids(hass: HomeAssistant, entry, coordinator) -> int:
    """Fix per-dongle entities that were registered with a dongle-less unique_id.

    TemperatureSensor / CalculatedSensor (and historically others) used to build
    their registry unique_id as ``{entry_id}_{key}`` — WITHOUT the dongle id — while
    the same key created as a plain sensor used ``{entry_id}_{dongle}_{key}``. The
    two differing unique_ids made HA create a second entity (``_2``) and orphan the
    first. Now that every per-dongle class uses the dongle-scoped form, rewrite any
    surviving dongle-less unique_id to the dongle-scoped one via the registry so the
    existing entity is REUSED (history kept) and its clean entity_id is reclaimed —
    instead of a fresh duplicate appearing on the next start.

    Works for any dongle count. A single dongle in a GridBoss/FlexBoss combo is no
    different from a standalone one — a duplicate is always wrong. When there are
    several dongles, a bare uid `{entry}_tbat` is ambiguous on its own, so we
    resolve the owning dongle from the orphan's ENTITY_ID (which always names its
    dongle, e.g. sensor.dongle_40_4c_.._tbat_2). Combined/aggregate uids are the
    only ones legitimately dongle-less and are skipped.
    """
    if not coordinator._dongle_ids:
        return 0

    ent_reg = er.async_get(hass)
    prefix = f"{entry.entry_id}_".lower()

    # Map each dongle to (uid-segment, formatted entity_id fragment) so we can
    # identify which dongle a dongle-less orphan belongs to FROM ITS ENTITY_ID.
    # This is what makes multi-dongle safe: a bare uid `{entry}_tbat` is
    # ambiguous, but the entity_id `sensor.dongle_40_4c_..._tbat_2` names its
    # dongle. formatted id: dongle-40:4C:.. -> dongle_40_4c_.. (entity_id form).
    dongle_info = []
    for d in coordinator._dongle_ids:
        seg = f"{entry.entry_id}_{d}_".lower()
        formatted = coordinator.get_formatted_dongle_id(d).lower()  # dongle_40_4c_..
        dongle_info.append((d, seg, formatted))
    dongle_segs = tuple(seg for _d, seg, _f in dongle_info)

    def _resolve_dongle_seg(entity_id: str):
        """Find the dongle segment whose formatted id appears in this entity_id."""
        eid = entity_id.split(".", 1)[-1].lower()
        for _d, seg, formatted in dongle_info:
            if formatted and formatted in eid:
                return seg
        # Single-dongle fallback: unambiguous.
        if len(dongle_info) == 1:
            return dongle_info[0][1]
        return None

    audit_session(hass, entry, coordinator, "dongle-less unique_id migration")
    migrated = 0
    for reg_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        uid = reg_entry.unique_id or ""
        uid_l = uid.lower()  # uids are stored with the dongle MAC in UPPERCASE
        # Skip if already dongle-scoped, or not one of our prefixed uids.
        # ALL comparisons are lowercased — prefix/dongle_segs are lowercase but
        # the uid contains an uppercase MAC, so a raw startswith would wrongly
        # treat a correct entity as dongle-less and double-prefix it.
        if not uid_l.startswith(prefix) or any(uid_l.startswith(s) for s in dongle_segs):
            continue
        # Skip combined/aggregate uids (they legitimately have no single dongle).
        key = uid_l[len(prefix):]
        if key.startswith("combined") or key == "sync_status":
            continue

        dongle_seg = _resolve_dongle_seg(reg_entry.entity_id)
        if dongle_seg is None:
            audit(hass, f"SKIP {reg_entry.entity_id} (uid {uid}): cannot resolve dongle")
            continue

        new_uid = f"{dongle_seg}{key}"
        # Don't collide with an already-correct entity.
        existing = ent_reg.async_get_entity_id(
            reg_entry.entity_id.split(".")[0], DOMAIN, new_uid
        )
        if existing and existing != reg_entry.entity_id:
            # The correct entity already exists; this dongle-less one is a true
            # orphan/duplicate — remove it so it stops shadowing the clean id.
            audit(
                hass,
                f"REMOVE orphan {reg_entry.entity_id} (uid {uid}); "
                f"{existing} already holds uid {new_uid}",
            )
            ent_reg.async_remove(reg_entry.entity_id)
            migrated += 1
            continue

        try:
            ent_reg.async_update_entity(reg_entry.entity_id, new_unique_id=new_uid)
            audit(hass, f"UID {reg_entry.entity_id}: {uid} -> {new_uid}")
        except ValueError as err:
            audit(hass, f"UID FAIL {reg_entry.entity_id}: {uid} -> {new_uid}: {err}")
            continue
        migrated += 1

    audit(hass, f"dongle-less unique_id migration: {migrated} change(s)")
    return migrated


import re as _re

_SUFFIX_RE = _re.compile(r"^(?P<base>.+)_(?P<n>\d+)$")


async def async_reclaim_suffixed_entity_ids(hass: HomeAssistant, entry, coordinator) -> int:
    """Reclaim clean entity_ids for correctly-registered entities stuck on `_N`.

    The `_2` duplicate has two shapes after a downgrade→upgrade:

      Shape A — the `_N` entity is the OLD dongle-less orphan; the clean id holds
        the correct dongle-scoped entity. async_migrate_dongleless_unique_ids
        already removes those orphans (freeing nothing to rename).

      Shape B — the CORRECT (dongle-scoped uid) entity itself got saddled with a
        `_2` entity_id because the slot was taken when it was first created, and
        the base id later became free (its old orphan was removed). Nothing
        rewrites it back down, so the live entity is stuck as `sensor.._t5_2`.

    This pass fixes Shape B: for every entity whose entity_id ends in `_<n>` and
    whose unique_id is the current dongle-scoped form, if the base entity_id is
    free (or held only by a removable dongle-less orphan), rename the entity down
    to the clean id. History is preserved (anchored to the unchanged unique_id).

    Runs BEFORE platforms are set up so the reclaimed ids exist before creation.
    Dongle-count-agnostic — a duplicate is always wrong whether the box has one
    dongle or a GridBoss/FlexBoss combo. Every entity carries its own dongle in
    the unique_id, so we never guess which dongle a stuck id belongs to. Returns
    count renamed.
    """
    if not coordinator._dongle_ids:
        return 0

    ent_reg = er.async_get(hass)
    entry_prefix = f"{entry.entry_id}_".lower()
    # A uid is "correct/dongle-scoped" if it starts with {entry}_{any-dongle}_.
    dongle_segs = tuple(
        f"{entry.entry_id}_{d}_".lower() for d in coordinator._dongle_ids
    )

    def _is_dongle_scoped(uid: str) -> bool:
        return any(uid.startswith(seg) for seg in dongle_segs)

    audit_session(hass, entry, coordinator, "reclaim suffixed entity_ids")

    # Snapshot entries up front — we mutate the registry while iterating.
    entries = list(er.async_entries_for_config_entry(ent_reg, entry.entry_id))
    by_entity_id = {e.entity_id: e for e in entries}

    reclaimed = 0
    for reg_entry in entries:
        m = _SUFFIX_RE.match(reg_entry.entity_id)
        if not m:
            continue
        # Only reclaim for entities that ALREADY hold a correct dongle-scoped
        # uid — i.e. this is the live entity, just on the wrong id. Leave anything
        # else (a genuine dongle-less orphan) to the uid migration.
        if not _is_dongle_scoped((reg_entry.unique_id or "").lower()):
            continue

        base_id = m.group("base")
        occupant = by_entity_id.get(base_id) or ent_reg.async_get(base_id)

        if occupant is not None and occupant.entity_id != reg_entry.entity_id:
            # Base id is taken. Only safe to reclaim if the occupant is a stale
            # dongle-less orphan for the SAME key; remove it, then take the id.
            occ_uid = (occupant.unique_id or "").lower()
            is_dongleless_orphan = (
                occ_uid.startswith(entry_prefix)
                and not _is_dongle_scoped(occ_uid)
            )
            if not is_dongleless_orphan:
                LOGGER.debug(
                    "Not reclaiming %s -> %s: base id held by %s (uid %s)",
                    reg_entry.entity_id, base_id, occupant.entity_id, occupant.unique_id,
                )
                continue
            audit(
                hass,
                f"REMOVE orphan {occupant.entity_id} (uid {occupant.unique_id}) "
                f"to free {base_id}",
            )
            ent_reg.async_remove(occupant.entity_id)
            by_entity_id.pop(occupant.entity_id, None)

        # Base id is now free — rename the correct entity down onto it.
        try:
            ent_reg.async_update_entity(reg_entry.entity_id, new_entity_id=base_id)
            audit(
                hass,
                f"RECLAIM {reg_entry.entity_id} -> {base_id} (uid {reg_entry.unique_id})",
            )
            by_entity_id.pop(reg_entry.entity_id, None)
            by_entity_id[base_id] = reg_entry
            reclaimed += 1
        except ValueError as err:
            audit(hass, f"RECLAIM FAIL {reg_entry.entity_id} -> {base_id}: {err}")

    audit(hass, f"reclaim suffixed entity_ids: {reclaimed} change(s)")
    return reclaimed


def list_restorable_entities(hass: HomeAssistant, entry) -> list[dict]:
    """List this entry's entities that a plain reload won't bring back.

    Two blocked states:
      - DISABLED: the registry entry still exists but disabled_by is set. HA
        won't create the state until it's re-enabled.
      - DELETED: the user removed the entity from the UI. HA keeps the unique_id
        in the registry's deleted set (for a grace period) and refuses to
        re-add it on setup — a reload/reboot will NOT restore it. Clearing that
        record frees the unique_id so the next setup recreates the entity.

    Returns a list of {"key", "entity_id", "name", "state"} where `key` encodes
    how to restore it: "disabled:<entity_id>" or "deleted:<entity_id>".
    """
    ent_reg = er.async_get(hass)
    items: list[dict] = []

    # Disabled (but still-registered) entities for this config entry.
    for reg_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if reg_entry.disabled_by is not None:
            items.append({
                "key": f"disabled:{reg_entry.entity_id}",
                "entity_id": reg_entry.entity_id,
                "name": reg_entry.name or reg_entry.original_name or reg_entry.entity_id,
                "state": "disabled",
            })

    # Deleted entities live in a separate registry structure keyed by entity_id.
    # Filter to this config entry. The attribute name has been stable across HA
    # versions, but guard so a rename can't crash the options flow.
    deleted = getattr(ent_reg, "deleted_entities", {}) or {}
    for entity_id, del_entry in deleted.items():
        if getattr(del_entry, "config_entry_id", None) != entry.entry_id:
            continue
        items.append({
            "key": f"deleted:{entity_id}",
            "entity_id": entity_id,
            "name": getattr(del_entry, "name", None)
                    or getattr(del_entry, "original_name", None)
                    or entity_id,
            "state": "deleted",
        })

    items.sort(key=lambda i: i["entity_id"])
    return items


async def async_restore_entities(hass: HomeAssistant, entry, keys: list[str]) -> int:
    """Restore the entities identified by keys from list_restorable_entities().

    - "disabled:<entity_id>" -> clear disabled_by so HA activates it.
    - "deleted:<entity_id>"  -> drop the deleted-registry record so the
      unique_id is free; the next platform setup recreates the entity fresh
      from the catalog. Caller should reload the config entry afterwards.

    Returns the number of entities actioned.
    """
    ent_reg = er.async_get(hass)
    restored = 0

    for key in keys:
        kind, _, entity_id = key.partition(":")
        if not entity_id:
            continue
        if kind == "disabled":
            reg_entry = ent_reg.async_get(entity_id)
            if reg_entry and reg_entry.disabled_by is not None:
                ent_reg.async_update_entity(entity_id, disabled_by=None)
                LOGGER.info("Restored (re-enabled) entity %s", entity_id)
                restored += 1
        elif kind == "deleted":
            # Purge the deleted record so the unique_id is reclaimable. Prefer a
            # public API if present; fall back to popping the internal dict.
            purged = False
            remover = getattr(ent_reg, "async_purge_deleted_entity", None)
            if callable(remover):
                try:
                    remover(entity_id)
                    purged = True
                except Exception as err:  # pragma: no cover - version drift
                    LOGGER.debug("purge API failed for %s: %s", entity_id, err)
            if not purged:
                deleted = getattr(ent_reg, "deleted_entities", None)
                if isinstance(deleted, dict) and entity_id in deleted:
                    deleted.pop(entity_id, None)
                    # Persist the registry change.
                    if hasattr(ent_reg, "async_schedule_save"):
                        ent_reg.async_schedule_save()
                    purged = True
            if purged:
                LOGGER.info(
                    "Cleared deleted record for %s — will be recreated on reload",
                    entity_id,
                )
                restored += 1

    if restored:
        LOGGER.info("Monitor My Solar: restored %d entity(ies)", restored)
    return restored
