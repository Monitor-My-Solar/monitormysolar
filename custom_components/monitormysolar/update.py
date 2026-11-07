# custom_components/monitormysolar/update.py
"""Update entity for MonitorMySolar.

This module provides firmware update functionality with:
- Automatic update checks every 6 hours
- Manual update checks via the entity UI
- Real-time progress tracking during updates
- Release notes display
- Support for stable and beta versions: every dongle gets a "Firmware" entity
  on the stable track and a "Firmware Beta" entity on the beta track. The beta
  entity is enabled by default only when the "Show beta firmware updates"
  option is on; otherwise it sits disabled in the entity registry, one click
  away.

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
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN, ENTITIES, LOGGER, CONF_USE_BETA, DEFAULT_USE_BETA, fw_version_is_newer
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

# How long to wait for the dongle to ACK the OTA admin command, and the overall
# ceiling on watching progress before we stop monitoring (the dongle reboots into
# the new firmware and reports a final result on <id>/ota/result).
OTA_ACK_TIMEOUT = 30  # seconds to wait for <id>/admin/response
OTA_OVERALL_TIMEOUT = 600  # seconds to watch progress/result before giving up

# The update server publishes one channel per chip. The bare /version endpoint is
# the legacy ESP32-C6 channel, so an ESP32-S3 dongle checked against it was
# offered the C6 build and never saw its own.
UPDATE_URL_BASE = "https://monitoring.monitormy.solar/version"
UPDATE_URLS = {"s3": f"{UPDATE_URL_BASE}/s3", "c6": f"{UPDATE_URL_BASE}/c6"}
UPDATE_CHECK_INTERVAL = timedelta(hours=6)  # Check every 6 hours

async def async_setup_entry(hass: HomeAssistant, entry: MonitorMySolarEntry, async_add_entities) -> None:
    """Set up update entities."""
    coordinator = entry.runtime_data
    dongle_ids = coordinator._dongle_ids
    
    # Fetch the latest firmware per chip channel. At setup a dongle may not have
    # published /status yet, so its chip is unknown — fetch both channels and let
    # each entity read the one its dongle resolves to.
    await _fetch_server_versions(coordinator, UPDATE_URLS.keys())

    entities = []

    # One stable and one beta update entity per dongle.
    show_beta = entry.data.get(CONF_USE_BETA, DEFAULT_USE_BETA)
    for dongle_id in dongle_ids:
        entities.append(DongleFirmwareUpdate(hass, entry, dongle_id, track="prod"))
        beta = DongleFirmwareUpdate(hass, entry, dongle_id, track="beta")
        entities.append(beta)
        if show_beta:
            _enable_if_integration_disabled(hass, beta.unique_id)

    if entities:
        async_add_entities(entities)


def _enable_if_integration_disabled(hass: HomeAssistant, unique_id: str) -> None:
    """Re-enable a beta entity this integration registered disabled.

    `entity_registry_enabled_default` only counts the first time an entity is
    registered, so a user who turns the beta option on later would never see
    the entity. A user who disabled it themselves is left alone.
    """
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("update", DOMAIN, unique_id)
    if not entity_id:
        return
    entry = registry.async_get(entity_id)
    if entry and entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION:
        registry.async_update_entity(entity_id, disabled_by=None)
        
async def _fetch_server_versions(coordinator, chips) -> None:
    """Fetch the latest firmware versions for the given chip channels ("s3"/"c6")."""
    try:
        async with aiohttp.ClientSession() as session:
            for chip in chips:
                url = UPDATE_URLS.get(chip)
                if not url:
                    continue
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            server_data = await response.json()
                            coordinator.server_versions[chip] = server_data
                            LOGGER.debug(f"Server versions updated for {chip}: {server_data}")
                        else:
                            LOGGER.warning(
                                f"Failed to fetch {chip} server versions: HTTP {response.status}"
                            )
                except asyncio.TimeoutError:
                    LOGGER.warning(f"Timeout fetching {chip} server versions")
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
        track: str = "prod",
    ) -> None:
        """Initialize the update entity for one firmware track ("prod" or "beta")."""
        self.hass = hass
        self.coordinator = entry.runtime_data
        self._dongle_id = dongle_id
        self._track = track
        self._formatted_dongle_id = self.coordinator.get_formatted_dongle_id(dongle_id)
        # The stable entity keeps its historical unique_id / entity_id.
        suffix = "firmware_update" if track == "prod" else "firmware_update_beta"
        self._unique_id = f"{entry.entry_id}_{dongle_id}_{suffix}"
        self._manufacturer = "MonitorMySolar"
        self.entity_id = self.coordinator.build_entity_id("update", self._dongle_id, suffix)
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
        beta = " Beta" if self._track == "beta" else ""
        if self._attr_has_entity_name:
            # Multiple dongles - return just "Firmware"
            return f"Firmware{beta}"
        else:
            # Single dongle - return full name
            return f"Firmware{beta} Update"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def _chip(self) -> str:
        """Chip channel this dongle's builds come from ("s3" / "c6")."""
        return self.coordinator.dongle_chip(self._dongle_id)

    @property
    def _server_versions(self) -> dict:
        """The update-server response for this dongle's chip."""
        return (self.coordinator.server_versions or {}).get(self._chip) or {}

    @property
    def installed_version(self) -> str | None:
        """Version the dongle reports, as published (e.g. "4.5.0.87S3").

        The server publishes the same chip-suffixed form, so installed and
        latest read alike; the numeric compare in version_is_newer ignores
        the suffix either way.
        """
        version = self.coordinator.current_fw_versions.get(self._dongle_id)

        if version in [None, "", "Waiting...", "Unknown"]:
            return None

        return str(version)

    @property
    def latest_version(self) -> str | None:
        """Latest version available on this dongle's chip channel and track."""
        server_versions = self._server_versions

        if self._track == "beta":
            version = server_versions.get("betaFwVersion")
        else:
            version = server_versions.get("latestFwVersion")

        if version in [None, ""]:
            return None

        return str(version)

    @property
    def _show_beta(self) -> bool:
        """The "Show beta firmware updates" option."""
        return self.coordinator.entry.data.get(CONF_USE_BETA, DEFAULT_USE_BETA)

    @property
    def extra_state_attributes(self) -> dict:
        """Which chip channel and track the offered build comes from."""
        return {"chip": self._chip.upper(), "track": self._track}

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
            server_versions = self._server_versions
            key = "changelogBeta" if self._track == "beta" else "changelog"
            changelog = server_versions.get(key)
            
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
        track = self._track

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

        def _mark_acknowledged(detail: str) -> None:
            """The dongle has taken the command, whichever topic told us so."""
            if ack["received"]:
                return
            ack["received"] = True
            ack["ok"] = True
            ack["detail"] = detail
            loop.call_soon_threadsafe(ack_event.set)

        @callback
        def _on_response(msg):
            try:
                data = json.loads(msg.payload)
            except (ValueError, TypeError):
                return
            if data.get("cmd") != "ota":
                return
            # Match our request id when the dongle echoes one; an OTA reply
            # without an id is still ours (we only ever have one in flight).
            msg_id = data.get("id")
            if msg_id is not None and msg_id != request_id:
                return
            if ack["received"]:
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
            # Progress means the dongle took the command, even if its ACK on
            # the response topic was missed (it reboots straight after sending
            # it, and the subscription can race the publish).
            _mark_acknowledged("progress received")
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
            # A result implies the command was accepted; never fail on a missed ACK.
            _mark_acknowledged("result received")
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
            # Let the three subscriptions settle at the broker before the
            # command goes out; the dongle ACKs and reboots within a second.
            await asyncio.sleep(0.5)
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
        LOGGER.debug(f"Checking for firmware updates for {self._dongle_id} ({self._chip})")
        await _fetch_server_versions(self.coordinator, [self._chip])
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
        """Stable is always on; beta only when the user asked to see beta updates."""
        return self._track != "beta" or bool(self._show_beta)
    
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