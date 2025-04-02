import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    Event,
)
from homeassistant.const import (
    STATE_UNKNOWN,
)
from typing import Dict, List, Optional
from .const import DOMAIN, ENTITIES, FIRMWARE_CODES
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry: MonitorMySolarEntry, async_add_entities):
    coordinator = entry.runtime_data
    inverter_brand = coordinator.inverter_brand
    dongle_ids = coordinator._dongle_ids
    
    brand_entities = ENTITIES.get(inverter_brand, {})
    switch_config = brand_entities.get("switch", {})

    entities = []
    
    # Loop through each dongle ID
    for dongle_id in dongle_ids:
        firmware_code = coordinator.get_firmware_code(dongle_id)
        device_type = FIRMWARE_CODES.get(firmware_code, {}).get("Device_Type", "")
        
        # Process switches for this dongle
        for bank_name, switches in switch_config.items():
            # Skip combined switches for individual dongles
            if bank_name == "combined":
                continue
                
            for switch in switches:
                allowed_device_types = switch.get("allowed_device_types", [])
                if not allowed_device_types or device_type in allowed_device_types:
                    try:
                        entities.append(
                            InverterSwitch(switch, hass, entry, bank_name, dongle_id)
                        )
                    except Exception as e:
                        _LOGGER.error(f"Error setting up switch {switch} for dongle {dongle_id}: {e}")
                        
    # Create combined switches if we have multiple dongles
    if len(dongle_ids) > 1 and "combined" in switch_config:
        _LOGGER.info(f"Creating combined switches for {len(dongle_ids)} dongles")
        combined_switches = switch_config.get("combined", [])
        for switch in combined_switches:
            try:
                entities.append(
                    CombinedSwitch(switch, hass, entry, dongle_ids)
                )
            except Exception as e:
                _LOGGER.error(f"Error setting up combined switch {switch}: {e}")

    async_add_entities(entities, True)

class InverterSwitch(MonitorMySolarEntity, SwitchEntity):
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, bank_name, dongle_id):
        """Initialize the switch."""
        _LOGGER.debug(f"Initializing switch with info: {entity_info} for dongle {dongle_id}")
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{dongle_id}_{entity_info['unique_id']}".lower()
        self._state = False
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._entity_type = entity_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id = f"switch.{self._formatted_dongle_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._previous_state = None

        super().__init__(self.coordinator)

    @property
    def name(self):
        return f"{self._name} ({self._dongle_id})"

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def is_on(self):
        return self._state

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            self._previous_state = self._state
            self._state = True  # Optimistically update the state
            self.async_write_ha_state()
            _LOGGER.info(f"Setting Switch on value for {self.entity_id}")
            success = await mqtt_handler.send_update(
                self._dongle_id, self.entity_info["unique_id"], 1, self
            )
            if not success:
                self.revert_state()
        else:
            _LOGGER.error("MQTT Handler is not initialized")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            self._previous_state = self._state  # Save the current state before changing
            self._state = False  # Optimistically update the state in HA
            self.async_write_ha_state()  # Update HA state immediately
            _LOGGER.info(f"Setting Switch off value for {self.entity_id}")
            success = await mqtt_handler.send_update(
                self._dongle_id, self.entity_info["unique_id"], 0, self
            )
            if not success:
                self.revert_state()
        else:
            _LOGGER.error("MQTT Handler is not initialized")

    def revert_state(self):
        """Revert to the previous state."""
        if self._previous_state is not None:
            self._state = self._previous_state
            self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                self._state = bool(value)
                # Schedule state update on the main thread
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state())

