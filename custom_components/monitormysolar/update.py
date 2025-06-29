# custom_components/monitormysolar/update.py
"""Update entity for MonitorMySolar.

This module provides firmware update functionality with:
- Automatic update checks every 6 hours
- Manual update checks via the entity UI
- Real-time progress tracking during updates
- Release notes display
- Support for stable and beta versions

The update entity will:
1. Check for updates automatically every 6 hours
2. Check when user clicks on the entity (via async_release_notes)
3. Display release notes from the server
4. Show progress during firmware installation
"""
from __future__ import annotations

import aiohttp
import asyncio
from datetime import timedelta
from homeassistant.components import mqtt
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature, UpdateDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN, ENTITIES, LOGGER
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

UPDATE_URL = "https://monitoring.monitormy.solar/version"
UPDATE_CHECK_INTERVAL = timedelta(hours=6)  # Check every 6 hours

async def async_setup_entry(hass: HomeAssistant, entry: MonitorMySolarEntry, async_add_entities) -> None:
    """Set up update entities."""
    coordinator = entry.runtime_data
    dongle_ids = coordinator._dongle_ids
    
    # Fetch latest firmware version from server
    await _fetch_server_versions(coordinator)

    entities = []
    
    # Create a firmware update entity for each dongle
    for dongle_id in dongle_ids:
        entities.append(
            DongleFirmwareUpdate(
                hass,
                entry,
                dongle_id
            )
        )

    if entities:
        async_add_entities(entities)
        
