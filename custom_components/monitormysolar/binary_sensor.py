"""Battery status binary sensors."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.const import (
    STATE_UNKNOWN,
)
from homeassistant.helpers.reload import async_setup_reload_service
from .const import DOMAIN, BATTERY_STATUS_MAP, ENTITIES, PLATFORMS, LOGGER
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

async def async_setup_entry(
    hass: HomeAssistant,
    entry: MonitorMySolarEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors based on a config entry."""
    coordinator = entry.runtime_data
    inverter_brand = coordinator.inverter_brand
    
    brand_entities = ENTITIES.get(inverter_brand, {})
    sensors_config = brand_entities.get("binary_sensor", {})  # We're still using the sensor config
    
    entities = []
    
    for bank_name, sensors in sensors_config.items():
        for sensor in sensors:
            if bank_name == "battery":
                entities.append(
                    BatteryStatusBinarySensor(sensor, hass, entry)
                )
    
    async_add_entities(entities, True)


class BatteryStatusBinarySensor(MonitorMySolarEntity, BinarySensorEntity):
    """Binary sensor for battery charge/discharge status."""

    def __init__(self, sensor_info, hass, entry):
        """Initialize the binary sensor."""
        self.coordinator = entry.runtime_data
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = self.coordinator.dongle_id
        self._status_type = sensor_info.get("status_type")
        self.entity_id = f"binary_sensor.{self._dongle_id}_{sensor_info['unique_id'].lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._parent_sensor = sensor_info.get("parent_sensor")

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
    def state(self):
        """Return the state of the binary sensor."""
        return "Allowed" if self._state else "Forbidden"

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
                LOGGER.warning(f"entity_id: {self.entity_id}")
                LOGGER.warning(f"parent_sensor: {self._parent_sensor}")
                # Check if this update is for our parent sensor (BatStatusINV)
                # if event_entity_id.endswith(self._parent_sensor.lower()):
                #     try:
                #         status_value = str(int(value)).zfill(2)
                #         if status_value in BATTERY_STATUS_MAP:
                #             self._state = BATTERY_STATUS_MAP[status_value][self._status_type]
                #             self.async_write_ha_state()
                #     except ValueError:
                #         LOGGER.debug(f"Invalid battery status value: {value}")