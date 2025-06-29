from homeassistant.components.number import NumberEntity
from homeassistant.core import callback
import json
import asyncio
from homeassistant.helpers.event import (
    async_track_state_change_event,
    Event,
)
from homeassistant.const import (
    STATE_UNKNOWN,
)
from typing import Dict, List, Optional
from .const import DOMAIN, ENTITIES, LOGGER
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

async def async_setup_entry(hass, entry: MonitorMySolarEntry, async_add_entities):
    coordinator = entry.runtime_data
    inverter_brand = coordinator.inverter_brand
    dongle_ids = coordinator._dongle_ids
    
    brand_entities = ENTITIES.get(inverter_brand, {})
    number_config = brand_entities.get("number", {})

    entities = []
    
    # Loop through each dongle ID
    for dongle_id in dongle_ids:
        firmware_code = coordinator.get_firmware_code(dongle_id)
        
        # Process numbers for this dongle
        for bank_name, numbers in number_config.items():
            # Skip combined numbers for individual dongles
            if bank_name == "combined":
                continue
                
            for number in numbers:
                allowed_firmware_codes = number.get("allowed_firmware_codes", [])
                if not allowed_firmware_codes or firmware_code in allowed_firmware_codes:
                    try:
                        entities.append(
                            InverterNumber(number, hass, entry, bank_name, dongle_id)
                        )
                    except Exception as e:
                        LOGGER.error(f"Error setting up number {number} for dongle {dongle_id}: {e}")
                    
    # Create combined numbers if we have multiple dongles
    if len(dongle_ids) > 1 and "combined" in number_config:
        LOGGER.info(f"Creating combined number entities for {len(dongle_ids)} dongles")
        combined_numbers = number_config.get("combined", [])
        for number in combined_numbers:
            try:
                entities.append(
                    CombinedNumber(number, hass, entry, dongle_ids)
                )
            except Exception as e:
                LOGGER.error(f"Error setting up combined number {number}: {e}")

    async_add_entities(entities, True)

