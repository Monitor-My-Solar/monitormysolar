from homeassistant.core import HomeAssistant
import asyncio
from homeassistant.components import mqtt
from homeassistant.helpers import service
from .const import LOGGER, PLATFORMS
from .coordinator import MonitorMySolar, MonitorMySolarEntry
from .migration import (
    async_migrate_entity_ids,
    async_cleanup_orphan_devices,
    async_migrate_dongleless_unique_ids,
    async_reclaim_suffixed_entity_ids,
    audit,
)

async def async_setup_entry(hass: HomeAssistant, entry: MonitorMySolarEntry):
    """Set up Monitor My Solar from a config entry."""
    inverter_brand = entry.data.get('inverter_brand')
    dongle_ids = entry.data.get('dongle_ids', [entry.data.get('dongle_id')])
    
    LOGGER.info(f"Setting up Monitor My Solar for {inverter_brand} with {len(dongle_ids)} dongles")
    audit(hass, f"########## SETUP START v4.0.0 | brand={inverter_brand} | dongles={dongle_ids} ##########")

    # Step 1: Initialize the coordinator with minimal setup
    coordinator = MonitorMySolar(hass, entry)
    entry.runtime_data = coordinator
    
    # Step 2: Request firmware codes for all dongles and wait for them
    # Initialize the coordinator but don't wait for data refresh
    try:
        await coordinator.async_setup()
    except Exception as e:
        error_msg = f"Error during coordinator setup: {e}"
        LOGGER.error(error_msg)
        coordinator._setup_errors.append(error_msg)
    
    # Wait for all firmware codes to be received (or timeout)
    LOGGER.debug("Waiting for firmware codes to be received for all dongles...")
    try:
        # Wait up to 20 seconds for firmware codes
        for attempt in range(20):
            if not coordinator._pending_dongles:
                LOGGER.debug("All firmware codes received successfully")
                break
            
            # If we're halfway through the timeout and still have pending dongles, try requesting again
            if attempt == 10 and coordinator._pending_dongles:
                error_msg = f"Still waiting for firmware codes from: {coordinator._pending_dongles}, sending request again"
                LOGGER.debug(error_msg)
                # Try requesting firmware codes again for the pending dongles
                for dongle_id in coordinator._pending_dongles:
                    try:
                        await mqtt.async_publish(
                            hass, f"{dongle_id}/firmwarecode/request", ""
                        )
                        LOGGER.debug(f"Resent firmware code request to {dongle_id}/firmwarecode/request")
                    except Exception as e:
                        error_msg = f"Error sending firmware request to {dongle_id}: {e}"
                        LOGGER.error(error_msg)
                        coordinator._setup_errors.append(error_msg)
            
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # Handle if the setup is cancelled
        error_msg = "Setup was cancelled while waiting for firmware codes"
        LOGGER.warning(error_msg)
        coordinator._setup_errors.append(error_msg)
        return False
    
    # Log status of firmware code reception
    if coordinator._pending_dongles:
        error_msg = f"Missing firmware codes from: {coordinator._pending_dongles}"
        LOGGER.warning(f"Proceeding with setup despite {error_msg}")
        coordinator._setup_errors.append(error_msg)
    else:
        LOGGER.debug("Successfully received firmware codes from all dongles")
    
    # Step 3: Register platform entity services using the new October 2025 API
    # Note: Service registration temporarily disabled due to API compatibility issues
    # TODO: Re-enable when Home Assistant service registration API is clarified
    LOGGER.debug("Skipping platform entity service registration - API compatibility issue")
    
    # Step 3.5: Migrate existing entity_ids to the current naming scheme BEFORE
    # platforms are set up. This renames via the entity registry so HA carries the
    # user's states + statistics history across (history is anchored to unique_id).
    try:
        await async_migrate_entity_ids(hass, entry, coordinator)
    except Exception as e:
        error_msg = f"Error migrating entity ids: {e}"
        LOGGER.error(error_msg)
        coordinator._setup_errors.append(error_msg)

    # Step 3.6: Fix any per-dongle entities that were registered with a dongle-less
    # unique_id (the cause of the _2 duplicates). Rewrites them to the dongle-scoped
    # form via the registry — reusing the existing entity (history kept, clean
    # entity_id reclaimed) — BEFORE platforms recreate entities.
    try:
        await async_migrate_dongleless_unique_ids(hass, entry, coordinator)
    except Exception as e:
        error_msg = f"Error migrating dongle-less unique ids: {e}"
        LOGGER.error(error_msg)
        coordinator._setup_errors.append(error_msg)

    # Step 3.7: Reclaim clean entity_ids for correct entities left stuck on `_2`
    # (Shape B of the duplicate bug — the live dongle-scoped entity got a `_2`
    # id because the slot was taken at creation, and the base id is now free).
    # Runs AFTER the dongle-less removal above so freed base ids are available,
    # and BEFORE platforms so the reclaimed ids exist before entity creation.
    try:
        await async_reclaim_suffixed_entity_ids(hass, entry, coordinator)
    except Exception as e:
        error_msg = f"Error reclaiming suffixed entity ids: {e}"
        LOGGER.error(error_msg)
        coordinator._setup_errors.append(error_msg)

    # Step 4: Now that we have tried to get firmware codes, set up the platforms
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception as e:
        LOGGER.error(f"Error setting up platforms: {e}")
        audit(hass, f"SETUP FAIL forwarding platforms: {e}")
        return False

    # Audit: report the entity registry state for this entry after platform setup,
    # including any that still carry a `_N` suffix (should be zero post-migration).
    try:
        import re as _re
        from homeassistant.helpers import entity_registry as _er
        _reg = _er.async_get(hass)
        _entries = _er.async_entries_for_config_entry(_reg, entry.entry_id)
        # Flag the HA de-dup suffix (_2, _3, ...). It's always >= 2, so a legit
        # trailing _0 / _1 (e.g. battery_0_voltage has _0 mid-id, not trailing)
        # won't false-positive; we match _<2-9 or multi-digit> at the very end.
        _dup_re = _re.compile(r"_([2-9]|\d{2,})$")
        _suffixed = [e.entity_id for e in _entries if _dup_re.search(e.entity_id)]
        audit(hass, f"post-setup: {len(_entries)} registry entities; "
                    f"{len(_suffixed)} still _N-suffixed"
                    + (f" -> {_suffixed}" if _suffixed else ""))
    except Exception as e:
        audit(hass, f"post-setup audit failed: {e}")

    # Step 5: Mark setup as complete
    LOGGER.info(f"Monitor My Solar setup completed successfully for {len(dongle_ids)} dongles")
    
    # Step 6: Start listening to all MQTT topics for all dongles
    # Only do this once to avoid duplicate subscriptions
    await coordinator.start_mqtt_subscription()

    # Step 7: Prune orphaned devices (e.g. empty device-grouping sub-devices left
    # behind after the user turned grouping off). Deferred until HA has started and
    # entity registration has settled, so we never remove a device whose entities
    # simply haven't finished registering yet.
    from homeassistant.helpers.start import async_at_started
    from homeassistant.helpers.event import async_call_later

    async def _run_device_cleanup(*_):
        try:
            await async_cleanup_orphan_devices(hass, entry)
        except Exception as e:
            LOGGER.error(f"Error cleaning up orphaned devices: {e}")

    def _schedule_device_cleanup(_event):
        async_call_later(hass, 5, _run_device_cleanup)

    async_at_started(hass, _schedule_device_cleanup)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: MonitorMySolarEntry) -> bool:
    """Unload a config entry."""
    LOGGER.info(f"Unloading Monitor My Solar integration for {entry.data.get('inverter_brand')}")
    
    # Get the coordinator instance
    coordinator = entry.runtime_data
    
    if coordinator:
        # First stop MQTT subscription to prevent new data coming in
        await coordinator.stop_mqtt_subscription()
        
        # Use the correct unload method
        try:
            # Unload all platforms
            unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
            return unload_ok
        except Exception as e:
            LOGGER.error(f"Error unloading entry: {e}")
            return False
    
    return True
