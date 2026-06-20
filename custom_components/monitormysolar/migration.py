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

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, LOGGER, CONF_DROP_DONGLE_ID


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

        LOGGER.info(
            "Migrating entity_id %s -> %s (history preserved via unique_id %s)",
            reg_entry.entity_id,
            desired,
            reg_entry.unique_id,
        )
        try:
            ent_reg.async_update_entity(reg_entry.entity_id, new_entity_id=desired)
        except ValueError as err:
            # HA raises if the target entity_id is already in use (registry or state
            # machine). Skip this one entity rather than aborting the whole migration.
            LOGGER.warning(
                "Could not migrate %s -> %s: %s", reg_entry.entity_id, desired, err
            )
            continue
        migrated += 1

    if migrated:
        LOGGER.info("Monitor My Solar: migrated %d entity_id(s) to new naming scheme", migrated)
