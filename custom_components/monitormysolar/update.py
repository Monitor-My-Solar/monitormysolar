# custom_components/monitormysolar/update.py
"""Update entity for MonitorMySolar."""
from __future__ import annotations

import aiohttp
from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityFeature,
    UpdateDeviceClass,
)
from homeassistant.const import (
    STATE_UNKNOWN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import (
    async_track_state_change_event,
)
from .const import DOMAIN, ENTITIES, LOGGER
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

UPDATE_URL = "https://monitoring.monitormy.solar/version"

async def async_setup_entry(hass: HomeAssistant, entry: MonitorMySolarEntry, async_add_entities) -> None:
    """Set up update entities."""
    coordinator = entry.runtime_data
    inverter_brand = coordinator.inverter_brand
    dongle_ids = coordinator._dongle_ids

    # Fetch latest versions from server first
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(UPDATE_URL) as response:
                if response.status == 200:
                    server_data = await response.json()
                    coordinator.server_versions = server_data
                    LOGGER.debug(f"Update server returned: {server_data}")
                else:
                    LOGGER.error(f"Failed to fetch versions: {response.status}")
    except Exception as e:
        LOGGER.error(f"Error fetching versions: {e}")

    brand_entities = ENTITIES.get(inverter_brand, {})
    update_config = brand_entities.get("update", {})

    entities = []
    
    # Loop through each dongle ID
    for dongle_id in dongle_ids:
        # Create update entities for this dongle
        for bank_name, updates in update_config.items():
            for update in updates:
                LOGGER.debug(f"Creating update entity: {update['name']} for dongle {dongle_id}")
                try:
                    # Ensure the entity gets proper values from the coordinator for proper detection
                    update_entity = InverterUpdate(
                        hass,
                        entry,
                        update["name"],
                        update["unique_id"],
                        update["version_key"],
                        update["update_command"],
                        dongle_id
                    )
                    entities.append(update_entity)
                except Exception as e:
                    LOGGER.error(f"Error setting up update entity {update['name']} for dongle {dongle_id}: {e}")

    if entities:
        LOGGER.debug(f"Adding {len(entities)} update entities")
        async_add_entities(entities)
    else:
        LOGGER.debug("No update entities were created")


class InverterUpdate(MonitorMySolarEntity, UpdateEntity):
    """Update entity for MonitorMySolar."""

    # These class-level attributes ensure proper entity classification
    _attr_has_entity_name = True
    _attr_supported_features = UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MonitorMySolarEntry,
        name: str,
        unique_id: str,
        version_key: str,
        update_command: str,
        dongle_id: str,
    ) -> None:
        """Initialize the update entity."""
        self.coordinator = entry.runtime_data
        self.hass = hass
        self._name = name
        self._unique_id = f"{entry.entry_id}_{dongle_id}_{unique_id}"
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._version_key = version_key
        self._update_command = update_command
        self._manufacturer = entry.data.get("inverter_brand")
        self.entity_id = f"update.{self._formatted_dongle_id}_{unique_id.lower()}"
        
        # Set explicit attributes required for update entities
        self._attr_title = f"{name}"
        self._attr_in_progress = False

        super().__init__(self.coordinator)

        # Set initial versions
        self._attr_installed_version = self._get_installed_version()
        self._attr_latest_version = self._get_latest_version()
        self._attr_release_summary = self._get_release_notes()

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._name} ({self._dongle_id})"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    def _get_installed_version(self) -> str:
        """Get current installed version from domain data."""
        version = None
        if self._version_key == "UI_VERSION":
            version = self.coordinator.current_ui_versions.get(self._dongle_id)
        else:
            version = self.coordinator.current_fw_versions.get(self._dongle_id)
            
        # If we don't have a version yet, return a placeholder
        if version in [None, "", "Waiting..."]:
            LOGGER.debug(f"No {self._version_key} available yet for {self._dongle_id}")
            return "Unknown"
            
        # Ensure version follows semantic versioning format
        if not isinstance(version, str) or not version.count('.'):
            # Convert simple version numbers to proper format
            try:
                version = f"{version}.0.0"
            except (ValueError, TypeError):
                version = "1.0.0"  # Default fallback
            
        return version

    @property
    def installed_version(self) -> str:
        """Get current version."""
        return self._get_installed_version()

    def _get_latest_version(self) -> str | None:
        """Get latest version from server data."""
        server_versions = self.coordinator.server_versions or {}
        version = None
        
        if self._version_key == "UI_VERSION":
            version = server_versions.get("latestUiVersion")
        else:
            version = server_versions.get("latestFwVersion")
            
        # If we don't have a version yet, return None
        if version in [None, ""]:
            return None
            
        # Ensure version follows semantic versioning format
        if not isinstance(version, str) or not version.count('.'):
            # Convert simple version numbers to proper format
            try:
                version = f"{version}.0.0"
            except (ValueError, TypeError):
                return None
            
        return version

    def _get_release_notes(self) -> str | None:
        """Get release notes from server data."""
        server_versions = self.coordinator.server_versions or {}
        changelog = server_versions.get("changelog")
        if not changelog:
            return None

        if "UI:" in changelog and "FW:" in changelog:
            parts = changelog.split("FW:")
            ui_part = parts[0].replace("UI:", "").strip()
            fw_part = parts[1].strip()

            return ui_part if self._version_key == "UI_VERSION" else fw_part
        return changelog
        
    @property
    def latest_version(self) -> str | None:
        """Get latest version."""
        latest = self._get_latest_version()
        if latest is None or latest == "":
            return "Unknown"
        return latest

    @property
    def in_progress(self) -> bool:
        """Return True if an update is in progress."""
        return self._attr_in_progress

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                self._attr_installed_version = value
                
                # Update the appropriate version tracking in coordinator
                if self._version_key == "UI_VERSION":
                    self.coordinator.current_ui_versions[self._dongle_id] = value
                else:
                    self.coordinator.current_fw_versions[self._dongle_id] = value
                
                # If we got an update, we're no longer in progress
                self._attr_in_progress = False
                self.async_write_ha_state()

    async def async_install(
        self, version: str | None, backup: bool, **kwargs
    ) -> None:
        """Install an update."""
        LOGGER.debug(f"Install update called for {self.name}")
        # Set in_progress to True to show update is happening
        self._attr_in_progress = True
        self.async_write_ha_state()
        
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler:
            try:
                # Send the update command via MQTT
                await mqtt_handler.send_update(
                    self._dongle_id,
                    self._update_command,
                    1,
                    self
                )
                # Update will be marked complete when new version is received
            except Exception as e:
                LOGGER.error(f"Error installing update: {e}")
                # If there was an error, we're no longer in progress
                self._attr_in_progress = False
                self.async_write_ha_state()