class CombinedSwitch(MonitorMySolarEntity, SwitchEntity):
    """Switch that controls multiple dongles at once."""
    
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, dongle_ids):
        """Initialize the combined switch."""
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._state = False
        self._dongle_ids = dongle_ids
        self._virtual_id = "combined_parallel"
        self._formatted_dongle_id = "combined"
        self._entity_type = entity_info["unique_id"]
        self._source_entity = entity_info["source_entity"]
        self.entity_id = f"switch.{self._formatted_dongle_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._previous_state = None
        
        # Track source entities that we need to monitor
        self._tracked_entities = []
        self._source_values = {}
        for dongle_id in dongle_ids:
            formatted_id = self.coordinator.get_formatted_dongle_id(dongle_id)
            source_entity_id = f"switch.{formatted_id}_{self._source_entity.lower()}"
            self._tracked_entities.append(source_entity_id)
            self._source_values[source_entity_id] = None
            
        # Set up state tracking
        for entity_id in self._tracked_entities:
            self._async_add_entity_listener(entity_id)
        
        super().__init__(self.coordinator)
        
    def _async_add_entity_listener(self, entity_id):
        """Set up a listener for a source entity."""
        @callback
        async def async_state_changed_listener(event: Event) -> None:
            """Handle entity state changes."""
            # Updated to use generic Event data structure
            if not hasattr(event, 'data'):
                return
                
            new_state = event.data.get("new_state")
            if new_state is None:
                return
                
            try:
                # Convert state to boolean
                if new_state.state.lower() == 'on':
                    value = True
                elif new_state.state.lower() == 'off':
                    value = False
                else:
                    value = bool(int(new_state.state))
                    
                self._source_values[entity_id] = value
                await self._update_combined_state()
            except (ValueError, TypeError):
                _LOGGER.warning(f"Invalid state value for {entity_id}: {new_state.state}")
                
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, entity_id, async_state_changed_listener
            )
        )
    
    async def _update_combined_state(self):
        """Update the combined state based on source switches.
        
        If any switch is off, the combined state is off.
        """
        # Get all defined values
        values = [v for v in self._source_values.values() if v is not None]
        
        if not values:
            _LOGGER.debug(f"No values available for combined switch {self._name}")
            return
            
        # If any switch is OFF, the combined state is OFF
        new_state = all(values)
        
        if new_state != self._state:
            self._state = new_state
            self.async_write_ha_state()
        
    @property
    def name(self):
        return self._name
        
    @property
    def unique_id(self):
        return self._unique_id
        
    @property
    def is_on(self):
        return self._state
        
    @property
    def available(self):
        # At least one source value should be available
        return any(v is not None for v in self._source_values.values())
        
    @property
    def extra_state_attributes(self):
        """Return extra attributes about the switch."""
        return {
            "source_entities": self._tracked_entities,
            "source_values": {k: ("on" if v else "off") for k, v in self._source_values.items() if v is not None}
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
        
    async def async_turn_on(self, **kwargs):
        """Turn all dongles' switches on."""
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            self._previous_state = self._state
            self._state = True  # Optimistically update the state
            self.async_write_ha_state()
            _LOGGER.info(f"Setting Combined Switch on value for {self.entity_id} across {len(self._dongle_ids)} dongles")
            success = await mqtt_handler.send_update_to_multiple_dongles(
                self._dongle_ids, self._source_entity, 1, self
            )
            if not success:
                self.revert_state()
        else:
            _LOGGER.error("MQTT Handler is not initialized")
            
    async def async_turn_off(self, **kwargs):
        """Turn all dongles' switches off."""
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            self._previous_state = self._state
            self._state = False  # Optimistically update the state
            self.async_write_ha_state()
            _LOGGER.info(f"Setting Combined Switch off value for {self.entity_id} across {len(self._dongle_ids)} dongles")
            success = await mqtt_handler.send_update_to_multiple_dongles(
                self._dongle_ids, self._source_entity, 0, self
            )
            if not success:
                self.revert_state()
        else:
            _LOGGER.error("MQTT Handler is not initialized")
            
    def revert_state(self):
        """Revert to the previous state."""
        if self._previous_state is not None:
            self._state = self._previous_state
            self.async_write_ha_state()
