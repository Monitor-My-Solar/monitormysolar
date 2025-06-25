"""Base MonitorMySolar entity."""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import recorder as recorder_helper

from .coordinator import MonitorMySolar
from .const import DOMAIN, LOGGER

class MonitorMySolarEntity(CoordinatorEntity[MonitorMySolar]):
    """Base MonitorMySolar entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MonitorMySolar,
    ) -> None:
        # self.coordinator = coordinator
        """Initialize light."""
        super().__init__(coordinator)
        
        # If this attribute is not set in a subclass, default to True
        if not hasattr(self, '_attr_entity_registry_enabled_default'):
            self._attr_entity_registry_enabled_default = True
            
        # Initialize throttling variables
        self._last_state_change = 0
        self._update_interval = None

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
        
    def get_device_info(self, dongle_id: str, manufacturer: str) -> dict:
        """Return a consistent device info dictionary.
        
        This centralizes the device_info creation for all entity types.
        """
        # Get firmware versions if available
        fw_version = self.coordinator.current_fw_versions.get(dongle_id, "")
        # UI version tracking was removed in v3.0.0
        fw_code = self.coordinator.get_firmware_code(dongle_id)
        
        # Build device info dictionary with standard HA fields
        # Note: Home Assistant expects exactly these field names
        device_info = {
            "identifiers": {(DOMAIN, dongle_id)},
            "name": f"{dongle_id}",
        }
        
        # Default model and manufacturer values
        model_name = "Monitor My Solar Dongle"
        brand_name = manufacturer
        
        # Extract information from firmware code
        if fw_code and len(fw_code) == 4:
            # Import constants
            from .const import FIRMWARE_CODES, VALID_FIRMWARE_CODES
            
            # First character is device type code
            device_type_code = fw_code[0]
            # Second character is derived device type
            derived_type_code = fw_code[1]
            # Third character is ODM code (brand)
            odm_code = fw_code[2]
            # Fourth character is feature code (country)
            feature_code = fw_code[3]
            
            # Find the corresponding firmware code category
            model_key = None
            for key in FIRMWARE_CODES:
                if key.startswith(device_type_code.lower()) or key.startswith(device_type_code):
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
                
                # Use lookup for friendly name if available
                if fw_code in VALID_FIRMWARE_CODES:
                    model_name = VALID_FIRMWARE_CODES[fw_code]
        
        # Set manufacturer - this is a standard field in Home Assistant device registry
        device_info["manufacturer"] = brand_name
        
        # Set model - this is a standard field in Home Assistant device registry
        device_info["model"] = model_name
        
        # Add firmware version information
        if fw_version:
            device_info["sw_version"] = fw_version
            
        # Set via_device to establish device topology
        #device_info["via_device"] = (DOMAIN, "monitor_my_solar_hub")
            
        return device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            self._state = self.coordinator.entities[self.entity_id]
        else:
            LOGGER.warning(f"entity {self.entity_id} key not found")
        self.throttled_async_write_ha_state()