class InverterNumber(MonitorMySolarEntity, NumberEntity):
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, bank_name, dongle_id):
        """Initialize the number."""
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._attr_name = entity_info["name"]
        self._attr_unique_id = f"{entry.entry_id}_{dongle_id}_{entity_info['unique_id']}".lower()
        self._attr_native_value = 0
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._entity_type = entity_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id = f"number.{self._formatted_dongle_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._attr_native_min_value = entity_info.get("min", None)
        self._attr_native_max_value = entity_info.get("max", None)
        self._attr_mode = entity_info.get("mode", "auto")
        self._attr_native_unit_of_measurement = entity_info.get("unit", None)
        self._attr_device_class = entity_info.get("class", None)
        self._manufacturer = entry.data.get("inverter_brand")
        self._previous_value = self._attr_native_value  # Track the previous value for revert

        super().__init__(self.coordinator)

    @property
    def name(self):
        return self._attr_name

    async def async_set_native_value(self, value):
        """Set the number value."""
        LOGGER.debug(f"Setting value of number {self.entity_id} to {value}")
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            # Save the current value before changing
            self._previous_value = self._attr_native_value
            # Set the new value
            self._attr_native_value = value
            self.throttled_async_write_ha_state()

            # Send the update via MQTT
            success = await mqtt_handler.send_update(
                self._dongle_id,
                self.entity_info["unique_id"],
                value,
                self,
            )
            if not success:
                self.revert_state()
        else:
            LOGGER.error("MQTT Handler is not initialized")

    def revert_state(self):
        """Revert to the previous state."""
        LOGGER.info(f"Reverting state for {self.entity_id} to {self._previous_value}")
        self._attr_native_value = self._previous_value
        self.hass.loop.call_soon_threadsafe(self.throttled_async_write_ha_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                self._attr_native_value = value
                self.hass.loop.call_soon_threadsafe(self.throttled_async_write_ha_state)

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

class CombinedNumber(MonitorMySolarEntity, NumberEntity):
    """Number entity that controls multiple dongles at once."""
    
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, dongle_ids):
        """Initialize the combined number."""
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._attr_native_value = 0
        self._dongle_ids = dongle_ids
        self._virtual_id = "combined_parallel"
        self._formatted_dongle_id = "combined"
        self._entity_type = entity_info["unique_id"]
        self._source_entity = entity_info.get("source_entity", "")
        # Remove 'combined_' prefix from unique_id for entity_id
        entity_suffix = self._entity_type.lower().replace("combined_", "", 1)
        self.entity_id = f"number.{self._formatted_dongle_id}_{entity_suffix}"
        self.hass = hass
        self._attr_native_min_value = entity_info.get("min", None)
        self._attr_native_max_value = entity_info.get("max", None)
        self._attr_mode = entity_info.get("mode", "auto")
        self._attr_native_unit_of_measurement = entity_info.get("unit", None)
        self._attr_device_class = entity_info.get("class", None)
        self._manufacturer = entry.data.get("inverter_brand")
        self._previous_value = self._attr_native_value  # Track the previous value for revert
        
        # Track source entities that we need to monitor
        self._tracked_entities = []
        self._source_values = {}
        for dongle_id in dongle_ids:
            formatted_id = self.coordinator.get_formatted_dongle_id(dongle_id)
            source_entity_id = f"number.{formatted_id}_{self._source_entity.lower()}"
            self._tracked_entities.append(source_entity_id)
            self._source_values[source_entity_id] = None
            
        # Set up state tracking
        for entity_id in self._tracked_entities:
            self._async_add_entity_listener(entity_id)
        
        super().__init__(self.coordinator)
        
        # Initialize the state based on current source values
        self.hass.async_create_task(self._initialize_state())
        
    def _async_add_entity_listener(self, entity_id):
        """Set up a listener for a source entity."""
        @callback
        def async_state_changed_listener(event: Event) -> None:
            """Handle entity state changes."""
            # Handle generic Event data structure
            if not hasattr(event, 'data'):
                return
                
            new_state = event.data.get("new_state")
            if new_state is None:
                return
                
            try:
                value = float(new_state.state)
                self._source_values[entity_id] = value
                # Use create_task to run the async method from a sync callback
                self.hass.async_create_task(self._update_combined_state())
            except (ValueError, TypeError):
                LOGGER.warning(f"Invalid state value for {entity_id}: {new_state.state}")
                
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, entity_id, async_state_changed_listener
            )
        )
    
    async def _update_combined_state(self):
        """Update the combined state based on source entities.
        
        Takes the average of all current values.
        """
        # Filter out None values
        values = [v for v in self._source_values.values() if v is not None]
        
        if not values:
            LOGGER.debug(f"No values available for combined number {self._name}")
            return
            
        # Take the average for the display state
        avg_value = sum(values) / len(values)
        
        if avg_value != self._attr_native_value:
            self._attr_native_value = avg_value
            self.throttled_async_write_ha_state()
        
    @property
    def name(self):
        return self._name
        
    @property
    def unique_id(self):
        return self._unique_id
        
    @property
    def available(self):
        # At least one source value should be available
        return any(v is not None for v in self._source_values.values())
        
    @property
    def extra_state_attributes(self):
        """Return extra attributes about the number."""
        return {
            "source_entities": self._tracked_entities,
            "source_values": {k: v for k, v in self._source_values.items() if v is not None}
        }
        
    @property
    def device_info(self):
        # Create a custom device info for the virtual combined device
        device_info = {
            "identifiers": {(DOMAIN, self._virtual_id)},
            "name": "Combined Parallel Inverters",
            "manufacturer": f"{self._manufacturer}",
            "model": f"Virtual Combined Device ({len(self._dongle_ids)} inverters)"
        }
        return device_info
        
    async def async_set_native_value(self, value):
        """Set the value on all dongles."""
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            # Save the current value before changing
            self._previous_value = self._attr_native_value
            # Set the new value
            self._attr_native_value = value
            self.throttled_async_write_ha_state()
            
            LOGGER.info(f"Setting Combined Number value for {self.entity_id} to {value} across {len(self._dongle_ids)} dongles")
            success = await mqtt_handler.send_update_to_multiple_dongles(
                self._dongle_ids, self._source_entity, value, self
            )
            if not success:
                self.revert_state()
        else:
            LOGGER.error("MQTT Handler is not initialized")
            
    def revert_state(self):
        """Revert to the previous state."""
        LOGGER.info(f"Reverting state for {self.entity_id} to {self._previous_value}")
        self._attr_native_value = self._previous_value
        self.hass.loop.call_soon_threadsafe(self.throttled_async_write_ha_state)
    
    @property
    def extra_state_attributes(self):
        """Return extra attributes about the combined number."""
        # Format the dongle values for display
        dongle_values = {}
        for entity_id, value in self._source_values.items():
            # Extract dongle ID from entity_id
            parts = entity_id.split('.')[-1].split('_')
            if len(parts) >= 6:  # dongle_XX_XX_XX_XX_XX + setting name
                dongle_id = '_'.join(parts[:6]).replace('_', ':')
                dongle_values[f"{dongle_id}"] = str(value) if value is not None else "unknown"
        
        return {
            **dongle_values,
            "source_entities": self._tracked_entities,
            "operation": "average"
        }
    
    async def _initialize_state(self):
        """Initialize the state based on current source entity states."""
        await asyncio.sleep(2)  # Give entities time to load
        
        for entity_id in self._tracked_entities:
            state = self.hass.states.get(entity_id)
            if state:
                try:
                    value = float(state.state)
                    self._source_values[entity_id] = value
                except (ValueError, TypeError):
                    LOGGER.debug(f"Could not parse state for {entity_id}: {state.state}")
        
        await self._update_combined_state()
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Override to prevent looking for combined entity in coordinator."""
        # Combined entities don't receive direct MQTT updates
        # They only update based on their source entities
        pass