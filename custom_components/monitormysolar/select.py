from homeassistant.components.select import SelectEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import (
    async_track_state_change_event,
)
from homeassistant.const import (
    STATE_UNKNOWN,
)
from .const import DOMAIN, ENTITIES, LOGGER
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

async def async_setup_entry(hass, entry: MonitorMySolarEntry, async_add_entities):
    coordinator = entry.runtime_data
    inverter_brand = coordinator.inverter_brand
    dongle_ids = coordinator._dongle_ids
    
    brand_entities = ENTITIES.get(inverter_brand, {})
    select_config = brand_entities.get("select", {})

    entities = []
    
    # Loop through each dongle ID
    for dongle_id in dongle_ids:
        firmware_code = coordinator.get_firmware_code(dongle_id)
        
        # Only create entities if we have a firmware code
        if not firmware_code:
            LOGGER.debug(f"Skipping entity creation for {dongle_id} - no firmware code available yet")
            continue
        
        # Process selects for this dongle
        for bank_name, selects in select_config.items():
            for select in selects:
                allowed_firmware_codes = select.get("allowed_firmware_codes", [])
                # For GridBoss dongles (IAAB), only create entities that explicitly allow this firmware code
                if coordinator.is_gridboss_dongle(dongle_id):
                    if not allowed_firmware_codes or firmware_code not in allowed_firmware_codes:
                        continue
                else:
                    # For regular dongles, use the original logic
                    if not allowed_firmware_codes or firmware_code in allowed_firmware_codes:
                        pass  # Continue to entity creation
                    else:
                        continue  # Skip this entity
                
                try:
                    if bank_name == "holdbank6":
                        entities.append(QuickChargeDurationSelect(select, hass, entry, bank_name, dongle_id))
                    else:
                        entities.append(InverterSelect(select, hass, entry, dongle_id))
                except Exception as e:
                    LOGGER.error(f"Error setting up select {select} for dongle {dongle_id}: {e}")

    async_add_entities(entities, True)

