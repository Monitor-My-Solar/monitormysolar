import logging
import asyncio
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
from .const import DOMAIN, ENTITIES
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
        
        # Process switches for this dongle
        for bank_name, switches in switch_config.items():
            # Skip combined switches for individual dongles
            if bank_name == "combined":
                continue
                
            for switch in switches:
                allowed_firmware_codes = switch.get("allowed_firmware_codes", [])
                if not allowed_firmware_codes or firmware_code in allowed_firmware_codes:
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
                # Check if this is the sync settings switch
                if switch.get("is_sync_switch", False):
                    entities.append(
                        CombinedSyncSwitch(switch, hass, entry, dongle_ids)
                    )
                else:
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
        return self._name

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
            self.throttled_async_write_ha_state()
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
            self.throttled_async_write_ha_state()  # Update HA state immediately
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
            self.throttled_async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                self._state = bool(value)
                # Schedule state update on the main thread
                self.hass.loop.call_soon_threadsafe(self.throttled_async_write_ha_state)

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
        self._source_entity = entity_info.get("source_entity", "")
        # Remove 'combined_' prefix from unique_id for entity_id
        entity_suffix = self._entity_type.lower().replace("combined_", "", 1)
        self.entity_id = f"switch.{self._formatted_dongle_id}_{entity_suffix}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._previous_state = None
        self._initialization_complete = False
        
        _LOGGER.info(f"Initializing combined switch {self._name} with entity_id: {self.entity_id}, source_entity: {self._source_entity}")
        
        # Track source entities that we need to monitor
        self._tracked_entities = []
        self._source_values = {}
        for dongle_id in dongle_ids:
            formatted_id = self.coordinator.get_formatted_dongle_id(dongle_id)
            source_entity_id = f"switch.{formatted_id}_{self._source_entity.lower()}"
            self._tracked_entities.append(source_entity_id)
            self._source_values[source_entity_id] = None
            _LOGGER.debug(f"Combined switch {self._name} will track: {source_entity_id}")
            
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
                # Use create_task to run the async method from a sync callback
                self.hass.async_create_task(self._update_combined_state())
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
            _LOGGER.info(f"Combined switch {self._name} state updated to: {self._state}")
        
        # Always update to ensure attributes are refreshed
        self.throttled_async_write_ha_state()
        
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
        # Check if we're still initializing
        if not hasattr(self, '_initialization_complete'):
            return True  # Show as available during initialization
        # After initialization, at least one source entity should exist and have a valid state
        for entity_id in self._tracked_entities:
            state = self.hass.states.get(entity_id)
            if state and state.state not in [STATE_UNKNOWN, "unavailable"]:
                return True
        return False
        
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
            self.throttled_async_write_ha_state()
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
            self.throttled_async_write_ha_state()
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
            self.throttled_async_write_ha_state()


    @property
    def extra_state_attributes(self):
        """Return extra attributes about the combined switch."""
        # Format the dongle states for display
        dongle_states = {}
        for entity_id, value in self._source_values.items():
            # Extract dongle ID from entity_id (e.g., switch.dongle_40_4c_ca_4e_90_00_accharge)
            parts = entity_id.split('.')[-1].split('_')
            if len(parts) >= 8:  # dongle + XX_XX_XX_XX_XX_XX + setting name
                dongle_id = '_'.join(parts[1:7]).replace('_', ':')
                dongle_states[f"dongle:{dongle_id}"] = "on" if value else "off" if value is not None else "unknown"
        
        # Log for debugging
        _LOGGER.debug(f"Combined switch {self._name} attributes - source values: {self._source_values}, dongle states: {dongle_states}")
        
        return {
            **dongle_states,
            "source_entities": self._tracked_entities
        }
    
    async def _initialize_state(self):
        """Initialize the state based on current source entity states."""
        # Try multiple times with increasing delays to ensure entities are loaded
        for attempt in range(3):
            await asyncio.sleep(2 * (attempt + 1))  # 2s, 4s, 6s delays
            
            entities_found = False
            for entity_id in self._tracked_entities:
                state = self.hass.states.get(entity_id)
                if state and state.state not in [STATE_UNKNOWN, "unavailable"]:
                    entities_found = True
                    try:
                        if state.state.lower() == 'on':
                            value = True
                        elif state.state.lower() == 'off':
                            value = False
                        else:
                            value = bool(int(state.state))
                        self._source_values[entity_id] = value
                    except (ValueError, TypeError):
                        _LOGGER.debug(f"Could not parse state for {entity_id}: {state.state}")
            
            if entities_found:
                break
            elif attempt < 2:
                _LOGGER.debug(f"Attempt {attempt + 1}: Source entities not ready for {self._name}, retrying...")
        
        self._initialization_complete = True
        await self._update_combined_state()
        self.throttled_async_write_ha_state()
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Override to prevent looking for combined entity in coordinator."""
        # Combined entities don't receive direct MQTT updates
        # They only update based on their source entities
        pass


class CombinedSyncSwitch(MonitorMySolarEntity, SwitchEntity):
    """Special switch to enable/disable automatic inverter setting synchronization."""
    
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, dongle_ids):
        """Initialize the sync switch."""
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._state = self.coordinator.get_sync_settings_enabled()  # Get saved state
        self._dongle_ids = dongle_ids
        self._virtual_id = "combined_parallel"
        self._formatted_dongle_id = "combined"
        self._entity_type = entity_info["unique_id"]
        # Remove 'combined_' prefix from unique_id if it exists for sync switch
        entity_suffix = self._entity_type.lower().replace("combined_", "", 1)
        self.entity_id = f"switch.{self._formatted_dongle_id}_{entity_suffix}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._icon = entity_info.get("icon", "mdi:sync")
        
        # Track all listeners we set up
        self._sync_listeners = []
        self._monitored_entities: Dict[str, any] = {}
        self._periodic_sync_task = None
        self._sync_check_interval = 60  # Check every 60 seconds
        
        super().__init__(self.coordinator)
        
    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # If sync was enabled before restart, set up listeners
        if self._state:
            await self._setup_sync_listeners()
            _LOGGER.info(f"Restored sync state: enabled for {len(self._dongle_ids)} dongles")
        
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
    def icon(self):
        return self._icon
        
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
        
    @property
    def extra_state_attributes(self):
        """Return extra attributes about the sync switch."""
        # Get recent sync history
        recent_syncs = []
        if hasattr(self.coordinator, '_setting_history'):
            # Get last 10 sync operations
            all_changes = []
            for setting, history in self.coordinator._setting_history.items():
                for entry in history[-5:]:  # Last 5 per setting
                    all_changes.append({
                        "setting": setting,
                        "dongle": entry["dongle_id"],
                        "value": entry["value"],
                        "timestamp": entry["timestamp"]
                    })
            # Sort by timestamp and take last 10
            recent_syncs = sorted(all_changes, key=lambda x: x["timestamp"], reverse=True)[:10]
        
        return {
            "sync_enabled": self._state,
            "monitored_dongles": self._dongle_ids,
            "monitored_entities_count": len(self._monitored_entities),
            "synced_entity_types": ["switch", "number", "select", "time"] if self._state else [],
            "sync_check_interval_seconds": self._sync_check_interval,
            "recent_sync_history": recent_syncs
        }
        
    async def async_turn_on(self, **kwargs):
        """Enable setting synchronization."""
        self._state = True
        self.coordinator.set_sync_settings_enabled(True)
        self.throttled_async_write_ha_state()
        await self._setup_sync_listeners()
        await self._start_periodic_sync_check()
        # Do an immediate sync check
        await self._check_and_sync_all_settings()
        _LOGGER.info(f"Inverter settings synchronization enabled for {len(self._dongle_ids)} dongles")
        
    async def async_turn_off(self, **kwargs):
        """Disable setting synchronization."""
        self._state = False
        self.coordinator.set_sync_settings_enabled(False)
        self.throttled_async_write_ha_state()
        await self._remove_sync_listeners()
        await self._stop_periodic_sync_check()
        _LOGGER.info("Inverter settings synchronization disabled")
        
    async def _setup_sync_listeners(self):
        """Set up listeners for all entities that should be synchronized."""
        # Get all entities that need syncing
        inverter_brand = self.coordinator.inverter_brand
        brand_entities = ENTITIES.get(inverter_brand, {})
        
        # Entity types to monitor for changes (excluding sensors and binary sensors)
        monitored_types = ["switch", "number", "select", "time", "time_hhmm"]
        
        for entity_type in monitored_types:
            if entity_type not in brand_entities:
                continue
                
            for bank_name, entities in brand_entities[entity_type].items():
                # Skip combined entities to avoid loops
                if bank_name == "combined":
                    continue
                    
                for entity_config in entities:
                    unique_id = entity_config["unique_id"]
                    
                    # Create listeners for each dongle
                    for dongle_id in self._dongle_ids:
                        formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
                        
                        # Determine the actual entity type for entity_id
                        actual_entity_type = "time" if entity_type == "time_hhmm" else entity_type
                        entity_id = f"{actual_entity_type}.{formatted_dongle_id}_{unique_id.lower()}"
                        
                        # Store entity info for later use
                        self._monitored_entities[entity_id] = {
                            "dongle_id": dongle_id,
                            "unique_id": unique_id,
                            "entity_type": entity_type,
                            "bank_name": bank_name
                        }
                        
                        # Set up listener
                        @callback
                        async def async_state_changed_listener(event: Event, monitored_entity_id=entity_id) -> None:
                            """Handle entity state changes and sync to other dongles."""
                            await self._handle_entity_change(event, monitored_entity_id)
                            
                        listener = async_track_state_change_event(
                            self.hass, entity_id, async_state_changed_listener
                        )
                        self._sync_listeners.append(listener)
        
        _LOGGER.info(f"Set up synchronization for {len(self._monitored_entities)} entities across {len(self._dongle_ids)} dongles")
        
    async def _handle_entity_change(self, event: Event, entity_id: str):
        """Handle when a monitored entity changes and sync to other dongles."""
        if not self._state:  # Sync is disabled
            return
            
        if not hasattr(event, 'data'):
            return
            
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        
        if new_state is None or new_state.state in [STATE_UNKNOWN, "unavailable"]:
            return
            
        # Get entity info
        entity_info = self._monitored_entities.get(entity_id)
        if not entity_info:
            return
            
        source_dongle_id = entity_info["dongle_id"]
        unique_id = entity_info["unique_id"]
        entity_type = entity_info["entity_type"]
        
        # Don't sync if the value hasn't actually changed
        if old_state and old_state.state == new_state.state:
            return
            
        _LOGGER.info(f"Syncing change from {entity_id}: {old_state.state if old_state else 'unknown'} -> {new_state.state}")
        
        # Record this change in history
        self.coordinator.record_setting_change(source_dongle_id, unique_id, new_state.state)
        
        # Determine the value to sync based on entity type
        value = None
        if entity_type == "switch":
            value = 1 if new_state.state == "on" else 0
        elif entity_type in ["number", "select"]:
            value = new_state.state
        elif entity_type in ["time", "time_hhmm"]:
            # For time entities, we need to handle the format properly
            value = new_state.state
            
        if value is None:
            _LOGGER.warning(f"Could not determine value to sync for {entity_id}")
            return
            
        # Get the MQTT handler
        mqtt_handler = self.coordinator.mqtt_handler
        if not mqtt_handler:
            _LOGGER.error("MQTT Handler is not initialized")
            return
            
        # Sync to all other dongles
        other_dongle_ids = [d for d in self._dongle_ids if d != source_dongle_id]
        
        if not other_dongle_ids:
            return
            
        # Create a temporary entity object for the MQTT handler
        class TempEntity:
            def __init__(self, entity_id):
                self.entity_id = entity_id
                
            def revert_state(self):
                pass
                
            def async_write_ha_state(self):
                pass
                
        temp_entity = TempEntity(entity_id)
        
        # Use the multi-dongle update method for better reliability
        _LOGGER.debug(f"Syncing {unique_id}={value} from {source_dongle_id} to {len(other_dongle_ids)} other dongles")
        try:
            # Send update to all other dongles at once and wait for all responses
            success = await mqtt_handler.send_update_to_multiple_dongles(
                other_dongle_ids, unique_id, value, temp_entity
            )
            if not success:
                _LOGGER.warning(f"Failed to sync {unique_id} to one or more dongles: {other_dongle_ids}")
            else:
                _LOGGER.info(f"Successfully synced {unique_id}={value} to all {len(other_dongle_ids)} other dongles")
        except Exception as e:
            _LOGGER.error(f"Error syncing to other dongles: {e}")
        
    async def _remove_sync_listeners(self):
        """Remove all sync listeners."""
        for listener in self._sync_listeners:
            listener()
        self._sync_listeners.clear()
        self._monitored_entities.clear()
        _LOGGER.debug("Removed all sync listeners")
    
    async def _start_periodic_sync_check(self):
        """Start periodic checking for out-of-sync settings."""
        async def periodic_check():
            while self._state:
                await asyncio.sleep(self._sync_check_interval)
                if self._state:  # Double check we're still enabled
                    await self._check_and_sync_all_settings()
        
        self._periodic_sync_task = self.hass.async_create_task(periodic_check())
        _LOGGER.debug(f"Started periodic sync check every {self._sync_check_interval} seconds")
    
    async def _stop_periodic_sync_check(self):
        """Stop periodic sync checking."""
        if self._periodic_sync_task:
            self._periodic_sync_task.cancel()
            self._periodic_sync_task = None
        _LOGGER.debug("Stopped periodic sync check")
    
    async def _check_and_sync_all_settings(self):
        """Check all monitored settings and sync any that are out of sync."""
        if not self._state:
            return
            
        _LOGGER.debug("Running periodic sync check for all monitored settings")
        
        # Get all unique settings being monitored
        unique_settings = {}
        for entity_id, entity_info in self._monitored_entities.items():
            unique_id = entity_info["unique_id"]
            entity_type = entity_info["entity_type"]
            if unique_id not in unique_settings:
                unique_settings[unique_id] = {
                    "entity_type": entity_type,
                    "entities": []
                }
            unique_settings[unique_id]["entities"].append(entity_id)
        
        # Check each setting
        out_of_sync_count = 0
        for unique_id, setting_info in unique_settings.items():
            entity_type = setting_info["entity_type"]
            entities = setting_info["entities"]
            
            # Get current values for all dongles
            values = {}
            for entity_id in entities:
                state = self.hass.states.get(entity_id)
                if state and state.state not in [STATE_UNKNOWN, "unavailable"]:
                    dongle_id = self._monitored_entities[entity_id]["dongle_id"]
                    values[dongle_id] = state.state
            
            # Check if values are different
            if len(set(values.values())) > 1:
                out_of_sync_count += 1
                _LOGGER.warning(f"Setting {unique_id} is out of sync across dongles: {values}")
                
                # Use history to determine which value is correct
                latest_change = self.coordinator.get_latest_setting_change(unique_id)
                
                if latest_change:
                    # Use the most recent change as source of truth
                    correct_value = latest_change["value"]
                    source_dongle = latest_change["dongle_id"]
                    _LOGGER.info(f"Using most recent change from {source_dongle} as source of truth: {unique_id}={correct_value}")
                else:
                    # No history, use the most common value or first dongle's value
                    value_counts = {}
                    for v in values.values():
                        value_counts[v] = value_counts.get(v, 0) + 1
                    correct_value = max(value_counts, key=value_counts.get)
                    source_dongle = next(d for d, v in values.items() if v == correct_value)
                    _LOGGER.info(f"No history available, using most common value from {source_dongle}: {unique_id}={correct_value}")
                
                # Sync all other dongles to the correct value
                dongles_to_sync = [d for d, v in values.items() if v != correct_value]
                
                if dongles_to_sync:
                    # Convert value for MQTT based on entity type
                    mqtt_value = None
                    if entity_type == "switch":
                        mqtt_value = 1 if correct_value == "on" else 0
                    elif entity_type in ["number", "select", "time", "time_hhmm"]:
                        mqtt_value = correct_value
                    
                    if mqtt_value is not None:
                        # Create temp entity for sync
                        class TempEntity:
                            def __init__(self, entity_id):
                                self.entity_id = entity_id
                            def revert_state(self):
                                pass
                            def async_write_ha_state(self):
                                pass
                        
                        temp_entity = TempEntity(f"sync_check_{unique_id}")
                        
                        # Send update to out-of-sync dongles
                        mqtt_handler = self.coordinator.mqtt_handler
                        if mqtt_handler:
                            try:
                                success = await mqtt_handler.send_update_to_multiple_dongles(
                                    dongles_to_sync, unique_id, mqtt_value, temp_entity
                                )
                                if success:
                                    _LOGGER.info(f"Successfully synced {unique_id}={correct_value} to {len(dongles_to_sync)} dongles")
                                else:
                                    _LOGGER.error(f"Failed to sync {unique_id} to out-of-sync dongles")
                            except Exception as e:
                                _LOGGER.error(f"Error during periodic sync of {unique_id}: {e}")
        
        if out_of_sync_count > 0:
            _LOGGER.info(f"Periodic sync check found and corrected {out_of_sync_count} out-of-sync settings")
        else:
            _LOGGER.debug("Periodic sync check found all settings in sync")
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Override to prevent looking for sync switch in coordinator."""
        # Sync switch doesn't receive direct MQTT updates
        # It only manages other entities
        pass