async def _fetch_server_versions(coordinator) -> None:
    """Fetch latest firmware versions from server."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(UPDATE_URL, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    server_data = await response.json()
                    coordinator.server_versions = server_data
                    LOGGER.debug(f"Server versions updated: {server_data}")
                else:
                    LOGGER.warning(f"Failed to fetch server versions: HTTP {response.status}")
    except asyncio.TimeoutError:
        LOGGER.warning("Timeout fetching server versions")
    except Exception as e:
        LOGGER.error(f"Failed to fetch server versions: {e}")


class DongleFirmwareUpdate(MonitorMySolarEntity, UpdateEntity):
    """Firmware update entity for MonitorMySolar dongle."""
    
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES | UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MonitorMySolarEntry,
        dongle_id: str,
    ) -> None:
        """Initialize the update entity."""
        self.hass = hass
        self.coordinator = entry.runtime_data
        self._dongle_id = dongle_id
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        self._unique_id = f"{entry.entry_id}_{dongle_id}_firmware_update"
        self._manufacturer = "MonitorMySolar"
        self.entity_id = f"update.{self._formatted_dongle_id}_firmware_update"
        self._attr_in_progress = False
        self._attr_progress = None
        self._unsubscribe_timer = None
        self._last_check = None
        
        super().__init__(self.coordinator)

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._dongle_id} Firmware"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def installed_version(self) -> str | None:
        """Version currently installed."""
        version = self.coordinator.current_fw_versions.get(self._dongle_id)
        
        if version in [None, "", "Waiting...", "Unknown"]:
            return None
            
        return str(version)

    @property
    def latest_version(self) -> str | None:
        """Latest version available."""
        server_versions = self.coordinator.server_versions or {}
        
        # Check if we should use beta version
        # You might want to add a config option for this later
        use_beta = False  # For now, default to stable
        
        if use_beta:
            version = server_versions.get("betaFwVersion")
        else:
            version = server_versions.get("latestFwVersion")
            
        if version in [None, ""]:
            return None
            
        return str(version)
    
    def release_notes(self) -> str | None:
        """Return the release notes."""
        try:
            server_versions = self.coordinator.server_versions or {}
            
            # Determine which changelog to show based on version
            latest = self.latest_version
            beta_version = server_versions.get("betaFwVersion")
            
            # If latest version matches beta, show beta changelog
            if latest and beta_version and latest == beta_version:
                changelog = server_versions.get("changelogBeta")
            else:
                # Otherwise show standard changelog
                changelog = server_versions.get("changelog")
            
            if not changelog:
                return None
            
            return str(changelog)
        except Exception as e:
            LOGGER.error(f"Error getting release notes: {e}")
            return None
    
    @property
    def in_progress(self) -> bool:
        """Return True if update is in progress."""
        return self._attr_in_progress
    
    @property
    def update_percentage(self) -> int | float | None:
        """Return update progress percentage."""
        return self._attr_progress
    
    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        """Install an update."""
        dongle_ip = self.coordinator.get_dongle_ip(self._dongle_id)
        if not dongle_ip:
            raise Exception("No IP address configured for this dongle. Please configure the dongle IP in the integration settings.")
        
        # Use the provided version or latest version
        target_version = version or self.latest_version
        
        if not target_version:
            raise Exception("No target version specified and no latest version available")
        
        LOGGER.info(f"Installing firmware version {target_version} on {self._dongle_id} at IP {dongle_ip}")
        
        # Set update in progress
        self._attr_in_progress = True
        self._attr_progress = 0
        self.async_write_ha_state()
        
        try:
            # First, trigger the update
            async with aiohttp.ClientSession() as session:
                update_url = f"http://{dongle_ip}/api/perform-update"
                payload = {
                    "update": "FW_update",
                    "fwVersion": target_version
                }
                
                LOGGER.debug(f"Sending update request to {update_url} with payload: {payload}")
                
                async with session.post(update_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        result = await response.text()
                        LOGGER.info(f"Update initiated successfully: {result}")
                        # Dongle will reboot, so we need to wait and monitor progress
                        await self._monitor_update_progress(dongle_ip)
                    else:
                        error_text = await response.text()
                        raise Exception(f"Update failed with status {response.status}: {error_text}")
                        
        except Exception as e:
            LOGGER.error(f"Error installing update: {e}")
            self._attr_in_progress = False
            self._attr_progress = None
            self.async_write_ha_state()
            raise
            
    async def _monitor_update_progress(self, dongle_ip: str) -> None:
        """Monitor update progress via WebSocket."""
        # Wait for dongle to reboot and start update
        await asyncio.sleep(10)
        
        ws_url = f"ws://{dongle_ip}/ws"
        retry_count = 0
        max_retries = 30  # 5 minutes with 10 second intervals
        
        while retry_count < max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(ws_url, timeout=aiohttp.ClientTimeout(total=300)) as ws:
                        LOGGER.info("Connected to dongle WebSocket for update monitoring")
                        
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    import json
                                    data = json.loads(msg.data)
                                    
                                    if data.get("event") == "ota_status":
                                        status = data.get("data", "")
                                        LOGGER.debug(f"OTA Status: {status}")
                                        
                                        # Parse progress from message
                                        if "Progress:" in status and "%" in status:
                                            import re
                                            match = re.search(r'(\d+)%', status)
                                            if match:
                                                progress = int(match.group(1))
                                                self._attr_progress = progress
                                                self.async_write_ha_state()
                                                
                                        # Check for completion
                                        if "Update complete" in status or "rebooting" in status:
                                            LOGGER.info("Update completed successfully")
                                            self._attr_in_progress = False
                                            self._attr_progress = 100
                                            self.async_write_ha_state()
                                            
                                            # Wait for dongle to reboot and update the firmware version
                                            await asyncio.sleep(30)  # Give dongle time to reboot
                                            
                                            # Force a refresh of the firmware version
                                            await self._refresh_firmware_version()
                                            return
                                            
                                        # Check for errors
                                        if "failed" in status.lower() or "error" in status.lower():
                                            raise Exception(f"Update failed: {status}")
                                            
                                except json.JSONDecodeError:
                                    LOGGER.debug(f"Non-JSON WebSocket message: {msg.data}")
                                    
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                LOGGER.error(f'WebSocket error: {ws.exception()}')
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                LOGGER.info("WebSocket closed")
                                break
                                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                retry_count += 1
                LOGGER.warning(f"WebSocket connection failed (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    await asyncio.sleep(10)
                else:
                    # Assume update completed if we can't connect after many retries
                    LOGGER.info("Could not monitor update progress, assuming success")
                    self._attr_in_progress = False
                    self._attr_progress = None
                    self.async_write_ha_state()
                    
                    # Wait additional time for dongle to fully reboot
                    await asyncio.sleep(60)
                    
                    # Force a refresh of the firmware version
                    await self._refresh_firmware_version()
                    return
                    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Set up periodic update checks
        async def _periodic_update_check(_):
            """Check for updates periodically."""
            await self._async_check_for_update()
        
        self._unsubscribe_timer = async_track_time_interval(
            self.hass, _periodic_update_check, UPDATE_CHECK_INTERVAL
        )
        
        LOGGER.debug(f"Set up periodic update check for {self._dongle_id} every {UPDATE_CHECK_INTERVAL}")
    
    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        if self._unsubscribe_timer:
            self._unsubscribe_timer()
        await super().async_will_remove_from_hass()
    
    async def _async_check_for_update(self) -> None:
        """Check for firmware updates."""
        LOGGER.debug(f"Checking for firmware updates for {self._dongle_id}")
        await _fetch_server_versions(self.coordinator)
        self._last_check = self.hass.loop.time()
        self.async_write_ha_state()
    
    async def async_release_notes(self) -> str | None:
        """Return the release notes and trigger update check if needed."""
        # Check for updates if we haven't checked recently
        if self._last_check is None or (self.hass.loop.time() - self._last_check) > 300:  # 5 minutes
            await self._async_check_for_update()
        
        return self.release_notes()
    
    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return True
    
    async def _refresh_firmware_version(self) -> None:
        """Refresh the firmware version after an update."""
        LOGGER.info(f"Refreshing firmware version for {self._dongle_id}")
        
        # Request the dongle to send its current firmware version
        try:
            await mqtt.async_publish(
                self.hass, 
                f"{self._dongle_id}/firmwarecode/request", 
                ""
            )
            LOGGER.debug(f"Sent firmware version request to {self._dongle_id}")
            
            # Wait a bit for the response
            await asyncio.sleep(5)
            
            # The coordinator will handle the response and update current_fw_versions
            # Force an update check to refresh latest version
            await self._async_check_for_update()
            
            LOGGER.info(f"Firmware version refreshed for {self._dongle_id}: {self.installed_version}")
            
        except Exception as e:
            LOGGER.error(f"Error refreshing firmware version: {e}")