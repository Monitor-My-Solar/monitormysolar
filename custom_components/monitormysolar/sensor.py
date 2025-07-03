from datetime import datetime, timedelta
import json
import asyncio
from typing import cast, List
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_MODE,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    STATE_UNKNOWN,
)
from homeassistant.core import (
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit_system import METRIC_SYSTEM, US_CUSTOMARY_SYSTEM

from .const import DOMAIN, ENTITIES, FIRMWARE_CODES, LOGGER
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

async def async_setup_entry(hass, entry: MonitorMySolarEntry, async_add_entities):
    coordinator = entry.runtime_data
    inverter_brand = coordinator.inverter_brand
    dongle_ids = coordinator._dongle_ids
    
    brand_entities = ENTITIES.get(inverter_brand, {})
    sensors_config = brand_entities.get("sensor", {})

    entities = []

    # Loop through each dongle ID
    for dongle_id in dongle_ids:
        firmware_code = coordinator.get_firmware_code(dongle_id)
        formatted_dongle_id = coordinator.get_formatted_dongle_id(dongle_id)
        
        # Loop through the sensors in the configuration for this dongle
        for bank_name, sensors in sensors_config.items():
            # Skip combined sensors for individual dongles
            if bank_name == "combined":
                continue
                
            for sensor in sensors:
                allowed_firmware_codes = sensor.get("allowed_firmware_codes", [])
                if not allowed_firmware_codes or firmware_code in allowed_firmware_codes:
                    try:
                        # Check if the sensor is of type 'status' to create the StatusSensor class
                        if bank_name == "status":
                            entities.append(
                                StatusSensor(sensor, hass, entry, bank_name, dongle_id),
                            )
                        elif bank_name == "powerflow":
                            entities.append(
                                PowerFlowSensor(sensor, hass, entry, bank_name, dongle_id)
                            )
                        elif bank_name == "timestamp":
                            entities.append(
                                BankUpdateSensor(sensor, hass, entry, bank_name, dongle_id)
                            )
                        elif bank_name == "warning":
                            entities.append(
                                FaultWarningSensor(sensor, hass, entry, bank_name, dongle_id)
                            )
                        elif bank_name == "fault":
                            entities.append(
                                FaultWarningSensor(sensor, hass, entry, bank_name, dongle_id)
                            )
                        elif bank_name == "calculated":
                            entities.append(
                                CalculatedSensor(sensor, hass, entry, bank_name, dongle_id)
                            )
                        elif bank_name == "temperature":
                            entities.append(
                                TemperatureSensor(sensor, hass, entry, bank_name, dongle_id)
                            )
                        else:
                            entities.append(
                                InverterSensor(sensor, hass, entry, bank_name, dongle_id)
                            )
                    except Exception as e:
                        LOGGER.error(f"Error setting up sensor {sensor} for dongle {dongle_id}: {e}")

    # Create combined parallel sensors if we have multiple dongles
    if len(dongle_ids) > 1 and "combined" in sensors_config:
        LOGGER.info(f"Creating combined sensors for {len(dongle_ids)} dongles")
        combined_sensors = sensors_config.get("combined", [])
        for sensor in combined_sensors:
            try:
                entities.append(
                    CombinedParallelSensor(sensor, hass, entry, dongle_ids)
                )
            except Exception as e:
                LOGGER.error(f"Error setting up combined sensor {sensor}: {e}")
        
        # Add sync status sensor
        LOGGER.info(f"Creating sync status sensor for {len(dongle_ids)} dongles")
        entities.append(SyncStatusSensor(hass, entry, dongle_ids))

    async_add_entities(entities)


class InverterSensor(MonitorMySolarEntity, SensorEntity):
    def __init__(self, sensor_info, hass, entry, bank_name, dongle_id):
        """Initialize the sensor."""
        LOGGER.debug(f"Initializing sensor with info: {sensor_info} for dongle {dongle_id}")
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{dongle_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._sensor_type = sensor_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id: str = f"sensor.{self._formatted_dongle_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._unsubscribe_midnight = None
        self._reset_at_midnight = self._sensor_type in ["HourlyConsumption", "DailyConsumption"]
        LOGGER.debug(f"Initialized sensor {self.entity_id}")

        super().__init__(self.coordinator)

    @property
    def name(self):
        """Return the name of the sensor."""
        # If single dongle (has_entity_name is False), return just the name
        # If multiple dongles (has_entity_name is True), return entity name only
        if self._attr_has_entity_name:
            return self._name
        else:
            # For single dongle, return a clean name without device prefix
            return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def state_class(self):
        return self.sensor_info.get("state_class")

    @property
    def unit_of_measurement(self):
        return self.sensor_info.get("unit_of_measurement")

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")
    
    @property
    def suggested_display_precision(self):
        """Return the suggested display precision for energy sensors."""
        if self.device_class == SensorDeviceClass.ENERGY:
            return 2
        return None

    @property
    def last_reset(self):
        """Return the time when the sensor was last reset (midnight)."""
        if self.state_class == "total":
            return datetime.min
        return None

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                if self._sensor_type == "RunningTime" and isinstance(value, (float, int)):
                    # Convert seconds to HH:MM:SS format
                    seconds = int(value)
                    hours, remainder = divmod(seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    self._state = f"{hours:02}:{minutes:02}:{seconds:02}"
                # Convert Wh to kWh for energy consumption sensors
                elif self._sensor_type in ["HourlyConsumption", "DailyConsumption"] and isinstance(value, (float, int)):
                    # Convert from Wh to kWh by dividing by 1000
                    self._state = round(value / 1000, 3)
                    #LOGGER.debug(f"Converted {self._sensor_type} from {value}Wh to {self._state}kWh")
                else:
                    self._state = (
                        round(value, 2) if isinstance(value, (float, int)) else value
                    )
                self.throttled_async_write_ha_state()
        else:
            LOGGER.warning(f"entity {self.entity_id} key not found")

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Set up midnight reset for consumption sensors
        if self._reset_at_midnight:
            @callback
            def reset_consumption(_):
                """Reset consumption to 0 at midnight."""
                LOGGER.info(f"Resetting {self._sensor_type} to 0 at midnight for {self._dongle_id}")
                self._state = 0
                self.async_write_ha_state()
                
                # Also reset in coordinator data
                self.coordinator.entities[self.entity_id] = 0
            
            # Schedule reset at midnight (00:00:00)
            # For HourlyConsumption, also reset every hour
            if self._sensor_type == "HourlyConsumption":
                # Reset every hour on the hour
                self._unsubscribe_midnight = async_track_time_change(
                    self.hass,
                    reset_consumption,
                    minute=0,
                    second=0
                )
                LOGGER.debug(f"Set up hourly reset for {self._sensor_type} on {self._dongle_id}")
            else:  # DailyConsumption
                # Reset at midnight only
                self._unsubscribe_midnight = async_track_time_change(
                    self.hass,
                    reset_consumption,
                    hour=0,
                    minute=0,
                    second=0
                )
                LOGGER.debug(f"Set up daily midnight reset for {self._sensor_type} on {self._dongle_id}")
    
    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        if self._unsubscribe_midnight:
            self._unsubscribe_midnight()
        await super().async_will_remove_from_hass()



class StatusSensor(MonitorMySolarEntity, SensorEntity):
    def __init__(self, sensor_info, hass, entry, bank_name, dongle_id):
        """Initialize the sensor."""
        LOGGER.debug(f"Initializing sensor with info: {sensor_info} for dongle {dongle_id}")
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{dongle_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._sensor_type = sensor_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id = f"sensor.{self._formatted_dongle_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._expected_attributes = sensor_info.get("attributes", [])

        # Initialize attributes with default values
        self._attributes = {attr: "unknown" for attr in self._expected_attributes}

        super().__init__(self.coordinator)

    @property
    def name(self):
        """Return the name of the sensor."""
        # If single dongle (has_entity_name is False), return just the name
        # If multiple dongles (has_entity_name is True), return entity name only
        if self._attr_has_entity_name:
            return self._name
        else:
            # For single dongle, return a clean name without device prefix
            return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state
    @property
    def state_class(self):
        return self.sensor_info.get("state_class")

    @property
    def unit_of_measurement(self):
        return self.sensor_info.get("unit")

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")
    
    @property
    def suggested_display_precision(self):
        """Return the suggested display precision for energy sensors."""
        if self.device_class == SensorDeviceClass.ENERGY:
            return 2
        return None

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if isinstance(value, dict):
                # Extract the 'uptime' for the sensor's state
                self._state = value.get("uptime")
                #LOGGER.debug(f'State updated to: {self._state}')

                # Update the sensor's attributes based on the expected attributes list
                for attr in self._expected_attributes:
                    self._attributes[attr] = value.get(attr, "unknown")

                #LOGGER.debug(f'Attributes updated to: {self._attributes}')

                self.throttled_async_write_ha_state()

class PowerFlowSensor(MonitorMySolarEntity, SensorEntity):
    def __init__(self, sensor_info, hass, entry, bank_name, dongle_id):
        """Initialize the Power Flow sensor."""
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{dongle_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._sensor_type = sensor_info["unique_id"]
        self.entity_id = f"sensor.{self._formatted_dongle_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._attribute1 = sensor_info.get("attribute1")
        self._attribute2 = sensor_info.get("attribute2")
        self._value1 = 0
        self._value2 = 0

        super().__init__(self.coordinator)

    @property
    def name(self):
        """Return the name of the sensor."""
        # If single dongle (has_entity_name is False), return just the name
        # If multiple dongles (has_entity_name is True), return entity name only
        if self._attr_has_entity_name:
            return self._name
        else:
            # For single dongle, return a clean name without device prefix
            return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state
    @property
    def state_class(self):
        return self.sensor_info.get("state_class")

    @property
    def unit_of_measurement(self):
        return self.sensor_info.get("unit_of_measurement")

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")
    
    @property
    def suggested_display_precision(self):
        """Return the suggested display precision for energy sensors."""
        if self.device_class == SensorDeviceClass.ENERGY:
            return 2
        return None


    @property
    def extra_state_attributes(self):
        return {
            self._attribute1: self._value1,
            self._attribute2: self._value2,

        }

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        attr1_entity_id = f"sensor.{self._formatted_dongle_id}_{self._attribute1.lower()}"
        attr2_entity_id = f"sensor.{self._formatted_dongle_id}_{self._attribute2.lower()}"
        if attr1_entity_id in self.coordinator.entities:
            attr1_value = self.coordinator.entities[attr1_entity_id]
            if attr1_value is not None:
                self._value1 = float(attr1_value)
        if attr2_entity_id in self.coordinator.entities:
            attr2_value = self.coordinator.entities[attr2_entity_id]
            if attr2_value is not None:
                self._value2 = float(attr2_value)

        # Calculate the flow value
        if self._value1 > 0:
            self._state = -1 * self._value1
        else:
            self._state = self._value2

        self.throttled_async_write_ha_state()

class CombinedSensor(MonitorMySolarEntity, SensorEntity):
    def __init__(self, sensor_info, hass, entry, dongle_id):
        """Initialize the Combined sensor."""
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = self.coordinator.dongle_id
        self._device_id = self.coordinator.dongle_id
        self._sensor_type = sensor_info["unique_id"]
        self.entity_id = f"sensor.{self._device_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._attributes = sensor_info.get("attributes", [])
        self._sensor_values = {attr: 0.0 for attr in self._attributes}  # Store individual sensor values

        super().__init__(self.coordinator)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state
    @property
    def state_class(self):
        return self.sensor_info.get("state_class")

    @property
    def unit_of_measurement(self):
        return self.sensor_info.get("unit_of_measurement")

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")
    
    @property
    def suggested_display_precision(self):
        """Return the suggested display precision for energy sensors."""
        if self.device_class == SensorDeviceClass.ENERGY:
            return 2
        return None


    @property
    def extra_state_attributes(self):
        return self._sensor_values

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        LOGGER.warning(f"CombinedSensor id: {self.entity_id}")
        LOGGER.warning(f"sensor_values: {self._sensor_values}")
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:

                if self.entity_id in self._sensor_values:
                    self._sensor_values[self.entity_id] = float(value)

                    # Example operation: Summing all sensor values
                    self._state = sum(self._sensor_values.values())
                    self.throttled_async_write_ha_state()

class BankUpdateSensor(MonitorMySolarEntity, SensorEntity):
    def __init__(self, sensor_info, hass, entry, bank_name, dongle_id):
        """Initialize the Bank Update sensor."""
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{dongle_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._sensor_type = sensor_info["unique_id"]
        self.entity_id = f"sensor.{self._formatted_dongle_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        
        # Set optional entity registry enabled default attribute
        self._attr_entity_registry_enabled_default = sensor_info.get("entity_registry_enabled_default", True)

        # Initialize attributes with None values
        self._attributes = {attr: None for attr in sensor_info.get("attributes", [])}

        super().__init__(self.coordinator)

    @property
    def name(self):
        """Return the name of the sensor."""
        # If single dongle (has_entity_name is False), return just the name
        # If multiple dongles (has_entity_name is True), return entity name only
        if self._attr_has_entity_name:
            return self._name
        else:
            # For single dongle, return a clean name without device prefix
            return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        """Return the most recent update time."""
        return self._state

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")
    
    @property
    def suggested_display_precision(self):
        """Return the suggested display precision for energy sensors."""
        if self.device_class == SensorDeviceClass.ENERGY:
            return 2
        return None

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    @callback
    def _handle_bank_update(self, event):
        """Handle bank update events."""
        # Skip processing if entity is disabled
        if not self.enabled:
            return
            
        bank_name = event.data.get("bank_name")
        event_dongle_id = event.data.get("dongle_id")
        
        # Only process events for our specific dongle
        if event_dongle_id != self._dongle_id:
            return
            
        LOGGER.debug(f"Update Event Called for: {bank_name} on dongle {event_dongle_id}")
        if bank_name:
            current_time = datetime.now().isoformat()
            attr_name = f"{bank_name}_last_update"
            LOGGER.debug(f"Updating Attribute name: {attr_name}")

            if attr_name in self._attributes:
                self._attributes[attr_name] = current_time
                self._state = current_time  # Update state to most recent update
                self.throttled_async_write_ha_state()

    async def async_added_to_hass(self):
        """Subscribe to events when added to hass."""
        LOGGER.debug(f"Subscribing to bank update event for {self.entity_id}")
        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_bank_updated", self._handle_bank_update)
        )

class FaultWarningSensor(MonitorMySolarEntity, SensorEntity):
    def __init__(self, sensor_info, hass, entry, bank_name, dongle_id):
        """Initialize the fault/warning sensor."""
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id
        self._device_id = dongle_id
        self._sensor_type = sensor_info["unique_id"]
        self.entity_id = f"sensor.{self._device_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._bank_name = bank_name

        self._history = []
        self._state = "No Fault" if "fault" in sensor_info["unique_id"] else "No Warning"
        self._value = 0

        super().__init__(self.coordinator)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._value == 0:
            return "No Fault" if "fault" in self._sensor_type else "No Warning"
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = {
            "value": self._value,
            "history": self._history
        }
        return attrs
    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)


    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        if self.entity_id in self.coordinator.entities:
            value_data = self.coordinator.entities[self.entity_id]
            #LOGGER.debug(f"Value data: {value_data}")
            if isinstance(value_data, dict):
                self._value = value_data.get("value", 0)
                description = value_data.get("description")
                #LOGGER.debug(f"Description: {description}")

                if description:  # New fault/warning
                    self._state = description
                    start_time = value_data.get("start_time", "Unknown")
                    end_time = value_data.get("end_time", "Ongoing")

                    # Check if the last entry in history is ongoing and matches the current description
                    if self._history and self._history[-1]["end_time"] == "Ongoing" and self._history[-1]["description"] == description:
                        # Update the end time of the ongoing event
                        self._history[-1]["end_time"] = end_time
                    else:
                        # Append a new entry for a new event
                        self._history.append({
                            "description": description,
                            "value": self._value,
                            "start_time": start_time,
                            "end_time": end_time
                        })
                    LOGGER.debug(f"History: {self._history}")
                else:  # Reset state
                    self._state = "No Fault" if "fault" in self._sensor_type else "No Warning"

                    # If there's an ongoing issue in history, mark it as resolved
                    if self._history and self._history[-1]["end_time"] == "Ongoing":
                        self._history[-1]["end_time"] = value_data.get("timestamp", "Unknown")

            self.throttled_async_write_ha_state()

class CalculatedSensor(MonitorMySolarEntity, SensorEntity):
    def __init__(self, sensor_info, hass, entry, bank_name, dongle_id):
        """Initialize the calculated sensor."""
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self.entry = entry  # Store the entry for use in event handling
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None

        # Store the formatted IDs
        self._dongle_id = dongle_id  # For device_info
        self._formatted_id = dongle_id.replace(":", "_")   # For sensor entity matching

        self._sensor_type = sensor_info["unique_id"]
        self.entity_id = f"sensor.{self._formatted_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._bank_name = bank_name

        # Get calculation info
        self._calculation = sensor_info.get("calculation", {})
        self._operation = self._calculation.get("operation")
        self._source_sensors = self._calculation.get("sensors", [])
        self._sensor_values = {sensor: 0 for sensor in self._source_sensors}

        super().__init__(self.coordinator)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def state_class(self):
        return self.sensor_info.get("state_class")

    @property
    def unit_of_measurement(self):
        return self.sensor_info.get("unit_of_measurement")

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")
    
    @property
    def suggested_display_precision(self):
        """Return the suggested display precision for energy sensors."""
        if self.device_class == SensorDeviceClass.ENERGY:
            return 2
        return None

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    def _calculate_state(self):
        """Calculate the state based on the operation and sensor values."""
        if self._operation == "division":
            numerator = self._sensor_values[self._source_sensors[0]]
            denominator = self._sensor_values[self._source_sensors[1]]
            if denominator and denominator != 0:
                self._state = round(numerator / denominator, 2)
            else:
                self._state = 0

        elif self._operation == "battery_time":
            capacity_ah = self._sensor_values.get("batcapacity", 0)
            voltage = self._sensor_values.get("vbat", 0)
            load_watts = self._sensor_values.get("pload", 0)
            battery_flow = self._sensor_values.get("batteryflow_live", 0)
            soc = self._sensor_values.get("soc", 0)
            pv_power = self._sensor_values.get("pall", 0)

            if capacity_ah > 0 and voltage > 0 and soc > 0:
                usable_energy_wh = (capacity_ah * voltage) * (soc / 100)
                net_load = max(load_watts - pv_power, 0)
                adjusted_load = net_load - battery_flow

                if adjusted_load > 0:
                    self._state = round(usable_energy_wh / adjusted_load, 2)
                else:
                    self._state = "Charging"

                # Calculate attributes
                self._attr_extra_state_attributes = {
                    "calculated_kwh_storage_total": round(capacity_ah * voltage / 1000, 2),
                    "calculated_kwh_left": round((capacity_ah * voltage * (soc / 100)) / 1000, 2),
                }

                # Calculate time battery empty
                if adjusted_load > 0:
                    hours_remaining = usable_energy_wh / adjusted_load
                    current_time = datetime.now()
                    empty_time = current_time + timedelta(hours=hours_remaining)

                    self._attr_extra_state_attributes.update({
                        "time_battery_empty": empty_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "human_readable_time_left": f"{int(hours_remaining)} hours, {int((hours_remaining - int(hours_remaining)) * 60)} minutes"
                    })
            else:
                self._state = "Unavailable"
                self._attr_extra_state_attributes = {
                    "calculated_kwh_storage_total": "Unavailable",
                    "calculated_kwh_left": "Unavailable",
                    "time_battery_empty": "Unavailable",
                    "human_readable_time_left": "Unavailable"
                }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # Get our source sensor IDs using the entry ID format
        source_entity_ids = {
            f"sensor.{self._formatted_id}_{sensor.lower()}": sensor
            for sensor in self._source_sensors
        }

        for entity_id in source_entity_ids.keys():
            # Check if this event matches one of our source sensors
             if entity_id in self.coordinator.entities:
                value = self.coordinator.entities[entity_id]
                if value is not None:
                    sensor_name = source_entity_ids[entity_id]
                    self._sensor_values[sensor_name] = float(value)

                    # LOGGER.debug(
                    #     f"Updated {sensor_name} value to {value} for calculated sensor {self.entity_id}"
                    # )

                    self._calculate_state()
                    self.throttled_async_write_ha_state()

class TemperatureSensor(MonitorMySolarEntity, SensorEntity):
    def __init__(self, sensor_info, hass, entry, bank_name, dongle_id):
        """Initialize the temperature sensor."""
        LOGGER.debug(f"Initializing sensor with info: {sensor_info}")
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id
        self._device_id = dongle_id
        self._sensor_type = sensor_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id = f"sensor.{self._device_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")

       

        super().__init__(self.coordinator)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def state_class(self):
        return self.sensor_info.get("state_class")

    @property
    def unit_of_measurement(self):
        if self.hass.config.units is US_CUSTOMARY_SYSTEM:
            return UnitOfTemperature.FAHRENHEIT
        else:
            return UnitOfTemperature.CELSIUS

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")
    
    @property
    def suggested_display_precision(self):
        """Return the suggested display precision for energy sensors."""
        if self.device_class == SensorDeviceClass.ENERGY:
            return 2
        return None

    @property
    def last_reset(self):
        """Return the time when the sensor was last reset (midnight)."""
        if self.state_class == "total":
            return datetime.min
        return None

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                # Default state to value sent in.
                self._state = (
                    round(value, 2) if isinstance(value, (float, int)) else value
                )
                # Check for HA config values and convert if neccessary.
                if self.hass.config.units is US_CUSTOMARY_SYSTEM:
                    # Const defines Celsius but HA should show Fahrenheit.
                    if UnitOfTemperature.FAHRENHEIT != self.sensor_info.get("unit_of_measurement"):
                        self._state = (
                            round( (((value)*9/5)+32), 2 ) if isinstance(value, (float, int)) else value
                        )
                else:
                    # Const defines Fahrenheit but HA should show Celsius.
                    if UnitOfTemperature.CELSIUS != self.sensor_info.get("unit_of_measurement"):
                        self._state = (
                            round( ((value)-32/(9/5)), 2 ) if isinstance(value, (float, int)) else value
                        )
                LOGGER.debug(f"Sensor {self.entity_id} state updated to {self._state}")
                self.throttled_async_write_ha_state()

class CombinedParallelSensor(MonitorMySolarEntity, SensorEntity):
    """Sensor that combines values from multiple dongles."""
    
    def __init__(self, sensor_info, hass, entry, dongle_ids):
        """Initialize the combined parallel sensor."""
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_ids = dongle_ids
        self._virtual_id = "combined_parallel"
        self._formatted_dongle_id = "combined"
        self._sensor_type = sensor_info["unique_id"]
        self.entity_id = f"sensor.{self._formatted_dongle_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        
        # Get calculation info
        self._calculation = sensor_info.get("calculation", {})
        self._operation = self._calculation.get("operation")
        self._source_entity = self._calculation.get("source_entity")
        self._source_values = {}
        
        # Track source entities that we need to monitor
        self._tracked_entities = []
        for dongle_id in dongle_ids:
            formatted_id = self.coordinator.get_formatted_dongle_id(dongle_id)
            source_entity_id = f"sensor.{formatted_id}_{self._source_entity}"
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
        def async_state_changed_listener(event: Event[EventStateChangedData]) -> None:
            """Handle entity state changes."""
            if (new_state := event.data["new_state"]) is None:
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
        """Calculate the combined state based on source entities."""
        # Filter out None values
        values = [v for v in self._source_values.values() if v is not None]
        
        if not values:
            LOGGER.debug(f"No values available for combined sensor {self._name}")
            self._state = None
            self.throttled_async_write_ha_state()
            return
            
        if self._operation == "addition":
            self._state = sum(values)
        elif self._operation == "average":
            self._state = sum(values) / len(values)
        else:
            LOGGER.warning(f"Unknown operation {self._operation} for combined sensor {self._name}")
            return
            
        # Round to 2 decimal places
        if isinstance(self._state, float):
            self._state = round(self._state, 2)
            
        self.throttled_async_write_ha_state()
    
    async def _initialize_state(self):
        """Initialize the state based on current source entity states."""
        await asyncio.sleep(2)  # Give entities time to load
        
        for entity_id in self._tracked_entities:
            state = self.hass.states.get(entity_id)
            if state and state.state not in [STATE_UNKNOWN, "unavailable"]:
                try:
                    value = float(state.state)
                    self._source_values[entity_id] = value
                except (ValueError, TypeError):
                    LOGGER.debug(f"Could not parse state for {entity_id}: {state.state}")
        
        await self._update_combined_state()
        
    @property
    def name(self):
        return self._name
        
    @property
    def unique_id(self):
        return self._unique_id
        
    @property
    def state(self):
        return self._state
        
    @property
    def state_class(self):
        return self.sensor_info.get("state_class")
        
    @property
    def unit_of_measurement(self):
        return self.sensor_info.get("unit_of_measurement")
        
    @property
    def device_class(self):
        return self.sensor_info.get("device_class")
    
    @property
    def suggested_display_precision(self):
        """Return the suggested display precision for energy sensors."""
        if self.device_class == SensorDeviceClass.ENERGY:
            return 2
        return None
        
    @property
    def available(self):
        # At least one source value should be available
        return any(v is not None for v in self._source_values.values())
        
    @property
    def extra_state_attributes(self):
        """Return extra attributes about the combined sensor."""
        # Format the dongle values for display
        dongle_values = {}
        for entity_id, value in self._source_values.items():
            # Extract dongle ID from entity_id (e.g., sensor.dongle_12_34_56_78_90_12_pall)
            parts = entity_id.split('.')[-1].split('_')
            if len(parts) >= 6:  # dongle_XX_XX_XX_XX_XX + setting name
                dongle_id = '_'.join(parts[:6]).replace('_', ':')
                dongle_values[f"{dongle_id}"] = str(value) if value is not None else "unknown"
        
        return {
            **dongle_values,
            "source_entities": self._tracked_entities,
            "operation": self._operation
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
        
    @callback
    def _handle_coordinator_update(self) -> None:
        """Override to prevent looking for combined entity in coordinator."""
        # Combined entities don't receive direct MQTT updates
        # They only update based on their source entities
        pass


class SyncStatusSensor(MonitorMySolarEntity, SensorEntity):
    """Sensor that shows the synchronization status of multiple inverters."""
    
    def __init__(self, hass, entry: MonitorMySolarEntry, dongle_ids):
        """Initialize the sync status sensor."""
        self.coordinator = entry.runtime_data
        self._name = "Inverter Sync Status"
        self._unique_id = f"{entry.entry_id}_sync_status".lower()
        self._state = "unknown"
        self._dongle_ids = dongle_ids
        self._virtual_id = "combined_parallel"
        self._formatted_dongle_id = "combined"
        self.entity_id = f"sensor.{self._formatted_dongle_id}_sync_status"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        
        # Sync status tracking
        self._total_settings = 0
        self._out_of_sync_count = 0
        self._last_check_time = None
        self._sync_details = {}  # {setting_id: {dongle_id: value}}
        self._monitored_settings = {}  # {unique_id: entity_type}
        
        # Get entity configuration for monitoring
        inverter_brand = self.coordinator.inverter_brand
        brand_entities = ENTITIES.get(inverter_brand, {})
        
        # Build list of settings to monitor
        monitored_types = ["switch", "number", "select", "time", "time_hhmm"]
        for entity_type in monitored_types:
            if entity_type not in brand_entities:
                continue
                
            for bank_name, entities in brand_entities[entity_type].items():
                # Skip combined entities
                if bank_name == "combined":
                    continue
                    
                for entity_config in entities:
                    unique_id = entity_config["unique_id"]
                    self._monitored_settings[unique_id] = entity_type
        
        self._total_settings = len(self._monitored_settings)
        
        super().__init__(self.coordinator)
        
        # Start periodic sync status check
        self.hass.async_create_task(self._start_monitoring())
    
    async def _start_monitoring(self):
        """Start monitoring sync status."""
        # Initial delay to let entities load
        await asyncio.sleep(10)
        
        # Initial check
        await self._check_sync_status()
        
        # Set up periodic check every 30 seconds
        while True:
            await asyncio.sleep(30)
            await self._check_sync_status()
    
    async def _check_sync_status(self):
        """Check the sync status of all monitored settings."""
        self._last_check_time = datetime.now().isoformat()
        self._sync_details = {}
        self._out_of_sync_count = 0
        
        for unique_id, entity_type in self._monitored_settings.items():
            setting_values = {}
            
            # Get values from all dongles for this setting
            for dongle_id in self._dongle_ids:
                formatted_id = self.coordinator.get_formatted_dongle_id(dongle_id)
                
                # Determine entity ID based on type
                if entity_type == "time_hhmm":
                    entity_id = f"time.{formatted_id}_{unique_id.lower()}"
                else:
                    entity_id = f"{entity_type}.{formatted_id}_{unique_id.lower()}"
                
                state = self.hass.states.get(entity_id)
                if state and state.state not in [STATE_UNKNOWN, "unavailable"]:
                    setting_values[dongle_id] = state.state
                else:
                    setting_values[dongle_id] = "unknown"
            
            self._sync_details[unique_id] = setting_values
            
            # Check if values are different (excluding unknowns)
            known_values = [v for v in setting_values.values() if v != "unknown"]
            if known_values and len(set(known_values)) > 1:
                self._out_of_sync_count += 1
        
        # Update state
        if self._out_of_sync_count == 0:
            self._state = "synced"
        else:
            self._state = f"{self._out_of_sync_count} unsynced"
        
        self.throttled_async_write_ha_state()
        LOGGER.debug(f"Sync status check complete: {self._out_of_sync_count} out of sync settings")
    
    @property
    def name(self):
        return self._name
        
    @property
    def unique_id(self):
        return self._unique_id
        
    @property
    def state(self):
        return self._state
        
    @property
    def icon(self):
        if self._state == "synced":
            return "mdi:check-circle"
        elif self._state == "unknown":
            return "mdi:help-circle"
        else:
            return "mdi:alert-circle"
        
    @property
    def available(self):
        return True
        
    @property
    def extra_state_attributes(self):
        """Return detailed sync status attributes."""
        attributes = {
            "last_check": self._last_check_time,
            "total_settings": self._total_settings,
            "out_of_sync_count": self._out_of_sync_count,
            "sync_enabled": self.coordinator.get_sync_settings_enabled()
        }
        
        # Create sync status grid
        if self._sync_details:
            # Create header row with dongle IDs
            grid_data = {}
            
            # Group settings by their sync status
            synced_settings = {}
            unsynced_settings = {}
            
            for setting_id, values in self._sync_details.items():
                # Get all non-unknown values
                known_values = {k: v for k, v in values.items() if v != "unknown"}
                
                if not known_values:
                    continue
                    
                # Check if all known values are the same
                unique_values = set(known_values.values())
                if len(unique_values) == 1:
                    synced_settings[setting_id] = values
                else:
                    unsynced_settings[setting_id] = values
            
            # Add unsynced settings first
            if unsynced_settings:
                attributes["unsynced_settings"] = {}
                for setting_id, values in unsynced_settings.items():
                    row = {}
                    for dongle_id, value in values.items():
                        # Format dongle ID for display
                        display_id = dongle_id.split('-')[1] if '-' in dongle_id else dongle_id
                        row[display_id] = f"❌ {value}"
                    attributes["unsynced_settings"][setting_id] = row
            
            # Add synced settings count
            attributes["synced_settings_count"] = len(synced_settings)
            
            # Optionally show some synced settings (first 5)
            if synced_settings:
                attributes["synced_settings_sample"] = {}
                for i, (setting_id, values) in enumerate(synced_settings.items()):
                    if i >= 5:  # Only show first 5
                        break
                    row = {}
                    for dongle_id, value in values.items():
                        display_id = dongle_id.split('-')[1] if '-' in dongle_id else dongle_id
                        row[display_id] = f"✅ {value}"
                    attributes["synced_settings_sample"][setting_id] = row
        
        return attributes
        
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
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Override to prevent looking for entity in coordinator."""
        # This sensor doesn't receive direct MQTT updates
        pass