class InverterSelect(MonitorMySolarEntity, SelectEntity):
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, dongle_id):
        """Initialize the select entity."""
        LOGGER.debug(f"Initializing select with info: {entity_info} for dongle {dongle_id}")
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{dongle_id}_{entity_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._entity_type = entity_info["unique_id"]
        self.entity_id = f"select.{self._formatted_dongle_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._options = entity_info["options"]
        self._manufacturer = entry.data.get("inverter_brand")

        super().__init__(self.coordinator)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def current_option(self):
        return self._state

    @property
    def options(self):
        return self._options

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Always return True - we'll use HomeAssistantError for conditional logic
        return self.coordinator.last_update_success
    
    @property
    def device_state_attributes(self) -> dict:
        """Return device state attributes."""
        attrs = {}
        availability_info = self.coordinator.get_entity_availability_info(self._dongle_id, self._entity_type)
        if not availability_info["available"] and availability_info["reason"]:
            attrs["unavailable_reason"] = availability_info["reason"]
        return attrs

    async def async_select_option(self, option):
        """Update the select option."""
        LOGGER.info(f"Setting select option for {self.entity_id} to {option}")
        
        # Check if entity should be available based on conditional settings
        availability_info = self.coordinator.get_entity_availability_info(self._dongle_id, self._entity_type)
        if not availability_info["available"] and availability_info["reason"]:
            raise HomeAssistantError(availability_info["reason"])
        
        # Store the previous state before changing
        self._previous_state = self._state
        self._state = option
        
        # Set a flag to indicate this is a user-initiated change
        self._user_initiated_change = True
        
        self.throttled_async_write_ha_state()

        bit_value = self._options.index(option)
        LOGGER.info(f"Setting Select value for {self.entity_id} to {option}")
        
        # Initialize smartload_number for Port Mode logic
        smartload_number = None
        
        # If this is a Port Mode change, trigger immediate availability update
        if "PortMode" in self.entity_info["unique_id"]:
            LOGGER.info(f"Port Mode changed to {option} (value: {bit_value}), triggering immediate availability update")
            # Update the Port Mode data immediately for availability logic
            if "SmartLoad1" in self.entity_info["unique_id"]:
                smartload_number = 1
            elif "SmartLoad2" in self.entity_info["unique_id"]:
                smartload_number = 2
            elif "SmartLoad3" in self.entity_info["unique_id"]:
                smartload_number = 3
            elif "SmartLoad4" in self.entity_info["unique_id"]:
                smartload_number = 4
        
        # If this is a charge/discharge control change, trigger immediate availability update
        elif self.entity_info["unique_id"] == "ubBatChgcontrol":
            LOGGER.info(f"Charge Control changed to {option}, triggering immediate availability update")
            self.coordinator.update_charge_control_setting(self._dongle_id, option)
        elif self.entity_info["unique_id"] == "ubBatDischgControl":
            LOGGER.info(f"Discharge Control changed to {option}, triggering immediate availability update")
            self.coordinator.update_discharge_control_setting(self._dongle_id, option)
        elif self.entity_info["unique_id"] == "ACChargeType":
            LOGGER.info(f"Charge Type changed to {option}, triggering immediate availability update")
            self.coordinator.update_charge_type_setting(self._dongle_id, option)
            LOGGER.info(f"Current charge type setting after update: {self.coordinator.get_charge_type_setting(self._dongle_id)}")
        
        # Handle Port Mode updates
        if smartload_number is not None:
            # Update the Port Mode data immediately
            port_modes = self.coordinator.get_port_modes(self._dongle_id)
            port_modes[f"SmartLoad{smartload_number}_PortMode"] = bit_value
            self.coordinator.update_port_modes(self._dongle_id, port_modes)
            
            # Log what entities should become available
            if bit_value == 1:  # Smart Load mode
                LOGGER.info(f"SmartLoad{smartload_number} set to Smart Load mode - SmartLoad{smartload_number} Enable switch and SOC/Volt mode select should become available")
            elif bit_value == 2:  # AC Coupled mode
                LOGGER.info(f"SmartLoad{smartload_number} set to AC Coupled mode - AC Coupled{smartload_number} Enable switch and SOC/Volt mode select should become available")
            elif bit_value == 0:  # Does Not Operate mode
                LOGGER.info(f"SmartLoad{smartload_number} set to Does Not Operate mode - all related entities should become unavailable")
        
        # If this is a SOC/Volt mode change, trigger immediate availability update
        elif "SOC_Volt" in self.entity_info["unique_id"]:
            LOGGER.info(f"SOC/Volt mode changed to {option} (value: {bit_value}), triggering immediate availability update")
            # Update the SOC/Volt mode data immediately for availability logic
            smartload_number = None
            if "SmartLoad1" in self.entity_info["unique_id"]:
                smartload_number = 1
            elif "SmartLoad2" in self.entity_info["unique_id"]:
                smartload_number = 2
            elif "SmartLoad3" in self.entity_info["unique_id"]:
                smartload_number = 3
            elif "SmartLoad4" in self.entity_info["unique_id"]:
                smartload_number = 4
            
            if smartload_number is not None:
                # Update the SOC/Volt mode data immediately
                soc_volt_bits = self.coordinator.get_smart_soc_volt_bits(self._dongle_id)
                soc_volt_bits[f"SmartLoad{smartload_number}_SOC_Volt"] = bit_value == 1  # True for SOC/Volt, False for Time
                self.coordinator.update_smart_soc_volt_bits(self._dongle_id, soc_volt_bits)
                
                # Log what entities should become available
                if bit_value == 1:  # SOC/Volt mode
                    LOGGER.info(f"SmartLoad{smartload_number} set to SOC/Volt mode - SOC/Volt entities should become available, Time entities should become unavailable")
                elif bit_value == 0:  # Time mode
                    LOGGER.info(f"SmartLoad{smartload_number} set to Time mode - Time entities should become available, SOC/Volt entities should become unavailable")
        
        await self.coordinator.mqtt_handler.send_update(
            self._dongle_id,
            self.entity_info["unique_id"],
            bit_value,
            self,
        )

    def revert_state(self):
        """Revert to the previous state."""
        if hasattr(self, '_previous_state') and self._previous_state is not None:
            LOGGER.info(f"Reverting state for {self.entity_id} from {self._state} to {self._previous_state}")
            self._state = self._previous_state
            # Clear the user-initiated flag since we're reverting
            if hasattr(self, '_user_initiated_change'):
                self._user_initiated_change = False
            self.throttled_async_write_ha_state()
        else:
            LOGGER.warning(f"No previous state to revert to for {self.entity_id}")
    
    def clear_user_initiated_flag(self):
        """Clear the user-initiated change flag when MQTT response is successful."""
        if hasattr(self, '_user_initiated_change'):
            LOGGER.debug(f"Select {self.entity_id}: Clearing user_initiated flag after successful MQTT response")
            self._user_initiated_change = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                # Handle different value types for different select types
                if "SOC_Volt" in self.entity_info["unique_id"]:
                    # For SOC/Volt mode selects, value might be boolean (True/False) or int (0/1)
                    if isinstance(value, bool):
                        new_state = "SOC/Volt" if value else "Time"
                    elif isinstance(value, int):
                        new_state = self._options[value] if value < len(self._options) else value
                    else:
                        new_state = value
                else:
                    # For other selects (like Port Mode), value is typically int
                    new_state = (
                        self._options[value]
                        if isinstance(value, int) and value < len(self._options)
                        else value
                    )
                
                # Debug logging to see what's happening
                # LOGGER.info(f"Select {self.entity_id}: Coordinator update - current state: {self._state}, coordinator value: {value}, new state: {new_state}, user_initiated: {getattr(self, '_user_initiated_change', False)}")
                
                # If this is a user-initiated change, don't override it with coordinator data
                # unless the coordinator data matches what the user selected
                if hasattr(self, '_user_initiated_change') and self._user_initiated_change:
                    if new_state == self._state:
                        # Coordinator data matches user selection, clear the flag
                        LOGGER.debug(f"Select {self.entity_id}: Coordinator data matches user selection, clearing user_initiated flag")
                        self._user_initiated_change = False
                    else:
                        # Coordinator data doesn't match, this might be stale data
                        LOGGER.warning(f"Select {self.entity_id}: Ignoring coordinator update during user-initiated change (coordinator: {new_state}, user: {self._state})")
                        return
                
                # Only update if the state actually changed to prevent unnecessary updates
                if new_state != self._state:
                    # Only log if this isn't the initial state setup (when _state was None)
                    if self._state is not None:
                        LOGGER.info(f"Select {self.entity_id}: Updating state from {self._state} to {new_state} (coordinator value: {value})")
                    else:
                        LOGGER.debug(f"Select {self.entity_id}: Initializing state to {new_state} (coordinator value: {value})")
                    self._state = new_state
                    # Schedule state update on the main thread
                    self.hass.loop.call_soon_threadsafe(self.throttled_async_write_ha_state)
                else:
                    # LOGGER.debug(f"Select {self.entity_id}: No state change needed (already {self._state})")
                    pass


class QuickChargeDurationSelect(MonitorMySolarEntity, SelectEntity):
    def __init__(self, entity_info, hass, entry, bank_name, dongle_id):
        """Initialize the select entity."""
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._attr_name = entity_info["name"]
        self._attr_unique_id = f"{entry.entry_id}_{dongle_id}_{entity_info['unique_id']}".lower()
        self._attr_options = entity_info["options"]
        self._attr_current_option = self._attr_options[0]  # Default to first option
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._entity_type = entity_info["unique_id"]
        self.entity_id = f"select.{self._formatted_dongle_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._additional_payload = entity_info.get("additional_payload")

        super().__init__(self.coordinator)
        
    @property
    def name(self):
        return self._attr_name

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            # Prepare the payload dictionary
            payload_dict = {
                self._entity_type: option
            }
            
            # Add additional payload if configured
            if self._additional_payload:
                value_map = self._additional_payload.get("value_map", {})
                additional_value = value_map.get(option, value_map.get("default"))
                if additional_value is not None:
                    payload_dict[self._additional_payload["key"]] = additional_value

            # Send the multiple updates via MQTT
            await mqtt_handler.send_multiple_updates(
                self._dongle_id,
                payload_dict,
                self,
            )
            
            self._attr_current_option = option
            self.throttled_async_write_ha_state()
        else:
            LOGGER.error("MQTT Handler is not initialized")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                if value in self._attr_options:
                    self._attr_current_option = value
                    self.throttled_async_write_ha_state()