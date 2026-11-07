"""Base MonitorMySolar entity."""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import recorder as recorder_helper

from .coordinator import MonitorMySolar
from .const import DOMAIN, LOGGER, CONF_ENABLE_DEVICE_GROUPING, DEFAULT_ENABLE_DEVICE_GROUPING

class MonitorMySolarEntity(CoordinatorEntity[MonitorMySolar]):
    """Base MonitorMySolar entity."""

    def __init__(
        self,
        coordinator: MonitorMySolar,
    ) -> None:
        # self.coordinator = coordinator
        """Initialize light."""
        super().__init__(coordinator)

        # Freeze the coordinator-data key at construction. The coordinator keys
        # its data dict by the entity_id computed via build_entity_id(), but the
        # live self.entity_id can diverge from that afterwards: the registry
        # appends _2 on a collision (e.g. two unprefixed single-dongle entries)
        # and users can rename entity_ids. Data lookups must always use this
        # frozen key — looking up by self.entity_id breaks the entity forever
        # after any rename.
        self._data_key = getattr(self, "entity_id", None)

        # Dynamically set has_entity_name based on number of dongles
        # If single dongle, don't use entity name (cleaner display)
        # If multiple dongles, use entity name for clarity
        self._attr_has_entity_name = len(coordinator._dongle_ids) > 1
        
        # If this attribute is not set in a subclass, default to True
        if not hasattr(self, '_attr_entity_registry_enabled_default'):
            self._attr_entity_registry_enabled_default = True
            
        # Initialize throttling variables
        self._last_state_change = 0
        self._update_interval = None

    @property
    def data_key(self) -> str:
        """Key into coordinator.entities for this entity's data.

        The construction-time computed entity_id — NOT the live self.entity_id,
        which the registry may have renamed (collision _2 suffix, user rename).
        Falls back to the live id for entity classes that never set entity_id
        before base __init__ (they keep today's behaviour).
        """
        return self._data_key or self.entity_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True
        
    @property
    def update_interval(self) -> int:
        """Get the update interval from config entry."""
        if self._update_interval is None:
            # Get from config entry, default to 60 seconds if not set
            self._update_interval = self.coordinator.entry.data.get("update_interval", 60)
        return self._update_interval
    
    def throttled_async_write_ha_state(self) -> None:
        """Write HA state immediately - entities update in real-time."""
        # For MonitorMySolar, we always write state immediately for real-time updates
        # Call the parent class method directly to avoid recursion
        super().async_write_ha_state()
        
    @property 
    def should_poll(self) -> bool:
        """No polling needed."""
        return False
        
    @property
    def force_update(self) -> bool:
        """Force state updates even if state hasn't changed."""
        # This ensures UI updates even when values are the same
        return False
        
    def get_device_info(self, dongle_id: str, manufacturer: str, device_group: str = None) -> dict:
        """Return a consistent device info dictionary.

        This centralizes the device_info creation for all entity types.
        When device_group is provided and grouping is enabled in config,
        creates a sub-device linked to the main device via via_device.
        """
        # Check if device grouping is enabled
        grouping_enabled = self.coordinator.entry.data.get(
            CONF_ENABLE_DEVICE_GROUPING, DEFAULT_ENABLE_DEVICE_GROUPING
        )

        # If grouping is enabled and we have a device_group, create a sub-device
        if grouping_enabled and device_group:
            # Get firmware version for the sub-device too
            fw_version = self.coordinator.current_fw_versions.get(dongle_id, "")

            device_info = {
                "identifiers": {(DOMAIN, f"{dongle_id}_{device_group}")},
                "name": f"{dongle_id} - {device_group}",
                "manufacturer": manufacturer,
                "model": device_group,
                "via_device": (DOMAIN, dongle_id),
            }

            if fw_version:
                device_info["sw_version"] = fw_version

            return device_info

        # Default behavior: return main device info
        # Get firmware versions if available
        fw_version = self.coordinator.current_fw_versions.get(dongle_id, "")
        # UI version tracking was removed in v3.0.0
        fw_code = self.coordinator.get_firmware_code(dongle_id)

        # Build device info dictionary with standard HA fields
        # Note: Home Assistant expects exactly these field names
        device_info = {
            "identifiers": {(DOMAIN, dongle_id)},
            "name": dongle_id,
        }

        # Default model and manufacturer values
        model_name = "Monitor My Solar Dongle"
        brand_name = manufacturer

        # Extract information from firmware code
        if fw_code and len(fw_code) == 4:
            # Import constants
            from .const import FIRMWARE_CODES, VALID_FIRMWARE_CODES, fw_code_get

            # Dongles report codes in mixed case ("Ceaa", "FAAA") and the
            # per-character tables below are keyed uppercase — normalize before
            # every lookup.
            device_type_code = fw_code[0].upper()
            # Second character is derived device type
            derived_type_code = fw_code[1].upper()
            # Third character is ODM code (brand)
            odm_code = fw_code[2].upper()
            # Fourth character is feature code (country)
            feature_code = fw_code[3].upper()

            # Find the corresponding firmware code category
            model_key = None
            for key in FIRMWARE_CODES:
                if key.upper().startswith(device_type_code):
                    model_key = key
                    break

            if model_key:
                # Extract base model name by removing initial letter and underscores
                base_model = model_key.split('_', 1)[1] if '_' in model_key else model_key
                base_model = base_model.replace('_', ' ')

                # Get brand information from ODM code
                if odm_code in FIRMWARE_CODES.get(model_key, {}).get("ODM_Code", {}):
                    brand = FIRMWARE_CODES[model_key]["ODM_Code"][odm_code]
                    if brand and brand != "Others":
                        brand_name = brand

                # Get feature information (country/model type)
                feature = None
                if feature_code in FIRMWARE_CODES.get(model_key, {}).get("Feature_Code", {}):
                    feature = FIRMWARE_CODES[model_key]["Feature_Code"][feature_code]

                # Get derived type information
                derived_type = None
                if derived_type_code in FIRMWARE_CODES.get(model_key, {}).get("Derived_Device_Type", {}):
                    derived_type = FIRMWARE_CODES[model_key]["Derived_Device_Type"][derived_type_code]

                # Create a comprehensive model name
                if derived_type and derived_type != "Others" and derived_type != "Standard Model":
                    model_name = f"{base_model} - {derived_type}"
                else:
                    model_name = base_model

                # Add feature information if it adds value
                if feature and feature != "Others" and feature != "Standard Model":
                    model_name += f" ({feature})"

            # The lookup table is authoritative for the model name; the
            # character-derived name above is only a fallback for codes the
            # table doesn't know yet. Applied outside the model_key branch so
            # a table hit never depends on the character parsing working.
            friendly_name = fw_code_get(VALID_FIRMWARE_CODES, fw_code)
            if friendly_name:
                model_name = friendly_name

        # Set manufacturer - this is a standard field in Home Assistant device registry
        device_info["manufacturer"] = brand_name

        # Set model - this is a standard field in Home Assistant device registry
        device_info["model"] = model_name

        # Add firmware version information
        if fw_version:
            device_info["sw_version"] = fw_version

        return device_info

    async def async_added_to_hass(self) -> None:
        """Seed initial state from the coordinator store when added.

        HA's CoordinatorEntity does NOT call _handle_coordinator_update on add — an
        entity only updates on the *next* coordinator refresh after it subscribes.
        The connect-time snapshot is a one-shot: it writes every value into
        coordinator.entities once, often before this entity is added. On FW >= 4.3.0
        (change-data only) a value that doesn't change again — every hold/setting and
        many static input fields — would otherwise never reach the entity and it
        would sit empty forever. So pull whatever is already stored, right now.
        """
        await super().async_added_to_hass()
        # Every subclass's _handle_coordinator_update guards internally (it no-ops
        # if there's nothing stored for this entity), so calling it unconditionally
        # is safe and seeds whatever the snapshot already delivered.
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.data_key in self.coordinator.entities:
            self._state = self.coordinator.entities[self.data_key]
            self.throttled_async_write_ha_state()
        # No stored value yet (e.g. seeded at add-time before any data arrived) —
        # nothing to write. Avoid the spurious "key not found" warning + state write.
    
    def reload_integration(self) -> None:
        """Reload the integration."""
        LOGGER.info("Reload integration service called")
        # This would typically reload the integration
        # For now, just log the call
    
    def check_for_updates(self) -> None:
        """Check for firmware updates."""
        LOGGER.info("Check for updates service called")
        # This would typically check for firmware updates
        # For now, just log the call