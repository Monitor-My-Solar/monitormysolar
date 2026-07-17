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
import json
import uuid
from datetime import timedelta
from homeassistant.components import mqtt
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature, UpdateDeviceClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN, ENTITIES, LOGGER, CONF_USE_BETA, DEFAULT_USE_BETA, fw_version_is_newer
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

# How long to wait for the dongle to ACK the OTA admin command, and the overall
# ceiling on watching progress before we stop monitoring (the dongle reboots into
# the new firmware and reports a final result on <id>/ota/result).
OTA_ACK_TIMEOUT = 30  # seconds to wait for <id>/admin/response
OTA_OVERALL_TIMEOUT = 600  # seconds to watch progress/result before giving up

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
        self.entity_id = self.coordinator.build_entity_id("update", self._dongle_id, "firmware_update")
        self._attr_in_progress = False
        self._attr_progress = None
        self._unsubscribe_timer = None
        self._last_check = None
        
        super().__init__(self.coordinator)

    @property
    def device_info(self):
        return self.get_device_info(self._dongle_id, self._manufacturer, "Inverter")

    @property
    def name(self):
        """Return the name of the entity."""
        if self._attr_has_entity_name:
            # Multiple dongles - return just "Firmware"
            return "Firmware"
        else:
            # Single dongle - return full name
            return "Firmware Update"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @staticmethod
    def _strip_chip_suffix(version: str) -> str:
        """Strip the trailing chip designator (e.g. S3 / C6) from a version string.

        The dongle reports versions like "4.3.0.111S3" or "4.3.0C6", but the
        update server publishes the bare version ("4.3.0.111" / "4.3.0"). Without
        stripping the chip suffix the installed vs latest comparison never matches
        and HA would always show an update available. Removes a trailing run of
        letters+digits that isn't part of the dotted numeric version.
        """
        if not version:
            return version
        # Split on dots; the chip suffix is glued onto the last numeric segment,
        # e.g. "111S3" -> keep "111". Trim trailing chars from the last part once a
        # non-digit is hit.
        parts = version.split(".")
        last = parts[-1]
        trimmed = ""
        for ch in last:
            if ch.isdigit():
                trimmed += ch
            else:
                break
        parts[-1] = trimmed
        # Drop any now-empty trailing segment (e.g. version was just "4.3.0S3" with
        # nothing numeric after — shouldn't happen, but be safe).
        while parts and parts[-1] == "":
            parts.pop()
        return ".".join(parts)

    @property
    def installed_version(self) -> str | None:
        """Version currently installed (chip suffix stripped to match the server)."""
        version = self.coordinator.current_fw_versions.get(self._dongle_id)

        if version in [None, "", "Waiting...", "Unknown"]:
            return None

        return self._strip_chip_suffix(str(version))

    @property
    def latest_version(self) -> str | None:
        """Latest version available."""
        server_versions = self.coordinator.server_versions or {}

        if self._use_beta:
            version = server_versions.get("betaFwVersion")
        else:
            version = server_versions.get("latestFwVersion")

        if version in [None, ""]:
            return None

        return str(version)

    @property
    def _use_beta(self) -> bool:
        """Whether this install should track the beta firmware channel."""
        return self.coordinator.entry.data.get(CONF_USE_BETA, DEFAULT_USE_BETA)

    def version_is_newer(self, latest_version: str, installed_version: str) -> bool:
        """Offer an update only when the server version is strictly newer.

        HA's default comparison is an inequality, so a unit running a build
        NEWER than the server's published version (dev/beta units) would be
        offered a 'downgrade'. Numeric tuple compare instead. Deliberate
        consequence: a server-side rollback to an older version is not shown
        in HA — rollbacks are pushed via the /admin OTA command, which does
        not consult this comparison.
        """
        return fw_version_is_newer(latest_version, installed_version)
    
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
        """Install an update via the MQTT admin OTA command.

        Publishes {"cmd":"ota"} to <dongle_id>/admin and watches progress on
        <dongle_id>/ota/progress, finishing on <dongle_id>/ota/result. No dongle
        IP / HTTP / WebSocket involved — the whole flow is MQTT. Requires dongle
        firmware >= 4.3.0 (the /admin command surface).

        Version selection is by *track* only. Since firmware 4.3.0 the dongle's
        version is CI-stamped from the build (the build number in e.g.
        "4.3.0.111S3"), so HA never specifies a target version — it just asks for
        the current build on prod or beta. The `version` argument from HA is
        ignored.
        """
        track = "beta" if self._use_beta else "prod"

        request_id = uuid.uuid4().hex[:12]
        command = {"cmd": "ota", "id": request_id, "args": {"track": track}}

        LOGGER.info(
            f"Requesting OTA for {self._dongle_id}: track={track} (id={request_id})"
        )

        self._attr_in_progress = True
        self._attr_progress = 0
        self.async_write_ha_state()

        # Events/holders the MQTT callbacks fill in.
        ack = {"received": False, "ok": False, "detail": ""}
        ack_event = asyncio.Event()
        result = {"status": None, "detail": ""}
        result_event = asyncio.Event()
        loop = self.hass.loop

        @callback
        def _on_response(msg):
            try:
                data = json.loads(msg.payload)
            except (ValueError, TypeError):
                return
            if data.get("id") != request_id or data.get("cmd") != "ota":
                return
            ack["received"] = True
            ack["ok"] = data.get("status") == "ok"
            ack["detail"] = data.get("detail", "")
            loop.call_soon_threadsafe(ack_event.set)

        @callback
        def _on_progress(msg):
            # Ignore retained messages: a progress message retained from a previous
            # OTA is delivered immediately on subscribe and would jump the bar to a
            # stale value. Only act on live progress for this install.
            if getattr(msg, "retain", False):
                return
            try:
                data = json.loads(msg.payload)
            except (ValueError, TypeError):
                return
            # If the dongle echoes the request id on progress, honour it; otherwise
            # accept (the topic is dongle-specific and only subscribed during this
            # install).
            msg_id = data.get("id")
            if msg_id is not None and msg_id != request_id:
                return
            pct = data.get("progress")
            if isinstance(pct, (int, float)) and 0 <= pct <= 100:
                self._attr_progress = int(pct)
                self.async_write_ha_state()

        @callback
        def _on_result(msg):
            try:
                data = json.loads(msg.payload)
            except (ValueError, TypeError):
                return
            result["status"] = data.get("status")
            result["detail"] = data.get("detail", "")
            loop.call_soon_threadsafe(result_event.set)

        unsub_response = await mqtt.async_subscribe(
            self.hass, f"{self._dongle_id}/admin/response", _on_response
        )
        unsub_progress = await mqtt.async_subscribe(
            self.hass, f"{self._dongle_id}/ota/progress", _on_progress
        )
        unsub_result = await mqtt.async_subscribe(
            self.hass, f"{self._dongle_id}/ota/result", _on_result
        )

        # Suppress snapshot ({"what":"all"}) requests for the whole OTA window.
        # In OTA mode the dongle has no snapshot queue allocated, so the
        # reconnect-triggered snapshot request would crash it into a reboot loop.
        self.coordinator.set_ota_in_progress(self._dongle_id, True)

        try:
            await mqtt.async_publish(
                self.hass, f"{self._dongle_id}/admin", json.dumps(command), qos=1
            )

            # 1. Wait for the dongle to ACK the command.
            try:
                await asyncio.wait_for(ack_event.wait(), timeout=OTA_ACK_TIMEOUT)
            except asyncio.TimeoutError:
                raise Exception(
                    "Dongle did not acknowledge the OTA command. "
                    "Ensure the dongle is online and running firmware 4.3.0 or newer."
                )
            if not ack["ok"]:
                raise Exception(f"Dongle rejected the OTA command: {ack['detail'] or 'unknown error'}")

            LOGGER.info(f"OTA accepted by {self._dongle_id}: {ack['detail']}")

            # 2. Watch progress until the dongle reboots into the new firmware and
            #    publishes a final result (or we hit the overall ceiling).
            try:
                await asyncio.wait_for(result_event.wait(), timeout=OTA_OVERALL_TIMEOUT)
            except asyncio.TimeoutError:
                # The dongle reboots mid-update and may reconnect after our ceiling.
                # Don't hard-fail: clear progress and let the post-boot version
                # refresh confirm the outcome.
                LOGGER.warning(
                    f"No OTA result from {self._dongle_id} within {OTA_OVERALL_TIMEOUT}s; "
                    "the dongle may still be updating/rebooting."
                )
                await self._refresh_firmware_version()
                return

            # Accept both "success" (the documented OTA result token) and "ok"
            # (the admin-command ACK vocabulary) so a firmware that reuses "ok" on
            # the result topic isn't reported as a spurious failure.
            if result["status"] in ("success", "ok"):
                LOGGER.info(f"OTA succeeded for {self._dongle_id}")
                self._attr_progress = 100
                self.async_write_ha_state()
                await self._refresh_firmware_version()
            else:
                raise Exception(f"OTA failed: {result['detail'] or 'unknown error'}")

        except Exception as e:
            LOGGER.error(f"Error installing update for {self._dongle_id}: {e}")
            raise
        finally:
            unsub_response()
            unsub_progress()
            unsub_result()
            self.coordinator.set_ota_in_progress(self._dongle_id, False)
            if ack["ok"]:
                # Reconnect snapshot triggers (availability online, boot-count
                # change, data-gap recovery) that fired mid-OTA were suppressed
                # and won't refire, so refresh the dongle's state ourselves now
                # that OTA mode is over. request_snapshot swallows publish errors.
                await self.coordinator.request_snapshot(
                    self._dongle_id,
                    self.coordinator.current_fw_versions.get(self._dongle_id, ""),
                    force=True,
                )
            self._attr_in_progress = False
            self._attr_progress = None
            self.async_write_ha_state()
                    
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