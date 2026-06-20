from datetime import datetime, timedelta
import asyncio
from homeassistant.components.time import TimeEntity
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

    entities = []

    # Loop through each dongle ID
    for dongle_id in dongle_ids:
        firmware_code = coordinator.get_firmware_code(dongle_id)
        
        # Only create entities if we have a firmware code
        if not firmware_code:
            LOGGER.debug(f"Skipping entity creation for {dongle_id} - no firmware code available yet")
            continue
        
        # Setup Time entities
        time_config = brand_entities.get("time", {})
        for bank_name, time_entities in time_config.items():
            for time_entity in time_entities:
                allowed_firmware_codes = time_entity.get("allowed_firmware_codes", [])
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
                
                entities.append(InverterTime(time_entity, hass, entry, dongle_id))

    async_add_entities(entities, True)

class InverterTime(MonitorMySolarEntity, TimeEntity):
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, dongle_id):
        """Initialize the Time entity."""
        LOGGER.debug(f"Initializing Time entity with info: {entity_info} for dongle {dongle_id}")
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{dongle_id}_{entity_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._entity_type = entity_info["unique_id"]
        self.entity_id = self.coordinator.build_entity_id("time", self._dongle_id, self._entity_type)
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._last_mqtt_update = None
        self._debounce_task = None
        self._user_initiated_change = False
        self._previous_state = None

        super().__init__(self.coordinator)

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
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer, self.entity_info.get("device_group"))

    async def async_set_value(self, value):
        """Handle user input and send to MQTT."""
        now = datetime.now()

        # Check if entity should be available based on conditional settings
        availability_info = self.coordinator.get_entity_availability_info(self._dongle_id, self._entity_type)
        if not availability_info["available"] and availability_info["reason"]:
            raise HomeAssistantError(availability_info["reason"])

        # Check if the state has changed
        if self._state == value or self._state is None:
            LOGGER.debug(f"No change in state for {self.entity_id}. Skipping MQTT update.")
            return

        # Debounce logic to delay the MQTT update and prevent multiple messages
        if self._debounce_task:
            self._debounce_task.cancel()

        async def debounce():
            await asyncio.sleep(1)
            if self._last_mqtt_update and (now - self._last_mqtt_update).total_seconds() < 1:
                LOGGER.debug(f"Skipping MQTT update for {self.entity_id} due to rate limiting")
                return

            LOGGER.info(f"Setting time value for {self.entity_id} to {value}")
            self._previous_state = self._state
            self._user_initiated_change = True
            self.update_state(value)
            success = await self.coordinator.mqtt_handler.send_update(
                self._dongle_id,
                self.entity_info["unique_id"],
                value.isoformat(),
                self,
            )
            if not success:
                self.revert_state()

        self._debounce_task = asyncio.create_task(debounce())

    @callback
    def update_state(self, value):
        """Update the state without triggering MQTT (e.g., from MQTT message)."""
        if self._state != value:
            self._state = value
            self._last_mqtt_update = datetime.now()
            LOGGER.debug(f"Time {self.entity_id} state updated to {value}")
            # Schedule state update on the main thread
            self.hass.loop.call_soon_threadsafe(self.throttled_async_write_ha_state)

    def revert_state(self):
        """Revert to the previous state."""
        self._user_initiated_change = False
        if self._previous_state is not None:
            self._state = self._previous_state
        self.hass.loop.call_soon_threadsafe(self.throttled_async_write_ha_state)

    def clear_user_initiated_flag(self):
        """Clear the user-initiated change flag when MQTT response is successful."""
        LOGGER.debug(f"Time {self.entity_id}: Clearing user_initiated flag after successful MQTT response")
        self._user_initiated_change = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                # If this is a user-initiated change, don't override with stale coordinator data
                if self._user_initiated_change:
                    if value == self._state:
                        LOGGER.debug(f"Time {self.entity_id}: Coordinator data matches user selection, clearing user_initiated flag")
                        self._user_initiated_change = False
                    else:
                        LOGGER.debug(f"Time {self.entity_id}: Ignoring coordinator update during user-initiated change (coordinator: {value}, user: {self._state})")
                        return
                self.update_state(value)
                self.throttled_async_write_ha_state()
