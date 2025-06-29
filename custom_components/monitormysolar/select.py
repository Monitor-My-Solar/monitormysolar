from homeassistant.components.select import SelectEntity
from homeassistant.core import callback
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
        
        # Process selects for this dongle
        for bank_name, selects in select_config.items():
            for select in selects:
                allowed_firmware_codes = select.get("allowed_firmware_codes", [])
                if not allowed_firmware_codes or firmware_code in allowed_firmware_codes:
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

    async def async_select_option(self, option):
        """Update the select option."""
        LOGGER.info(f"Setting select option for {self.entity_id} to {option}")
        self._state = option
        self.throttled_async_write_ha_state()



        bit_value = self._options.index(option)
        LOGGER.info(f"Setting Select value for {self.entity_id} to {option}")
        await self.coordinator.mqtt_handler.send_update(
            self._dongle_id,
            self.entity_info["unique_id"],
            bit_value,
            self,
        )

    def revert_state(self):
        """Revert to the previous state."""
        LOGGER.info(f"Reverting state for {self.entity_id} to {self._state}")
        # Schedule state revert on the main thread
        self.hass.loop.call_soon_threadsafe(self.throttled_async_write_ha_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                self._state = (
                    self._options[value]
                    if isinstance(value, int) and value < len(self._options)
                    else value
                )
                # Schedule state update on the main thread
                self.hass.loop.call_soon_threadsafe(self.throttled_async_write_ha_state)


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