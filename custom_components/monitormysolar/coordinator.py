from __future__ import annotations
import json
import time
from typing import Any, cast, Set, List, Dict
from propcache import cached_property

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers.event import (
    async_call_later,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .mqttHandeler import MQTTHandler

from .const import (
    DOMAIN,
    ENTITIES,
    LOGGER,
    PLATFORMS,
)

# Forward reference type definition
class MonitorMySolar(DataUpdateCoordinator[None]):
    pass

type MonitorMySolarEntry = ConfigEntry[MonitorMySolar]

class MonitorMySolar(DataUpdateCoordinator[None]):

    def __init__(
            self,
            hass: HomeAssistant,
            entry: MonitorMySolarEntry,
        ) -> None:

        """Initialize the Coordinator."""
        self.hass = hass
        self.entry = entry
        self.mqtt_handler = {}
        
        # Get dongle data from config entry (new structure with bundle tracking)
        self._dongle_data: List[Dict[str, Any]] = entry.data.get("dongle_data", [])
        
        # Fallback to old structure for backward compatibility
        if not self._dongle_data:
            # Create dongle_data from old structure
            dongle_ids = entry.data.get("dongle_ids", [entry.data.get("dongle_id")])
            self._dongle_data = []
            for i, dongle_id in enumerate(dongle_ids):
                self._dongle_data.append({
                    "dongle_id": dongle_id,
                    "is_master": i == 0,  # First dongle is master
                    "is_slave": i > 0,    # Others are slaves
                    "is_gridboss": False,
                    "is_gridboss_slave": False,
                    "gridboss_bundle": None
                })

        # Extract dongle IDs (dongle IP was removed in 4.0.0 — OTA and all admin
        # actions go over MQTT now, so no IP is needed).
        self._dongle_ids: List[str] = [d["dongle_id"] for d in self._dongle_data]

        # Initialize per-dongle data structures
        # Load saved firmware codes from config entry
        saved_firmware_codes = entry.data.get("firmware_codes", {})
        self._firmware_codes: Dict[str, str] = {}
        for dongle_id in self._dongle_ids:
            self._firmware_codes[dongle_id] = saved_firmware_codes.get(dongle_id)
        self.entities: Dict[str, Any] = {}
        self.current_fw_versions: Dict[str, str] = {dongle_id: "" for dongle_id in self._dongle_ids}
        # self.current_ui_versions: Dict[str, str] = {dongle_id: "" for dongle_id in self._dongle_ids}  # Commented out - UI update entity removed
        self._mqtt_unsubscribe_callbacks: Dict[str, Any] = {}
        self._ignored_entity_suffixes: Set[str] = set()  # To track entities we've already logged about
        self._pending_dongles: List[str] = self._dongle_ids.copy()  # Track dongles still needing setup
        self.server_versions = {}
        self._sync_settings_enabled = False  # Track sync settings state
        self._setting_history = {}  # Track setting changes with timestamps
        self._max_history_entries = 100  # Limit history size per setting
        self._setup_errors = []  # Track errors during setup
        self._drop_dongle_id = entry.data.get("drop_dongle_id", False)  # Optional: omit dongle id from entity_ids (single-dongle only)
        self._snapshot_requested: Set[str] = set()  # Dongles we've requested a full snapshot from this session
        # Dongles currently doing an MQTT OTA update. While a dongle is in OTA
        # mode it has no snapshot queue allocated, so a {"what":"all"} request
        # crashes it into a reboot loop. Every snapshot path checks this set.
        self._ota_in_progress: Set[str] = set()
        self._dongle_availability: Dict[str, bool] = {}  # Track LWT online/offline per dongle
        self._dongle_boot_count: Dict[str, int] = {}  # Last-seen boot.count per dongle (detect silent reboots)
        # Recovery bookkeeping (monotonic seconds): last time we saw ANY message
        # from a dongle, and last time we sent it a recovery snapshot (for debounce).
        self._dongle_last_seen: Dict[str, float] = {}
        self._last_recovery_snapshot: Dict[str, float] = {}
        # A dongle that has been silent longer than this is considered "gone dark";
        # the next message it sends triggers a recovery snapshot.
        self._dongle_stale_after = 90.0
        # Don't send more than one recovery snapshot per dongle within this window.
        self._recovery_snapshot_debounce = 30.0
        self._has_gridboss = entry.data.get("has_gridboss", False)  # Track if GridBoss is enabled
        self._gridboss_dongle = entry.data.get("gridboss_dongle", "")  # Track which dongle is GridBoss
        self._last_fault_warning_data = {}  # Track last fault/warning data to prevent duplicate processing
        self._hass_startup_complete = False  # Track if Home Assistant has finished starting up
        self._smart_soc_volt_bits = {}  # Track SmartSOCVoltBits for each dongle
        self._smartload_bits = {}  # Track SmartLoad Bits for each dongle
        self._port_modes = {}  # Track Port Mode settings for each dongle

        # Self-write ledger for de-duplicating the FW >= 4.3.0 dual confirmation.
        # A HA write is acked on BOTH <dongle>/response (legacy, drives the
        # send lock + revert) AND <dongle>/setting/updated (durable echo). Both
        # carry the same value. We record what WE just wrote here; when the
        # matching /setting/updated echo arrives within the window we skip its
        # redundant refresh. Echoes for writes we DIDN'T make (Lux server, web
        # UI, HA TCP) have no ledger entry and still apply. Key: (dongle_id,
        # setting_suffix) -> (normalized_value, monotonic_ts).
        self._self_write_ledger: Dict[tuple, tuple] = {}
        self._self_write_dedup_window = 10.0  # seconds

        # Battery extended data tracking
        self._battery_data: Dict[str, Dict] = {}  # {dongle_id: battery payload data}
        self._battery_entities_created: Set[str] = set()  # Track which dongles have battery entities
        self._battery_async_add_entities = None  # Callback for adding battery sensor entities
        
        # Track charge/discharge control settings for standard units
        self._charge_control_settings = {}  # Track ubBatChgcontrol for each dongle
        self._discharge_control_settings = {}  # Track ubBatDischgControl for each dongle
        self._charge_type_settings = {}  # Track ACChargeType for each dongle

        super().__init__(
            hass,
            LOGGER,
            name="MonitorySolar Coordinator",
            setup_method=self.async_setup
        )

    def get_formatted_dongle_id(self, dongle_id: str) -> str:
        """Convert a dongle ID to the formatted version used in entity IDs."""
        return dongle_id.lower().replace("-", "_").replace(":", "_")

    @staticmethod
    def parse_fw_version(version: str):
        """Parse a dongle /status version string into a (major, minor, patch) tuple.

        Versions look like '4.3.0.111S3' — major.minor.patch.build + chip suffix.
        Returns the first three dotted integers, or None if they can't be parsed.
        """
        if not version:
            return None
        parts = version.strip().split(".")
        nums = []
        for part in parts[:3]:
            # Strip any trailing non-digits (e.g. the 'S3' chip suffix on the build field).
            digits = ""
            for ch in part:
                if ch.isdigit():
                    digits += ch
                else:
                    break
            if not digits:
                return None
            nums.append(int(digits))
        if len(nums) < 3:
            return None
        return tuple(nums)

    def _needs_snapshot(self, version: str) -> bool:
        """Whether a dongle on this firmware needs an explicit full-data snapshot.

        FW >= 4.3.0 only streams change-data, so it must be asked for a full
        snapshot on connect. Fail-open: if the version can't be parsed, request
        anyway — older firmware simply ignores the snapshot topic.
        """
        parsed = self.parse_fw_version(version)
        if parsed is None:
            return True
        return parsed >= (4, 3, 0)

    def set_ota_in_progress(self, dongle_id: str, in_progress: bool) -> None:
        """Mark a dongle as (no longer) running an OTA update.

        While marked, all snapshot requests to it are suppressed: in OTA mode
        the dongle has no snapshot queue, and a {"what":"all"} request sends it
        into a reboot loop.
        """
        # getattr: test coordinators are built via __new__ and skip __init__.
        ota_set = getattr(self, "_ota_in_progress", None)
        if ota_set is None:
            ota_set = self._ota_in_progress = set()
        if in_progress:
            ota_set.add(dongle_id)
        else:
            ota_set.discard(dongle_id)

    def is_ota_in_progress(self, dongle_id: str) -> bool:
        """Whether a dongle is currently running an OTA update."""
        return dongle_id in getattr(self, "_ota_in_progress", ())

    async def request_snapshot(self, dongle_id: str, version: str = "", force: bool = False) -> None:
        """Ask a dongle for a full /input + /hold snapshot (once per session).

        Dongles on FW >= 4.3.0 only publish change-data, so without this the
        entities stay 'unknown' until each value happens to change. Gated to fire
        once per dongle per HA session unless force=True (e.g. a reconnect).
        """
        if self.is_ota_in_progress(dongle_id):
            LOGGER.info(
                "Suppressing snapshot request for %s: OTA in progress", dongle_id
            )
            return
        if not force and dongle_id in self._snapshot_requested:
            return
        if not self._needs_snapshot(version):
            return
        try:
            await mqtt.async_publish(
                self.hass,
                f"{dongle_id}/snapshot/request",
                '{"what":"all"}',
                qos=1,
                retain=False,
            )
            self._snapshot_requested.add(dongle_id)
            LOGGER.info(
                "Requested full snapshot from %s (version=%s)", dongle_id, version or "unknown"
            )
        except Exception as e:
            LOGGER.debug(f"Snapshot request publish failed for {dongle_id} (non-fatal): {e}")

    async def request_recovery_snapshot(self, dongle_id: str, reason: str) -> None:
        """Force a snapshot after a dongle recovers, debounced per dongle.

        Called from the recovery triggers (availability 'online', silent-reboot,
        or a data gap). Debounced so a burst of triggers (e.g. availability +
        first status arriving together) only sends one request.
        """
        if self.is_ota_in_progress(dongle_id):
            # Don't burn the debounce window while suppressed — the post-OTA
            # snapshot (or the next trigger after OTA ends) must not be swallowed.
            LOGGER.debug(
                "Suppressing recovery snapshot for %s (%s): OTA in progress",
                dongle_id, reason,
            )
            return
        now = time.monotonic()
        last = self._last_recovery_snapshot.get(dongle_id, 0.0)
        if now - last < self._recovery_snapshot_debounce:
            return
        self._last_recovery_snapshot[dongle_id] = now
        LOGGER.info("Recovery snapshot for %s (%s)", dongle_id, reason)
        await self.request_snapshot(
            dongle_id, self.current_fw_versions.get(dongle_id, ""), force=True
        )

    async def mark_dongle_seen(self, dongle_id: str) -> None:
        """Record that a message arrived from a dongle and detect gap recovery.

        If the dongle had been silent past the stale threshold (it went dark, e.g.
        a restart whose LWT 'offline' we never received), its next message triggers
        a recovery snapshot so entities repopulate instead of staying unavailable.
        """
        now = time.monotonic()
        previous = self._dongle_last_seen.get(dongle_id)
        self._dongle_last_seen[dongle_id] = now
        if previous is not None and (now - previous) > self._dongle_stale_after:
            await self.request_recovery_snapshot(
                dongle_id, f"data resumed after {int(now - previous)}s gap"
            )

    def get_entity_prefix(self, dongle_id: str) -> str:
        """Return the per-dongle entity_id prefix, or "" for none.

        Sourced from the dongle's `entity_prefix` in dongle_data (set during setup:
        empty on single-dongle installs, mandatory dongle-id-or-custom on
        multi/parallel/gridboss). Falls back to the legacy behaviour for entries
        created before entity_prefix existed:
          - single dongle + drop_dongle_id flag -> "" (clean)
          - otherwise -> the formatted dongle id (never risk a real collision).
        The unique_id is unaffected by this, so entity_id renames preserve history.
        """
        info = self.get_dongle_info(dongle_id)
        if info is not None and "entity_prefix" in info:
            prefix = (info.get("entity_prefix") or "").strip()
            # Explicitly configured (may be intentionally empty on single dongle).
            return self.get_formatted_dongle_id(prefix) if prefix else ""

        # Legacy entries without entity_prefix: preserve prior behaviour.
        if getattr(self, "_drop_dongle_id", False) and len(self._dongle_ids) == 1:
            return ""
        return self.get_formatted_dongle_id(dongle_id)

    def build_entity_id(self, platform: str, dongle_id: str, type_suffix: str) -> str:
        """Build an entity_id using the dongle's entity_prefix.

        prefix set -> "<platform>.<prefix>_<suffix>"; empty -> "<platform>.<suffix>".
        The unique_id is separate and always dongle-scoped, so history follows across
        any entity_id naming change.
        """
        suffix = type_suffix.lower()
        prefix = self.get_entity_prefix(dongle_id)
        if prefix:
            return f"{platform}.{prefix}_{suffix}"
        return f"{platform}.{suffix}"
    

    @property
    def inverter_brand(self) -> str:
        """The brand of the inverter."""
        return cast(str, self.entry.data["inverter_brand"])
    
    @property
    def has_gridboss(self) -> bool:
        """Check if GridBoss is enabled."""
        return self._has_gridboss
    
    def get_firmware_group(self, dongle_id: str) -> str:
        """Return the firmware group (midbox/GEN/legacy/threephase/offgrid) for a dongle."""
        from .const import firmware_group
        return firmware_group(self.get_firmware_code(dongle_id))

    def entity_allowed_for_dongle(self, dongle_id: str, entity_def: dict) -> bool:
        """Whether an entity definition should be created for this dongle.

        Group-based gating, replacing the old exact `allowed_firmware_codes` lists:
        - An entity with `allowed_groups` is created only when the dongle's firmware
          group is listed.
        - An entity WITHOUT `allowed_groups` is a generic entity available to every
          group EXCEPT midbox. midbox (GridBoss) is a distinct device that only gets
          entities explicitly tagged with the 'midbox' group — matching the old rule
          where GridBoss dongles required an explicit allow-list entry.
        """
        group = self.get_firmware_group(dongle_id)
        allowed_groups = entity_def.get("allowed_groups")
        if not allowed_groups:
            return group != "midbox"
        return group in allowed_groups

    def is_gridboss_dongle(self, dongle_id: str) -> bool:
        """Check if a specific dongle is the GridBoss dongle."""
        # Firmware group 'midbox' (any I*** code) indicates GridBoss.
        if self.get_firmware_group(dongle_id) == "midbox":
            return True
        
        # Use the new dongle data structure to check if this dongle is marked as GridBoss
        dongle_info = self.get_dongle_info(dongle_id)
        if dongle_info.get("is_gridboss", False):
            return True
        
        # Fallback to old logic for backward compatibility
        if not self._has_gridboss or not self._gridboss_dongle:
            return False
        
        # Map the gridboss_dongle setting to actual dongle ID
        if self._gridboss_dongle == "dongle_id":
            # First dongle
            return dongle_id == self._dongle_ids[0] if self._dongle_ids else False
        elif self._gridboss_dongle.startswith("dongle_id_"):
            # Extract the index (dongle_id_2 = index 1, dongle_id_3 = index 2, etc.)
            try:
                index = int(self._gridboss_dongle.split("_")[-1]) - 1
                return dongle_id == self._dongle_ids[index] if index < len(self._dongle_ids) else False
            except (ValueError, IndexError):
                return False
        
        return False
    
    def update_smart_soc_volt_bits(self, dongle_id: str, smart_soc_volt_bits: dict):
        """Update the SmartSOCVoltBits settings for a dongle."""
        old_bits = self._smart_soc_volt_bits.get(dongle_id, {})
        self._smart_soc_volt_bits[dongle_id] = smart_soc_volt_bits
        # LOGGER.debug(f"Updated SmartSOCVoltBits for {dongle_id}: {smart_soc_volt_bits}")
        
        # If the bits changed, trigger entity updates
        if old_bits != smart_soc_volt_bits:
            self._trigger_entity_availability_update(dongle_id)
    
    def _trigger_entity_availability_update(self, dongle_id: str):
        """Trigger entity availability updates for a dongle."""
        # Don't trigger updates during startup
        if not self._hass_startup_complete:
            # LOGGER.debug(f"Skipping entity availability update for {dongle_id} - HA startup not complete")
            return
        
        # Add a small delay to allow MQTT responses to be processed first
        # This prevents availability logic from blocking legitimate user actions
        from homeassistant.helpers.event import async_call_later
        async def delayed_update(_):
            await self._async_update_entity_availability(dongle_id)
        async_call_later(self.hass, 2, delayed_update)
    
    async def _async_update_entity_availability(self, dongle_id: str):
        """Update entity availability states."""
        try:
            # Simply trigger a single coordinator update to refresh entity availability
            # The entities will check their availability in their available() property
            self.async_set_updated_data(self.entities)
            # LOGGER.debug(f"Triggered entity availability update for {dongle_id}")
        except Exception as e:
            LOGGER.error(f"Error updating entity availability for {dongle_id}: {e}")
    
    def get_smart_soc_volt_bits(self, dongle_id: str) -> dict:
        """Get the SmartSOCVoltBits settings for a dongle."""
        return self._smart_soc_volt_bits.get(dongle_id, {})
    
    def is_smartload_soc_volt_enabled(self, dongle_id: str, smartload_number: int) -> bool:
        """Check if a SmartLoad is configured to use SOC/Volt mode (True) or Time mode (False)."""
        smart_soc_volt_bits = self.get_smart_soc_volt_bits(dongle_id)
        key = f"SmartLoad{smartload_number}_SOC_Volt"
        return smart_soc_volt_bits.get(key, False)
    
    def is_entity_available_for_smartload(self, dongle_id: str, entity_unique_id: str) -> bool:
        """Check if an entity should be available based on SmartLoad SOC/Volt settings."""
        if not self.is_gridboss_dongle(dongle_id):
            return True  # Non-GridBoss entities are always available
        
        # Extract SmartLoad number from entity unique_id
        smartload_number = None
        if "SmartLoad1" in entity_unique_id:
            smartload_number = 1
        elif "SmartLoad2" in entity_unique_id:
            smartload_number = 2
        elif "SmartLoad3" in entity_unique_id:
            smartload_number = 3
        elif "SmartLoad4" in entity_unique_id:
            smartload_number = 4
        
        if smartload_number is None:
            return True  # Not a SmartLoad entity
        
        # Check if this is a SOC/Volt related entity
        soc_volt_entities = ["StartSOC", "EndSOC", "StartVolt", "EndVolt", "SheddingStartSOC", "SheddingEndSOC", "SheddingStartVolt", "SheddingEndVolt"]
        time_entities = ["Start0", "End0", "Start1", "End1", "Start2", "End2"]
        
        is_soc_volt_entity = any(suffix in entity_unique_id for suffix in soc_volt_entities)
        is_time_entity = any(suffix in entity_unique_id for suffix in time_entities)
        
        if is_soc_volt_entity:
            # SOC/Volt entities are available only when SmartLoad is in SOC/Volt mode
            return self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
        elif is_time_entity:
            # Time entities are available only when SmartLoad is in Time mode
            return not self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
        
        return True  # Other entities are always available
    
    def update_smartload_bits(self, dongle_id: str, smartload_bits: dict):
        """Update the SmartLoad Bits settings for a dongle."""
        old_bits = self._smartload_bits.get(dongle_id, {})
        self._smartload_bits[dongle_id] = smartload_bits
        # LOGGER.debug(f"Updated SmartLoad Bits for {dongle_id}: {smartload_bits}")
        
        # If the bits changed, trigger entity updates
        if old_bits != smartload_bits:
            self._trigger_entity_availability_update(dongle_id)
    
    def get_smartload_bits(self, dongle_id: str) -> dict:
        """Get the SmartLoad Bits settings for a dongle."""
        return self._smartload_bits.get(dongle_id, {})
    
    def update_port_modes(self, dongle_id: str, port_modes: dict):
        """Update the Port Mode settings for a dongle."""
        old_modes = self._port_modes.get(dongle_id, {})
        self._port_modes[dongle_id] = port_modes
        # LOGGER.debug(f"Updated Port Modes for {dongle_id}: {port_modes}")
        
        # If the modes changed, trigger entity updates
        if old_modes != port_modes:
            self._trigger_entity_availability_update(dongle_id)
    
    def get_port_modes(self, dongle_id: str) -> dict:
        """Get the Port Mode settings for a dongle."""
        return self._port_modes.get(dongle_id, {})
    
    def get_smartload_port_mode(self, dongle_id: str, smartload_number: int) -> int:
        """Get the Port Mode for a specific SmartLoad (0=Does Not Operate, 1=Smart Load, 2=AC Coupled)."""
        port_modes = self.get_port_modes(dongle_id)
        key = f"SmartLoad{smartload_number}_PortMode"  # The payload uses "SmartLoad1_PortMode", "SmartLoad2_PortMode", etc.
        return port_modes.get(key, 0)  # Default to "Does Not Operate"
    
    def update_charge_control_setting(self, dongle_id: str, charge_control):
        """Update the charge control setting for a dongle."""
        # Convert integer to string option if needed
        # ubBatChgcontrol options: ["SOC", "Voltage"]
        if isinstance(charge_control, int):
            options = ["SOC", "Voltage"]
            charge_control = options[charge_control] if charge_control < len(options) else charge_control

        if dongle_id not in self._charge_control_settings:
            self._charge_control_settings[dongle_id] = {}
        self._charge_control_settings[dongle_id] = charge_control
        # LOGGER.debug(f"Updated charge control setting for {dongle_id}: {charge_control}")
        self._trigger_entity_availability_update(dongle_id)
    
    def get_charge_control_setting(self, dongle_id: str) -> str:
        """Get the charge control setting for a dongle. Returns None if not available for this firmware."""
        return self._charge_control_settings.get(dongle_id, None)  # Return None if not available
    
    def update_discharge_control_setting(self, dongle_id: str, discharge_control):
        """Update the discharge control setting for a dongle."""
        # Convert integer to string option if needed
        # ubBatDischgControl options: ["SOC", "Voltage"]
        if isinstance(discharge_control, int):
            options = ["SOC", "Voltage"]
            discharge_control = options[discharge_control] if discharge_control < len(options) else discharge_control

        if dongle_id not in self._discharge_control_settings:
            self._discharge_control_settings[dongle_id] = {}
        self._discharge_control_settings[dongle_id] = discharge_control
        # LOGGER.debug(f"Updated discharge control setting for {dongle_id}: {discharge_control}")
        self._trigger_entity_availability_update(dongle_id)
    
    def get_discharge_control_setting(self, dongle_id: str) -> str:
        """Get the discharge control setting for a dongle."""
        return self._discharge_control_settings.get(dongle_id, "SOC")  # Default to SOC
    
    def update_charge_type_setting(self, dongle_id: str, charge_type):
        """Update the charge type setting for a dongle."""
        # Convert integer to string option if needed. ACChargeType's option list
        # varies by firmware group (0-based indexing) — these MUST stay in lockstep
        # with the three ACChargeType select entries in const.py:
        #   offgrid (C***):            6 options (0-5)
        #   GEN (12K, F/H/E):          3 options (According To Time / SOC-Volt / both)
        #   legacy (A) + ac_coupled (B): 3 options (Off / Time / SOC-Volt)
        if isinstance(charge_type, int):
            group = self.get_firmware_group(dongle_id)

            if group == "offgrid":
                options = ["Disabled", "Time According To", "According To Voltage", "According To SOC", "According To Time and Voltage", "According To Time and SOC"]
            elif group == "GEN":
                options = ["According To Time", "According To SOC/VOLT", "According To Time and SOC/VOLT"]
            elif group in ("legacy", "ac_coupled"):
                options = ["Off", "Time According To", "SOC/Volt According To"]
            else:
                LOGGER.warning(f"No ACChargeType option list for group {group!r} (dongle {dongle_id}), using legacy list")
                options = ["Off", "Time According To", "SOC/Volt According To"]

            charge_type = options[charge_type] if charge_type < len(options) else charge_type

        if dongle_id not in self._charge_type_settings:
            self._charge_type_settings[dongle_id] = {}
        self._charge_type_settings[dongle_id] = charge_type
        LOGGER.debug(f"Updated charge type setting for {dongle_id}: {charge_type}")
        self._trigger_entity_availability_update(dongle_id)
    
    def get_charge_type_setting(self, dongle_id: str) -> str:
        """Get the charge type setting for a dongle."""
        return self._charge_type_settings.get(dongle_id, "Time According To")  # Default to Time According To
    
    def is_smartload_enabled(self, dongle_id: str, smartload_number: int) -> bool:
        """Check if a SmartLoad is enabled."""
        smartload_bits = self.get_smartload_bits(dongle_id)
        key = f"SmartLoad{smartload_number}_Enable"
        return smartload_bits.get(key, False)
    
    def is_entity_available_for_smartload_enable(self, dongle_id: str, entity_unique_id: str) -> bool:
        """Check if an entity should be available based on Port Mode, SOC/Volt settings, and SmartLoad enable state."""
        if not self.is_gridboss_dongle(dongle_id):
            return True  # Non-GridBoss entities are always available
        
        # Extract SmartLoad number from entity unique_id
        smartload_number = None
        if "SmartLoad1" in entity_unique_id:
            smartload_number = 1
        elif "SmartLoad2" in entity_unique_id:
            smartload_number = 2
        elif "SmartLoad3" in entity_unique_id:
            smartload_number = 3
        elif "SmartLoad4" in entity_unique_id:
            smartload_number = 4
        
        # Check if this is a Port Mode select entity - these are always available
        if "PortMode" in entity_unique_id:
            return True
        
        # Check if this is a SOC/Volt mode select entity - available when Port Mode is Smart Load or AC Coupled
        if "SOC_Volt" in entity_unique_id:
            port_mode = self.get_smartload_port_mode(dongle_id, smartload_number)
            if port_mode in [1, 2]:  # Smart Load or AC Coupled mode
                # LOGGER.debug(f"Entity {entity_unique_id}: SOC/Volt mode select, Port Mode={port_mode}, available")
                return True
            else:
                # LOGGER.debug(f"Entity {entity_unique_id}: SOC/Volt mode select, Port Mode={port_mode}, not available")
                return False
        
        # If it's not a SmartLoad entity and not a Port Mode select, check if it's AC Coupled
        if smartload_number is None:
            # Check if this is an AC Coupled entity
            if "ACcouple" in entity_unique_id:
                # Extract AC Couple number
                ac_couple_number = None
                if "ACcouple1" in entity_unique_id:
                    ac_couple_number = 1
                elif "ACcouple2" in entity_unique_id:
                    ac_couple_number = 2
                elif "ACcouple3" in entity_unique_id:
                    ac_couple_number = 3
                elif "ACcouple4" in entity_unique_id:
                    ac_couple_number = 4
                
                if ac_couple_number is not None:
                    # AC Coupled entities are only available if the corresponding SmartLoad is in AC Coupled mode
                    port_mode = self.get_smartload_port_mode(dongle_id, ac_couple_number)
                    return port_mode == 2  # Only available if Port Mode is AC Coupled
                else:
                    return True  # Generic AC Coupled entity
            else:
                return True  # Not a SmartLoad or AC Coupled entity (like Generator, etc.)
        
        # Step 1: Check Port Mode first
        port_mode = self.get_smartload_port_mode(dongle_id, smartload_number)
        # LOGGER.debug(f"Entity {entity_unique_id}: SmartLoad{smartload_number} Port Mode={port_mode}")
        
        # If Port Mode is "Does Not Operate" (0), no entities are available
        if port_mode == 0:
            # LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=0, entity not available")
            return False
        
        # Step 2: Check entity type based on Port Mode
        if port_mode == 1:  # Smart Load mode
            # Smart Load entities are available
            if "SmartLoad" in entity_unique_id and "ACcouple" not in entity_unique_id:
                # Step 3: Check SOC/Volt vs Time mode for Smart Load entities
                if self._is_soc_volt_entity(entity_unique_id):
                    soc_volt_enabled = self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
                    # LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, SOC/Volt entity, SOC/Volt enabled={soc_volt_enabled}")
                    return soc_volt_enabled
                elif self._is_time_entity(entity_unique_id):
                    time_enabled = not self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
                    # LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, Time entity, Time enabled={time_enabled}")
                    return time_enabled
                else:
                    # Enable/Disable switches are always available when Port Mode is Smart Load
                    if "Enable" in entity_unique_id:
                        # LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, Enable switch, always available")
                        return True
                    # Other entities are available if SmartLoad is enabled
                    smartload_enabled = self.is_smartload_enabled(dongle_id, smartload_number)
                    # LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, Other entity, SmartLoad enabled={smartload_enabled}")
                    return smartload_enabled
            # LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, but not a SmartLoad entity")
            return False
            
        elif port_mode == 2:  # AC Coupled mode
            # AC Coupled entities are available
            if "ACcouple" in entity_unique_id:
                # AC Coupled enable switches are always available when Port Mode is AC Coupled
                if "Enable" in entity_unique_id:
                        # LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=2, AC Coupled Enable switch, always available")
                    return True
                # Other AC Coupled entities are available
                # LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=2, AC Coupled entity, available")
                return True
            return False
        
        return False
    
    def _is_soc_volt_entity(self, entity_unique_id: str) -> bool:
        """Check if an entity is SOC/Volt related."""
        soc_volt_entities = ["StartSOC", "EndSOC", "StartVolt", "EndVolt", "SheddingStartSOC", "SheddingEndSOC", "SheddingStartVolt", "SheddingEndVolt"]
        return any(entity in entity_unique_id for entity in soc_volt_entities)
    
    def _is_time_entity(self, entity_unique_id: str) -> bool:
        """Check if an entity is time related."""
        time_entities = ["Start0", "End0", "Start1", "End1", "Start2", "End2", "StartMinute", "EndMinute"]
        return any(entity in entity_unique_id for entity in time_entities)
    
    def _is_charge_voltage_entity(self, entity_unique_id: str) -> bool:
        """Check if an entity is charge voltage related."""
        charge_voltage_entities = ["ACChgStartVolt", "ACChgEndVolt"]
        return any(entity in entity_unique_id for entity in charge_voltage_entities)
    
    def _is_charge_soc_entity(self, entity_unique_id: str) -> bool:
        """Check if an entity is charge SOC related."""
        charge_soc_entities = ["ACChgStartSOC", "ACChgEndSOC"]
        return any(entity in entity_unique_id for entity in charge_soc_entities)
    
    def _is_discharge_voltage_entity(self, entity_unique_id: str) -> bool:
        """Check if an entity is discharge voltage related."""
        discharge_voltage_entities = ["ForceDichgEndVolt", "OngridEOD_Voltage", "CutVoltForDischg"]
        return any(entity in entity_unique_id for entity in discharge_voltage_entities)
    
    def _is_discharge_soc_entity(self, entity_unique_id: str) -> bool:
        """Check if an entity is discharge SOC related."""
        discharge_soc_entities = ["ForcedDischgSOCLimit"]
        return any(entity in entity_unique_id for entity in discharge_soc_entities)
    
    def _is_charge_time_entity(self, entity_unique_id: str) -> bool:
        """Check if an entity is charge time related (select entities for time-based charging)."""
        # Check for Time0-Time47 select entities (30-minute time slots)
        # Entity IDs are formatted as "dongle_id_Time0", "dongle_id_Time1", etc.
        for i in range(48):  # Time0 through Time47
            if entity_unique_id.endswith(f"_Time{i}") or entity_unique_id == f"Time{i}":
                return True
        
        # Check for other time-based charge entities
        charge_time_entities = ["ACChgStart", "ACChgEnd", "ACChgStart1", "ACChgEnd1", "ACChgStart2", "ACChgEnd2"]
        return any(entity in entity_unique_id for entity in charge_time_entities)
    
    def is_entity_available_for_standard_units(self, dongle_id: str, entity_unique_id: str) -> bool:
        """Check if an entity should be available for standard units based on charge/discharge control settings."""
        # Check charge voltage entities - must check BOTH ubBatChgcontrol AND ACChargeType
        if self._is_charge_voltage_entity(entity_unique_id):
            charge_control = self.get_charge_control_setting(dongle_id)
            charge_type = self.get_charge_type_setting(dongle_id)
            # If ubBatChgcontrol doesn't exist (returns None), these entities should be unavailable
            if charge_control is None:
                return False
            # ubBatChgcontrol: "Voltage" or "SOC"
            # ACChargeType consolidated options:
            # AAAA/BAAA/ccaa/EAAA/HAAA/ceaa: "According To Voltage", "According To Time and Voltage"
            # FAAB/FAAA: "According To SOC/VOLT", "According To Time and SOC/VOLT"
            return charge_control == "Voltage" and charge_type in ["According To Voltage", "According To Time and Voltage", "According To SOC/VOLT", "According To Time and SOC/VOLT"]

        # Check charge SOC entities - must check BOTH ubBatChgcontrol AND ACChargeType
        if self._is_charge_soc_entity(entity_unique_id):
            charge_control = self.get_charge_control_setting(dongle_id)
            charge_type = self.get_charge_type_setting(dongle_id)
            # If ubBatChgcontrol doesn't exist (returns None), these entities should be unavailable
            if charge_control is None:
                return False
            # ubBatChgcontrol: "Voltage" or "SOC"
            # ACChargeType consolidated options:
            # AAAA/BAAA/ccaa/EAAA/HAAA/ceaa: "According To SOC", "According To Time and SOC"
            # FAAB/FAAA: "According To SOC/VOLT", "According To Time and SOC/VOLT"
            return charge_control == "SOC" and charge_type in ["According To SOC", "According To Time and SOC", "According To SOC/VOLT", "According To Time and SOC/VOLT"]

        # Check charge time entities
        if self._is_charge_time_entity(entity_unique_id):
            charge_type = self.get_charge_type_setting(dongle_id)
            # ACChargeType consolidated options:
            # AAAA/BAAA/ccaa/EAAA/HAAA/ceaa: "Time According To", "According To Time and Voltage", "According To Time and SOC"
            # FAAB/FAAA: "According To Time", "According To Time and SOC/VOLT"
            # Disabled state should make time entities unavailable
            return charge_type in ["Time According To", "According To Time", "According To Time and Voltage", "According To Time and SOC", "According To Time and SOC/VOLT"]

        # Check discharge control entities
        if self._is_discharge_voltage_entity(entity_unique_id):
            discharge_control = self.get_discharge_control_setting(dongle_id)
            # ubBatDischgControl: "Voltage" or "SOC"
            return discharge_control == "Voltage"

        if self._is_discharge_soc_entity(entity_unique_id):
            discharge_control = self.get_discharge_control_setting(dongle_id)
            # ubBatDischgControl: "Voltage" or "SOC"
            return discharge_control == "SOC"

        # For all other entities, they are always available
        return True
    
    def is_entity_available_for_smartload(self, dongle_id: str, entity_unique_id: str) -> bool:
        """Check if an entity should be available based on Port Mode, SOC/Volt settings, and SmartLoad enable state."""
        # Use the new hierarchical availability logic
        return self.is_entity_available_for_smartload_enable(dongle_id, entity_unique_id)
    
    def is_entity_available(self, dongle_id: str, entity_unique_id: str) -> bool:
        """Unified method to check entity availability for both GridBoss and standard units."""
        if self.is_gridboss_dongle(dongle_id):
            # Use GridBoss conditional logic
            return self.is_entity_available_for_smartload_enable(dongle_id, entity_unique_id)
        else:
            # Use standard unit conditional logic
            return self.is_entity_available_for_standard_units(dongle_id, entity_unique_id)
    
    def get_entity_availability_info(self, dongle_id: str, entity_unique_id: str) -> dict:
        """Get detailed availability information including reason for unavailability."""
        if not self.last_update_success:
            return {
                "available": False,
                "reason": "Integration not responding - check connection"
            }
        
        if self.is_gridboss_dongle(dongle_id):
            # GridBoss logic
            available = self.is_entity_available_for_smartload_enable(dongle_id, entity_unique_id)
            if not available:
                reason = self._get_gridboss_unavailability_reason(dongle_id, entity_unique_id)
            else:
                reason = None
        else:
            # Standard unit logic
            available = self.is_entity_available_for_standard_units(dongle_id, entity_unique_id)
            if not available:
                reason = self._get_standard_unit_unavailability_reason(dongle_id, entity_unique_id)
            else:
                reason = None
        
        return {
            "available": available,
            "reason": reason
        }
    
    def _get_gridboss_unavailability_reason(self, dongle_id: str, entity_unique_id: str) -> str:
        """Get specific reason why a GridBoss entity is unavailable."""
        # Check if it's a SmartLoad entity
        if "SmartLoad" in entity_unique_id:
            # Extract SmartLoad number
            for i in range(1, 5):
                if f"SmartLoad{i}" in entity_unique_id:
                    smartload_number = i
                    break
            else:
                return "SmartLoad configuration not detected"
            
            port_mode = self.get_smartload_port_mode(dongle_id, smartload_number)
            
            if port_mode == 0:  # Does Not Operate
                return f"Smart Port {smartload_number} is set to 'Does Not Operate'"
            elif port_mode == 1:  # Smart Load
                if "Enable" in entity_unique_id:
                    return f"Smart Port {smartload_number} is in Smart Load mode - Enable switch should be available"
                elif "SOC_Volt" in entity_unique_id:
                    return f"Smart Port {smartload_number} is in Smart Load mode - SOC/Volt mode should be available"
                elif self._is_soc_volt_entity(entity_unique_id):
                    soc_volt_mode = self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
                    if not soc_volt_mode:
                        return f"Smart Port {smartload_number} is in Time mode - SOC/Volt settings not available"
                elif self._is_time_entity(entity_unique_id):
                    soc_volt_mode = self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
                    if soc_volt_mode:
                        return f"Smart Port {smartload_number} is in SOC/Volt mode - Time settings not available"
            elif port_mode == 2:  # AC Coupled
                if "Enable" in entity_unique_id:
                    return f"Smart Port {smartload_number} is in AC Coupled mode - Enable switch should be available"
                elif "SOC_Volt" in entity_unique_id:
                    return f"Smart Port {smartload_number} is in AC Coupled mode - SOC/Volt mode should be available"
                elif self._is_soc_volt_entity(entity_unique_id):
                    soc_volt_mode = self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
                    if not soc_volt_mode:
                        return f"Smart Port {smartload_number} is in Time mode - SOC/Volt settings not available"
                elif self._is_time_entity(entity_unique_id):
                    soc_volt_mode = self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
                    if soc_volt_mode:
                        return f"Smart Port {smartload_number} is in SOC/Volt mode - Time settings not available"
        
        return "Entity not available for current configuration"
    
    def _get_standard_unit_unavailability_reason(self, dongle_id: str, entity_unique_id: str) -> str:
        """Get specific reason why a standard unit entity is unavailable."""
        # Check charge control settings
        if self._is_charge_voltage_entity(entity_unique_id):
            charge_control = self.get_charge_control_setting(dongle_id)
            charge_type = self.get_charge_type_setting(dongle_id)
            if charge_control != "Voltage":
                return f"Charge control is set to '{charge_control}' - Voltage settings not available"
            elif charge_type not in ["According To Voltage", "According To Time and Voltage", "According To SOC/VOLT", "According To Time and SOC/VOLT"]:
                return f"Charge type is set to '{charge_type}' - Voltage settings not available"

        elif self._is_charge_soc_entity(entity_unique_id):
            charge_control = self.get_charge_control_setting(dongle_id)
            charge_type = self.get_charge_type_setting(dongle_id)
            if charge_control != "SOC":
                return f"Charge control is set to '{charge_control}' - SOC settings not available"
            elif charge_type not in ["According To SOC", "According To Time and SOC", "According To SOC/VOLT", "According To Time and SOC/VOLT"]:
                return f"Charge type is set to '{charge_type}' - SOC settings not available"

        elif self._is_charge_time_entity(entity_unique_id):
            charge_type = self.get_charge_type_setting(dongle_id)
            if charge_type not in ["Time According To", "According To Time", "According To Time and Voltage", "According To Time and SOC", "According To Time and SOC/VOLT"]:
                return f"Charge type is set to '{charge_type}' - Time settings not available"
        
        # Check discharge control settings
        elif self._is_discharge_voltage_entity(entity_unique_id):
            discharge_control = self.get_discharge_control_setting(dongle_id)
            if discharge_control != "Voltage":
                return f"Discharge control is set to '{discharge_control}' - Voltage settings not available"
        
        elif self._is_discharge_soc_entity(entity_unique_id):
            discharge_control = self.get_discharge_control_setting(dongle_id)
            if discharge_control != "SOC":
                return f"Discharge control is set to '{discharge_control}' - SOC settings not available"
        
        return "Entity not available for current configuration"

    def get_firmware_code(self, dongle_id: str) -> str:
        """Get firmware code for a specific dongle."""
        return self._firmware_codes.get(dongle_id)
    
    async def save_firmware_code(self, dongle_id: str, firmware_code: str):
        """Save firmware code to config entry data."""
        if self._firmware_codes.get(dongle_id) != firmware_code:
            self._firmware_codes[dongle_id] = firmware_code
            
            # Update config entry data
            current_data = self.entry.data.copy()
            if "firmware_codes" not in current_data:
                current_data["firmware_codes"] = {}
            current_data["firmware_codes"][dongle_id] = firmware_code
            
            # Update the config entry
            self.hass.config_entries.async_update_entry(self.entry, data=current_data)
            LOGGER.info(f"Saved firmware code {firmware_code} for dongle {dongle_id}")


    def get_dongle_info(self, dongle_id: str) -> Dict[str, Any]:
        """Get complete dongle information including bundle tracking."""
        for dongle_info in self._dongle_data:
            if dongle_info["dongle_id"] == dongle_id:
                return dongle_info
        return {}
    
    def is_dongle_master(self, dongle_id: str) -> bool:
        """Check if a dongle is a master."""
        dongle_info = self.get_dongle_info(dongle_id)
        return dongle_info.get("is_master", False)
    
    def is_dongle_slave(self, dongle_id: str) -> bool:
        """Check if a dongle is a slave."""
        dongle_info = self.get_dongle_info(dongle_id)
        return dongle_info.get("is_slave", False)
    
    def is_dongle_gridboss(self, dongle_id: str) -> bool:
        """Check if a dongle is a GridBoss."""
        dongle_info = self.get_dongle_info(dongle_id)
        return dongle_info.get("is_gridboss", False)
    
    def is_dongle_gridboss_slave(self, dongle_id: str) -> bool:
        """Check if a dongle is a GridBoss slave."""
        dongle_info = self.get_dongle_info(dongle_id)
        return dongle_info.get("is_gridboss_slave", False)
    
    def get_dongle_gridboss_bundle(self, dongle_id: str) -> int:
        """Get the GridBoss bundle number for a dongle (1 or 2, or None)."""
        dongle_info = self.get_dongle_info(dongle_id)
        return dongle_info.get("gridboss_bundle")
    
    def get_dongles_by_bundle(self, bundle_number: int) -> List[str]:
        """Get all dongle IDs that belong to a specific GridBoss bundle."""
        dongles = []
        for dongle_info in self._dongle_data:
            if dongle_info.get("gridboss_bundle") == bundle_number:
                dongles.append(dongle_info["dongle_id"])
        return dongles

    def get_dongles_by_filter(self, dongle_filter: str) -> List[str]:
        """Get dongle IDs based on filter type."""
        if dongle_filter == "inverters_only":
            # All non-GridBoss dongles (masters and slaves)
            return [d["dongle_id"] for d in self._dongle_data if not d.get("is_gridboss", False)]
        elif dongle_filter == "gridboss_only":
            # Only GridBoss dongles
            return [d["dongle_id"] for d in self._dongle_data if d.get("is_gridboss", False)]
        elif dongle_filter == "gridboss_slaves_only":
            # Only GridBoss slave dongles
            return [d["dongle_id"] for d in self._dongle_data if d.get("is_gridboss_slave", False)]
        elif dongle_filter == "bundle_1":
            # All dongles in bundle 1 (GridBoss + slaves)
            return [d["dongle_id"] for d in self._dongle_data if d.get("gridboss_bundle") == 1]
        elif dongle_filter == "bundle_2":
            # All dongles in bundle 2 (GridBoss + slaves)
            return [d["dongle_id"] for d in self._dongle_data if d.get("gridboss_bundle") == 2]
        else:
            # Default: return all dongles
            return [d["dongle_id"] for d in self._dongle_data]
    
    def get_all_gridboss_dongles(self) -> List[str]:
        """Get all GridBoss dongle IDs (both bundles)."""
        dongles = []
        for dongle_info in self._dongle_data:
            if dongle_info.get("is_gridboss", False):
                dongles.append(dongle_info["dongle_id"])
        return dongles
    
    def get_setup_type(self) -> str:
        """Get the setup type based on dongle data structure."""
        gridboss_dongles = self.get_all_gridboss_dongles()
        gridboss_slaves = [d for d in self._dongle_data if d.get("is_gridboss_slave", False)]
        masters = [d for d in self._dongle_data if d.get("is_master", False)]
        slaves = [d for d in self._dongle_data if d.get("is_slave", False)]
        
        if len(gridboss_dongles) == 2:
            return "dual_gridboss"
        elif len(gridboss_dongles) == 1 and len(gridboss_slaves) > 0:
            return "single_gridboss_with_slaves"
        elif len(gridboss_dongles) == 1 and len(gridboss_slaves) == 0:
            return "single_gridboss_only"
        elif len(masters) > 0 and len(slaves) > 0:
            return "parallel"
        else:
            return "single"
    
    def get_sync_settings_enabled(self) -> bool:
        """Get the current sync settings state."""
        return self._sync_settings_enabled

    def get_combined_entities_for_setup_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get combined entity definitions based on setup type and entity type."""
        setup_type = self.get_setup_type()
        
        # Only create combined entities for multi-dongle setups
        if setup_type == "single":
            return []
        
        # Get all dongle IDs for this setup
        all_dongle_ids = [d["dongle_id"] for d in self._dongle_data]
        
        if entity_type == "sensor":
            return self._get_combined_sensor_entities(setup_type, all_dongle_ids)
        elif entity_type == "switch":
            return self._get_combined_switch_entities(setup_type, all_dongle_ids)
        elif entity_type == "number":
            return self._get_combined_number_entities(setup_type, all_dongle_ids)
        else:
            return []

    def _get_combined_sensor_entities(self, setup_type: str, dongle_ids: List[str]) -> List[Dict[str, Any]]:
        """Get combined sensor entities based on setup type."""
        if setup_type == "parallel":
            # Standard parallel setup - combine all inverter values
            return [
                {"name": "Combined PV Power Total", "type": "sensor", "unique_id": "combined_pv_power", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "pall"}},
                {"name": "Combined House Power Load", "type": "sensor", "unique_id": "combined_house_power_load", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "pload"}},
                {"name": "Combined Energy To Grid Day", "type": "sensor", "unique_id": "combined_energy_to_grid_day", 
                 "state_class": "total_increasing", "unit_of_measurement": "kWh", "device_class": "energy", 
                 "calculation": {"operation": "addition", "source_entity": "etogrid_day"}},
                {"name": "Combined Energy To User Day", "type": "sensor", "unique_id": "combined_energy_to_user_day", 
                 "state_class": "total_increasing", "unit_of_measurement": "kWh", "device_class": "energy", 
                 "calculation": {"operation": "addition", "source_entity": "etouser_day"}},
                {"name": "Combined Energy To Grid (live)", "type": "sensor", "unique_id": "combined_energy_to_grid_live", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "ptogrid"}},
                {"name": "Combined Energy To User (live)", "type": "sensor", "unique_id": "combined_energy_to_user_live", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "ptouser"}},
                {"name": "Combined Discharge", "type": "sensor", "unique_id": "combined_discharge", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "pdischarge"}},
                {"name": "Combined Charge", "type": "sensor", "unique_id": "combined_charge", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "pcharge"}},
                {"name": "Combined SOC", "type": "sensor", "unique_id": "combined_soc", 
                 "state_class": "measurement", "device_class": "battery", "unit_of_measurement": "%", 
                 "calculation": {"operation": "average", "source_entity": "soc"}},
                {"name": "Combined SOH", "type": "sensor", "unique_id": "combined_soh", 
                 "state_class": "measurement", "device_class": "battery", "unit_of_measurement": "%", 
                 "calculation": {"operation": "average", "source_entity": "soh"}},
                {"name": "Combined Power EPS", "type": "sensor", "unique_id": "combined_eps", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "peps"}}
            ]
        
        elif setup_type in ["single_gridboss_with_slaves", "single_gridboss_only"]:
            # Single GridBoss + slaves - only combine if there are multiple slaves
            gridboss_slave_dongles = [d["dongle_id"] for d in self._dongle_data if d.get("is_gridboss_slave", False)]
            if len(gridboss_slave_dongles) <= 1:
                return []  # No combined entities for single GridBoss with 0-1 slaves
            
            # Combine only the slave inverter values (not GridBoss values)
            return [
                {"name": "Combined PV Power Total", "type": "sensor", "unique_id": "combined_pv_power", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "pall", "dongle_filter": "gridboss_slaves_only"}},
                {"name": "Combined House Power Load", "type": "sensor", "unique_id": "combined_house_power_load", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "pload", "dongle_filter": "gridboss_slaves_only"}},
                {"name": "Combined SOC", "type": "sensor", "unique_id": "combined_soc", 
                 "state_class": "measurement", "device_class": "battery", "unit_of_measurement": "%", 
                 "calculation": {"operation": "average", "source_entity": "soc", "dongle_filter": "gridboss_slaves_only"}},
                {"name": "Combined SOH", "type": "sensor", "unique_id": "combined_soh", 
                 "state_class": "measurement", "device_class": "battery", "unit_of_measurement": "%", 
                 "calculation": {"operation": "average", "source_entity": "soh", "dongle_filter": "gridboss_slaves_only"}}
            ]
        
        elif setup_type == "dual_gridboss":
            # Dual GridBoss - create NET entities and combined values
            return [
                # GridBoss NET Power Entities (L1 + L2)
                {"name": "GridBoss BU Active Power NET", "type": "sensor", "unique_id": "gridboss_bu_active_power_net", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "net_power", "source_entities": ["buL1ActivePower", "buL2ActivePower"], "dongle_filter": "gridboss_only"}},
                {"name": "GridBoss Grid Active Power NET", "type": "sensor", "unique_id": "gridboss_grid_active_power_net", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "net_power", "source_entities": ["gridL1ActivePower", "gridL2ActivePower"], "dongle_filter": "gridboss_only"}},
                {"name": "GridBoss BU RMS Current NET", "type": "sensor", "unique_id": "gridboss_bu_rms_current_net", 
                 "state_class": "measurement", "device_class": "current", "unit_of_measurement": "A", 
                 "calculation": {"operation": "net_current", "source_entities": ["buL1RMSCurrent", "buL2RMSCurrent"], "dongle_filter": "gridboss_only"}},
                {"name": "GridBoss Grid RMS Current NET", "type": "sensor", "unique_id": "gridboss_grid_rms_current_net", 
                 "state_class": "measurement", "device_class": "current", "unit_of_measurement": "A", 
                 "calculation": {"operation": "net_current", "source_entities": ["gridL1RMSCurrent", "gridL2RMSCurrent"], "dongle_filter": "gridboss_only"}},
                
                # GridBoss Voltage Averages
                {"name": "GridBoss BU RMS Voltage Average", "type": "sensor", "unique_id": "gridboss_bu_rms_voltage_avg", 
                 "state_class": "measurement", "device_class": "voltage", "unit_of_measurement": "V", 
                 "calculation": {"operation": "average", "source_entities": ["buL1RMSVoltage", "buL2RMSVoltage"], "dongle_filter": "gridboss_only"}},
                {"name": "GridBoss Grid RMS Voltage Average", "type": "sensor", "unique_id": "gridboss_grid_rms_voltage_avg", 
                 "state_class": "measurement", "device_class": "voltage", "unit_of_measurement": "V", 
                 "calculation": {"operation": "average", "source_entities": ["gridL1RMSVoltage", "gridL2RMSVoltage"], "dongle_filter": "gridboss_only"}},
                
                # FlexBoss Combined Entities (all slaves across both bundles)
                {"name": "Combined Battery Flow Live", "type": "sensor", "unique_id": "combined_batteryflow_live", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "batteryflow_live", "dongle_filter": "gridboss_slaves_only"}},
                {"name": "Combined PV Power Total", "type": "sensor", "unique_id": "combined_pv_power", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "pall", "dongle_filter": "gridboss_slaves_only"}},
                {"name": "Combined PV Energy Total", "type": "sensor", "unique_id": "combined_pv_energy_total", 
                 "state_class": "total", "device_class": "energy", "unit_of_measurement": "kWh", 
                 "calculation": {"operation": "addition", "source_entity": "epv_all", "dongle_filter": "gridboss_slaves_only"}},
                {"name": "Combined Battery Temperature Average", "type": "sensor", "unique_id": "combined_battery_temp_avg", 
                 "state_class": "measurement", "device_class": "temperature", "unit_of_measurement": "°C", 
                 "calculation": {"operation": "average", "source_entity": "tbat", "dongle_filter": "gridboss_slaves_only"}},
                {"name": "Combined SOC Average", "type": "sensor", "unique_id": "combined_soc_avg", 
                 "state_class": "measurement", "device_class": "battery", "unit_of_measurement": "%", 
                 "calculation": {"operation": "average", "source_entity": "soc", "dongle_filter": "gridboss_slaves_only"}},
                
                # Bundle-specific combined entities
                {"name": "GridBoss Bundle 1 PV Power", "type": "sensor", "unique_id": "gridboss_bundle1_pv_power", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "pall", "dongle_filter": "bundle_1"}},
                {"name": "GridBoss Bundle 2 PV Power", "type": "sensor", "unique_id": "gridboss_bundle2_pv_power", 
                 "state_class": "measurement", "device_class": "power", "unit_of_measurement": "W", 
                 "calculation": {"operation": "addition", "source_entity": "pall", "dongle_filter": "bundle_2"}}
            ]
        
        return []

    def _get_combined_switch_entities(self, setup_type: str, dongle_ids: List[str]) -> List[Dict[str, Any]]:
        """Get combined switch entities based on setup type."""
        if setup_type == "parallel":
            # Standard parallel setup - combine all inverter switches
            return [
                {"name": "Combined AC Charge", "type": "switch", "unique_id": "combined_accharge", "source_entity": "ACCharge"},
                {"name": "Combined EPS", "type": "switch", "unique_id": "combined_eps", "source_entity": "EPS"},
                {"name": "Combined Force Discharge", "type": "switch", "unique_id": "combined_forceddischg", "source_entity": "ForcedDischg"},
                {"name": "Combined Charge Priority", "type": "switch", "unique_id": "combined_forcedchg", "source_entity": "ForcedChg"},
                {"name": "Combined Export Allowed", "type": "switch", "unique_id": "combined_feedingrid", "source_entity": "FeedInGrid"},
                {"name": "Sync Inverter Settings", "type": "switch", "unique_id": "combined_sync_settings", "icon": "mdi:sync", "is_sync_switch": True}
            ]
        
        elif setup_type in ["single_gridboss_with_slaves", "single_gridboss_only"]:
            # Single GridBoss + slaves - only combine if there are multiple slaves
            gridboss_slave_dongles = [d["dongle_id"] for d in self._dongle_data if d.get("is_gridboss_slave", False)]
            if len(gridboss_slave_dongles) <= 1:
                return []  # No combined entities for single GridBoss with 0-1 slaves
            
            # Combine only the slave inverter switches (not GridBoss switches)
            return [
                {"name": "Combined AC Charge", "type": "switch", "unique_id": "combined_accharge", "source_entity": "ACCharge", "dongle_filter": "gridboss_slaves_only"},
                {"name": "Combined EPS", "type": "switch", "unique_id": "combined_eps", "source_entity": "EPS", "dongle_filter": "gridboss_slaves_only"},
                {"name": "Combined Force Discharge", "type": "switch", "unique_id": "combined_forceddischg", "source_entity": "ForcedDischg", "dongle_filter": "gridboss_slaves_only"},
                {"name": "Combined Charge Priority", "type": "switch", "unique_id": "combined_forcedchg", "source_entity": "ForcedChg", "dongle_filter": "gridboss_slaves_only"},
                {"name": "Combined Export Allowed", "type": "switch", "unique_id": "combined_feedingrid", "source_entity": "FeedInGrid", "dongle_filter": "gridboss_slaves_only"},
                {"name": "Sync Inverter Settings", "type": "switch", "unique_id": "combined_sync_settings", "icon": "mdi:sync", "is_sync_switch": True, "dongle_filter": "gridboss_slaves_only"}
            ]
        
        elif setup_type == "dual_gridboss":
            # Dual GridBoss - no combined switches, only individual dongle switches
            return []
        
        return []

    def _get_combined_number_entities(self, setup_type: str, dongle_ids: List[str]) -> List[Dict[str, Any]]:
        """Get combined number entities based on setup type."""
        if setup_type == "parallel":
            # Standard parallel setup - combine all inverter numbers
            return [
                {"name": "Combined AC Charge Rate", "type": "number", "unique_id": "combined_acchgpowercmd", "source_entity": "ACChgPowerCMD", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"},
                {"name": "Combined AC Charge SOC Limit", "type": "number", "unique_id": "combined_acchgsoclimit", "source_entity": "ACChgSOCLimit", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider", "class": "BATTERY"},
                {"name": "Combined Discharge Power Rate", "type": "number", "unique_id": "combined_dischgpowerpercentcmd", "source_entity": "DischgPowerPercentCMD", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"}
            ]
        
        elif setup_type in ["single_gridboss_with_slaves", "single_gridboss_only"]:
            # Single GridBoss + slaves - only combine if there are multiple slaves
            gridboss_slave_dongles = [d["dongle_id"] for d in self._dongle_data if d.get("is_gridboss_slave", False)]
            if len(gridboss_slave_dongles) <= 1:
                return []  # No combined entities for single GridBoss with 0-1 slaves
            
            # Combine only the slave inverter numbers (not GridBoss numbers)
            return [
                {"name": "Combined AC Charge Rate", "type": "number", "unique_id": "combined_acchgpowercmd", "source_entity": "ACChgPowerCMD", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider", "dongle_filter": "gridboss_slaves_only"},
                {"name": "Combined AC Charge SOC Limit", "type": "number", "unique_id": "combined_acchgsoclimit", "source_entity": "ACChgSOCLimit", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider", "class": "BATTERY", "dongle_filter": "gridboss_slaves_only"},
                {"name": "Combined Discharge Power Rate", "type": "number", "unique_id": "combined_dischgpowerpercentcmd", "source_entity": "DischgPowerPercentCMD", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider", "dongle_filter": "gridboss_slaves_only"}
            ]
        
        elif setup_type == "dual_gridboss":
            # Dual GridBoss - no combined numbers, only individual dongle numbers
            return []
        
        return []
    
    def set_sync_settings_enabled(self, enabled: bool) -> None:
        """Set the sync settings state."""
        self._sync_settings_enabled = enabled
        # LOGGER.debug(f"Sync settings state set to: {enabled}")
    
    def record_setting_change(self, dongle_id: str, unique_id: str, value: any, timestamp: float = None) -> None:
        """Record a setting change with timestamp for tracking."""
        if timestamp is None:
            timestamp = self.hass.loop.time()
        
        setting_key = f"{unique_id}"
        if setting_key not in self._setting_history:
            self._setting_history[setting_key] = []
        
        # Add new entry
        self._setting_history[setting_key].append({
            "dongle_id": dongle_id,
            "value": value,
            "timestamp": timestamp
        })
        
        # Limit history size
        if len(self._setting_history[setting_key]) > self._max_history_entries:
            self._setting_history[setting_key] = self._setting_history[setting_key][-self._max_history_entries:]
        
        # LOGGER.debug(f"Recorded setting change: {dongle_id}/{unique_id} = {value} at {timestamp}")
    
    def get_latest_setting_change(self, unique_id: str) -> Dict[str, any]:
        """Get the most recent change for a setting across all dongles."""
        setting_key = f"{unique_id}"
        if setting_key not in self._setting_history or not self._setting_history[setting_key]:
            return None
        
        # Return the most recent change
        return max(self._setting_history[setting_key], key=lambda x: x["timestamp"])
    
    def get_setting_values_by_dongle(self, unique_id: str) -> Dict[str, any]:
        """Get the current values for a setting from each dongle based on history."""
        setting_key = f"{unique_id}"
        if setting_key not in self._setting_history:
            return {}
        
        # Get the most recent value for each dongle
        values_by_dongle = {}
        for entry in self._setting_history[setting_key]:
            dongle_id = entry["dongle_id"]
            # Keep the latest value for each dongle
            if dongle_id not in values_by_dongle or entry["timestamp"] > values_by_dongle[dongle_id]["timestamp"]:
                values_by_dongle[dongle_id] = {
                    "value": entry["value"],
                    "timestamp": entry["timestamp"]
                }
        
        return values_by_dongle

    @callback
    async def _async_handle_mqtt_message(self, msg) -> None:
        """Handle all MQTT messages."""
        topic = msg.topic
        
        # Extract dongle ID from the topic
        try:
            dongle_id = topic.split('/')[0]
            #LOGGER.debug(f"Received MQTT message on topic {topic} from dongle {dongle_id}")

            # Record liveness and recover from a silent gap. The snapshot reply
            # topics are excluded so the recovery snapshot doesn't re-arm itself
            # from its own reply.
            if not topic.endswith("/snap/input") and not topic.endswith("/snap/hold"):
                await self.mark_dongle_seen(dongle_id)

            # Always process firmware code responses as they're needed for setup
            if topic.endswith("/firmwarecode/response"):
                await self._handle_firmware_code_response(dongle_id, msg)
            # Skip debug topics - we don't need to process them
            elif "/debug/" in topic:
                # Ignore debug topics like debug/bits, debug/bitfield, etc.
                return
            # Handle battery extended data topic
            elif topic.endswith("/batteries"):
                await self._handle_battery_data(dongle_id, msg.payload)
            # Always process /status and /availability, even during startup: they
            # carry the firmware version and connection state that drive the
            # full-snapshot bootstrap (FW >= 4.3.0 streams change-data only).
            elif topic.endswith("/status"):
                await self.process_status_message(dongle_id, msg.payload)
            elif topic.endswith("/availability"):
                await self.process_message(dongle_id, topic, msg.payload)
            # Always process the snapshot reply, even during startup. The snapshot
            # IS the connect-time bootstrap: it arrives within ~1s of the request
            # we send in start_mqtt_subscription, which is well inside the ~30s
            # startup window. If we dropped it (as the generic pre-startup branch
            # below would), entities would stay empty until the next change-data —
            # which on FW >= 4.3.0 (change-data only) may be a long time. The
            # firmware publishes it on <dongle>/snap/input and <dongle>/snap/hold.
            elif topic.endswith("/snap/input") or topic.endswith("/snap/hold"):
                await self.process_message(dongle_id, topic, msg.payload)
                self.async_set_updated_data(self.entities)
            # Skip other message processing during startup to prevent excessive updates
            elif not self._hass_startup_complete:
                # Just store the message for later processing if needed
                pass
            else:
                # Process messages normally after startup is complete
                if topic.endswith("/response"):
                    # /response is owned by the dedicated subscription created in
                    # MQTTHandler._process_command for the in-flight write (it
                    # drives the send lock, revert-on-failure and confirm). The
                    # wildcard {dongle}/# sub also delivers it here — calling
                    # response_received again would double-process the same ack.
                    # Skip it; when no write is in flight there's nothing to do
                    # anyway (current_entity is None -> early return).
                    pass
                elif topic.endswith("/status"):
                    await self.process_status_message(dongle_id, msg.payload)
                else:
                    await self.process_message(dongle_id, topic, msg.payload)

                self.async_set_updated_data(self.entities)
        except Exception as e:
            LOGGER.error(f"Error processing MQTT message on topic {msg.topic}: {e}")
            # Only update data after startup is complete
            if self._hass_startup_complete:
                self.async_set_updated_data(self.entities)

    async def _handle_firmware_code_response(self, dongle_id: str, msg) -> None:
        """Handle firmware code response."""
        LOGGER.debug(f"Received firmware code response for dongle {dongle_id}")
        try:
            data = json.loads(msg.payload)

            # Handle both dict and list response formats
            if isinstance(data, list):
                LOGGER.warning(f"Firmware code response for {dongle_id} is a list format: {data}. Expected dict format with 'FWCode' key.")
                # Try to extract firmware code from list if it's a single-element list with a dict
                if len(data) == 1 and isinstance(data[0], dict):
                    data = data[0]
                else:
                    LOGGER.error(f"Cannot parse firmware code from list format for {dongle_id}: {data}")
                    return

            if not isinstance(data, dict):
                LOGGER.error(f"Firmware code response for {dongle_id} is not a dict or parseable list: {type(data)}")
                return

            firmware_code = data.get("FWCode")

            # Validate the dongle ID is one we're expecting
            if dongle_id not in self._dongle_ids:
                LOGGER.warning(f"Received firmware code response from unexpected dongle ID: {dongle_id}")
                return

            if firmware_code:
                self._firmware_codes[dongle_id] = firmware_code
                LOGGER.debug(f"Firmware code received for {dongle_id}: {firmware_code}")
                
                # Save the firmware code to config entry
                await self.save_firmware_code(dongle_id, firmware_code)
                
                # Create entities for this dongle now that we have the firmware code
                await self._create_entities_for_dongle(dongle_id)
                
                # Check if this completes our setup for all dongles
                if dongle_id in self._pending_dongles:
                    self._pending_dongles.remove(dongle_id)
                    LOGGER.debug(f"Removed {dongle_id} from pending dongles. Remaining: {len(self._pending_dongles)} - {self._pending_dongles}")
                else:
                    LOGGER.warning(f"Received firmware code for {dongle_id} but it wasn't in the pending list")
                    
                # Note: We don't automatically start MQTT subscription here anymore
                # That's handled in __init__.py after all setup steps
            else:
                LOGGER.error(f"No firmware code found in response for dongle {dongle_id}")
        except json.JSONDecodeError:
            LOGGER.error(f"Failed to decode JSON from response for dongle {dongle_id}: {msg.payload}")
        except ValueError as e:
            LOGGER.error(f"Error processing firmware code for {dongle_id}: {e}")
        except Exception as e:
            LOGGER.error(f"Unexpected error handling firmware code response for {dongle_id}: {str(e)}")
        
        # Update coordinator data to trigger any listeners
        self.async_set_updated_data(self.entities)
    
    async def _handle_battery_data(self, dongle_id: str, payload) -> None:
        """Handle battery extended data from dongleid/batteries topic."""
        if payload is None or len(payload.strip()) == 0:
            return

        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            LOGGER.error(f"Invalid JSON in battery data from {dongle_id}")
            return

        # Handle both wrapped and direct payload formats
        if "payload" in data:
            battery_payload = data["payload"]
        else:
            battery_payload = data

        batteries = battery_payload.get("batteries", [])
        if not batteries:
            return

        LOGGER.debug(f"Received battery data for {dongle_id}: {len(batteries)} batteries")

        # Store battery data
        self._battery_data[dongle_id] = battery_payload

        # Update entity states for existing battery sensors.
        # NOTE: the firmware's batIndex is unreliable — multiple batteries in the
        # same payload can all report batIndex == 0. Use the list position as the
        # stable per-battery index instead, matching _create_battery_entities().
        for position, battery in enumerate(batteries):
            for key, value in battery.items():
                if key in ("batIndex",):
                    continue
                entity_id = self.build_entity_id(
                    "sensor", dongle_id, f"battery_{position}_{key}"
                )
                self.entities[entity_id] = value

        # Fire the creation event whenever we see more batteries than we've already
        # built entities for (the count can grow, and the firmware's batIndex can't
        # be trusted to distinguish them). Tracked per (dongle, position).
        created = self._battery_entities_created
        new_positions = [
            f"{dongle_id}:{pos}" for pos in range(len(batteries))
            if f"{dongle_id}:{pos}" not in created
        ]
        if new_positions:
            LOGGER.info(
                f"Battery data for {dongle_id}: {len(batteries)} batteries, "
                f"{len(new_positions)} new - triggering entity creation"
            )
            self.hass.bus.async_fire(
                f"{DOMAIN}_battery_data_received",
                {"dongle_id": dongle_id, "battery_count": len(batteries)}
            )

        self.async_set_updated_data(self.entities)

    def get_battery_data(self, dongle_id: str) -> Dict:
        """Get battery extended data for a dongle."""
        return self._battery_data.get(dongle_id, {})

    def _process_gridboss_nested_data(self, dongle_id: str, payload_data):
        """Process GridBoss nested payload structure - now simplified since payload has correct entity names."""

        # Recursively process all nested data, flattening it to match entity unique_ids
        def flatten_nested_data(data, prefix=""):
            """Recursively flatten nested data structure."""
            flattened = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    # Recursively process nested dictionaries
                    nested_flattened = flatten_nested_data(value, prefix)
                    flattened.update(nested_flattened)
                else:
                    # Direct key-value pair - use the key as-is since it now matches unique_id
                    flattened[key] = value
            return flattened
        
        # Check for SmartSOCVoltBits in the payload and track it
        if "SmartSOCVoltBits" in payload_data:
            self.update_smart_soc_volt_bits(dongle_id, payload_data["SmartSOCVoltBits"])
        
        # Check for SmartLoad Bits in the payload and track it
        if "SmartLoad" in payload_data and "Bits" in payload_data["SmartLoad"]:
            self.update_smartload_bits(dongle_id, payload_data["SmartLoad"]["Bits"])
        
        # Check for Port Mode settings in the payload and track it
        if "MIDBox_SmartPortModeStruct" in payload_data:
            # Store Port Mode data as-is without flattening (it already has correct keys)
            port_mode_data = payload_data["MIDBox_SmartPortModeStruct"]
            self.update_port_modes(dongle_id, port_mode_data)
        
        # Flatten the entire payload structure
        flattened_data = flatten_nested_data(payload_data)
        
        # Process each flattened item
        for entity_id_suffix, state in flattened_data.items():
            # Skip if we've already handled these keys
            if entity_id_suffix in ("SW_VERSION", "UI_VERSION"):
                continue
                
            formatted_entity_id_suffix = entity_id_suffix.lower().replace("-", "_").replace(":", "_")
            entity_type = self.determine_entity_type(formatted_entity_id_suffix)
            entity_id = self.build_entity_id(entity_type, dongle_id, formatted_entity_id_suffix)
            self.entities[entity_id] = state

    async def _create_entities_for_dongle(self, dongle_id: str):
        """Create entities for a specific dongle after firmware code is received."""
        is_gridboss = self.is_gridboss_dongle(dongle_id)
        
        # Get brand entities
        brand_entities = ENTITIES.get(self.inverter_brand, {})
        if not brand_entities:
            LOGGER.error(f"No entities defined for inverter brand: {self.inverter_brand}")
            return
        
        entities_created = 0
        for entityTypeName, entityTypes in brand_entities.items():
            # Defensive: some brand registries have legacy flat-list
            # entries (e.g. ENTITIES["Lux"]["calculated"] is a list, not
            # a dict-of-lists like ENTITIES["Lux"]["sensor"]). Skip those
            # — they're either dead code or get created via a different
            # path. Without this guard `.items()` below crashes the
            # entire firmware-code-response handler with
            # "'list' object has no attribute 'items'".
            if not isinstance(entityTypes, dict):
                LOGGER.debug(
                    f"Skipping legacy flat-list entry {self.inverter_brand}.{entityTypeName}"
                )
                continue
            for typeName, entities in entityTypes.items():
                for entity in entities:
                    # Use the source field if present, otherwise fall back to the bank name (typeName)
                    source = entity.get("source", typeName)
                    # For GridBoss dongles, only create GridBoss-specific entities
                    if is_gridboss and not source.startswith("gridboss_"):
                        continue
                    # For non-GridBoss dongles, skip GridBoss-specific entities
                    elif not is_gridboss and source.startswith("gridboss_"):
                        continue
                        
                    entity_id: str = self.build_entity_id(entityTypeName, dongle_id, entity['unique_id'])
                    self.entities[entity_id] = None
                    entities_created += 1
        
        LOGGER.info(f"Created {entities_created} entities for dongle {dongle_id} (GridBoss: {is_gridboss}, Firmware: {self.get_firmware_code(dongle_id)})")
        
        # Update coordinator data
        self.async_set_updated_data(self.entities)

    @callback
    async def async_setup(self):
        """Initial setup of coordinator."""
        # Initialize the MQTT handler and store it in the hass data under the domain
        mqtt_handler = MQTTHandler(self.hass)
        mqtt_handler.coordinator = self  # Give MQTT handler access to coordinator
        self.mqtt_handler = mqtt_handler

        # Set up entities dictionary
        brand_entities = ENTITIES.get(self.inverter_brand, {})
        if not brand_entities:
            LOGGER.error(f"No entities defined for inverter brand: {self.inverter_brand}")
            return False

        # Don't create entities yet - wait for firmware codes to determine entity types
        # Entities will be created in _recreate_entities_for_dongle() after firmware codes are received

        # Request firmware codes for all dongles
        await self.request_firmware_codes()
        
        # Set up update listener
        self.entry.async_on_unload(self.entry.add_update_listener(self.config_entry_update_listener))
        
        # Schedule startup completion after a delay to allow Home Assistant to finish starting up
        async def mark_startup_complete(_):
            self._hass_startup_complete = True
            LOGGER.info("Home Assistant startup complete - MQTT message processing enabled")
            
            # Trigger entity availability updates for all dongles now that startup is complete
            for dongle_id in self._dongle_ids:
                if self.is_gridboss_dongle(dongle_id):
                    self._trigger_entity_availability_update(dongle_id)
        
        # Wait 30 seconds after setup to allow Home Assistant to finish starting up
        async_call_later(self.hass, 30, mark_startup_complete)
        
        return True

    def set_battery_async_add_entities(self, async_add_entities) -> None:
        """Store the async_add_entities callback for battery sensors."""
        self._battery_async_add_entities = async_add_entities

    async def request_firmware_codes(self):
        """Request firmware codes for dongles that don't have them saved."""
        dongles_needing_firmware = [dongle_id for dongle_id in self._dongle_ids if not self._firmware_codes.get(dongle_id)]
        
        if not dongles_needing_firmware:
            LOGGER.info("All firmware codes already saved, proceeding with entity creation")
            await self._create_entities_for_all_dongles()
            return
        
        LOGGER.debug(f"Requesting firmware codes for {len(dongles_needing_firmware)} dongles (already have {len(self._dongle_ids) - len(dongles_needing_firmware)})")
        
        # Request firmware codes only for dongles that don't have them
        for dongle_id in dongles_needing_firmware:
            LOGGER.debug(f"Requesting firmware code for dongle {dongle_id}...")
            firmware_topic = f"{dongle_id}/firmwarecode/response"
            
            try:
                # Subscribe to firmware code response for this dongle
                unsubscribe_callback = await mqtt.async_subscribe(
                    self.hass, firmware_topic, self._async_handle_mqtt_message
                )
                
                self._mqtt_unsubscribe_callbacks[f"{dongle_id}_firmware"] = unsubscribe_callback
                LOGGER.debug(f"Successfully subscribed to {firmware_topic}")
                
                # Publish request for firmware code
                await mqtt.async_publish(
                    self.hass, f"{dongle_id}/firmwarecode/request", ""
                )
                LOGGER.debug(f"Published firmware code request to {dongle_id}/firmwarecode/request")
            except Exception as e:
                LOGGER.error(f"Error setting up MQTT for dongle {dongle_id}: {e}")
        
        # Log which dongles already have firmware codes
        for dongle_id in self._dongle_ids:
            if self._firmware_codes.get(dongle_id):
                LOGGER.debug(f"Firmware code already saved for dongle {dongle_id}: {self._firmware_codes[dongle_id]}")

        # Log all active subscriptions to verify
        LOGGER.debug(f"Active MQTT subscriptions: {list(self._mqtt_unsubscribe_callbacks.keys())}")

        # Set up timeout to handle case where firmware codes are not received
        async def firmware_timeout(_):
            if self._pending_dongles:
                LOGGER.error(f"Firmware code responses not received for dongles: {self._pending_dongles}")
                # Log active subscriptions for diagnostic purposes
                LOGGER.debug(f"Current active MQTT subscriptions: {list(self._mqtt_unsubscribe_callbacks.keys())}")
                
                # Create default entities for dongles that didn't respond (assume regular inverter)
                for dongle_id in self._pending_dongles:
                    LOGGER.warning(f"Creating default entities for dongle {dongle_id} (no firmware code received)")
                    await self._create_entities_for_dongle(dongle_id)
                
                # Clear pending dongles
                self._pending_dongles.clear()
                
        async_call_later(self.hass, 15, firmware_timeout)
        
    async def start_mqtt_subscription(self):
        """Start listening to all MQTT topics for all dongles."""
        LOGGER.debug(f"Starting subscription to all MQTT topics for {len(self._dongle_ids)} dongles")
        
        # Log all pending dongles at this point
        if self._pending_dongles:
            LOGGER.warning(f"Starting MQTT subscription with pending dongles: {self._pending_dongles}")
        
        # Clean up firmware-only subscriptions
        firmware_subscriptions = [key for key in self._mqtt_unsubscribe_callbacks.keys() if '_firmware' in key]
        LOGGER.debug(f"Cleaning up {len(firmware_subscriptions)} firmware-only subscriptions: {firmware_subscriptions}")
        
        for key in firmware_subscriptions:
            try:
                unsubscribe = self._mqtt_unsubscribe_callbacks[key]
                unsubscribe()
                del self._mqtt_unsubscribe_callbacks[key]
                LOGGER.debug(f"Successfully unsubscribed from firmware topic {key}")
            except Exception as e:
                LOGGER.error(f"Error unsubscribing from firmware topic {key}: {e}")
        
        # Subscribe to all topics for all dongles
        subscription_success = True
        for dongle_id in self._dongle_ids:
            try:
                # Check if we already have a subscription for this dongle
                if dongle_id in self._mqtt_unsubscribe_callbacks:
                    LOGGER.debug(f"Already subscribed to MQTT topics for {dongle_id}")
                    continue
                    
                topic_pattern = f"{dongle_id}/#"
                self._mqtt_unsubscribe_callbacks[dongle_id] = await mqtt.async_subscribe(
                    self.hass, topic_pattern, self._async_handle_mqtt_message
                )
                LOGGER.debug(f"Subscribed to all MQTT topics for {dongle_id} with pattern {topic_pattern}")
                
                # If this is a GridBoss dongle, subscribe to GridBoss specific topics
                if self.is_gridboss_dongle(dongle_id):
                    gridboss_topics = [
                        f"{dongle_id}/gridboss_inputbank1",
                        f"{dongle_id}/gridboss_inputbank2",
                        f"{dongle_id}/gridboss_holdbank1",
                        f"{dongle_id}/gridboss_holdbank2",
                        f"{dongle_id}/gridboss_holdbank3"
                    ]
                    
                    for topic in gridboss_topics:
                        try:
                            unsubscribe_callback = await mqtt.async_subscribe(
                                self.hass, topic, self._async_handle_mqtt_message
                            )
                            self._mqtt_unsubscribe_callbacks[f"{dongle_id}_gridboss_{topic.split('/')[-1]}"] = unsubscribe_callback
                            LOGGER.debug(f"Subscribed to GridBoss topic: {topic}")
                        except Exception as e:
                            LOGGER.error(f"Failed to subscribe to GridBoss topic {topic}: {e}")
            except Exception as e:
                LOGGER.error(f"Failed to subscribe to MQTT topics for {dongle_id}: {e}")
                subscription_success = False
        
        if not subscription_success:
            LOGGER.warning("One or more MQTT subscriptions failed, some functionality may be limited")

        # Log all active subscriptions
        LOGGER.debug(f"Active MQTT subscriptions after setup: {list(self._mqtt_unsubscribe_callbacks.keys())}")

        # Full-data snapshot bootstrap (FW >= 4.3.0 streams change-data only).
        #
        # We must NOT request the snapshot here: at this point the platforms have
        # been forwarded but each entity's async_added_to_hass (where it subscribes
        # to the coordinator) is only *scheduled*, not yet run. The snap/input reply
        # comes back within ~1s; if it lands before the input sensors have finished
        # subscribing, their async_set_updated_data fan-out misses them and they sit
        # at 'unknown' until a later change-data delta happens to carry that key —
        # which for static fields (SOC when idle, settings, etc.) may be never.
        # (Verified on a live dongle: hold populated but input did not, and the
        # difference was purely this timing window.)
        #
        # So defer the request to a short settle delay, by which point every
        # entity's coordinator subscription is live. fail-open: request_snapshot()
        # with no version requests anyway, and old firmware ignores the topic.
        # force=True bypasses the per-session dedup but still records the dongle, so
        # the later /status-driven call won't double-send on this same connect.
        #
        # The /status (version-confirmed) and /availability offline->online paths
        # remain the triggers for reconnect/reboot recovery — see
        # process_status_message() and request_snapshot().
        async def _request_initial_snapshots(*_):
            for dongle_id in self._dongle_ids:
                await self.request_snapshot(dongle_id, version="", force=True)

        # Fire once HA has fully started (async_at_started runs immediately if HA
        # is already running, e.g. a config-entry reload), then a short settle so
        # the just-added entities have finished subscribing to the coordinator
        # before the snapshot reply lands.
        from homeassistant.helpers.start import async_at_started

        @callback
        def _schedule_snapshot(_event):
            async_call_later(self.hass, 2, _request_initial_snapshots)

        async_at_started(self.hass, _schedule_snapshot)

        # Schedule a one-time log of ignored entity counts after 2 minutes
        async def log_ignored_entities(_):
            ignored_count = len(self._ignored_entity_suffixes)
            if ignored_count > 0:
                LOGGER.info(f"Total of {ignored_count} unique unmatched entity suffixes were ignored to reduce log spam")
        
        async_call_later(self.hass, 120, log_ignored_entities)  # Log after 2 minutes
        
    async def stop_mqtt_subscription(self):
        """Stop all MQTT subscriptions."""
        LOGGER.debug(f"Stopping MQTT subscriptions for all dongles")
        for key, unsubscribe in list(self._mqtt_unsubscribe_callbacks.items()):
            try:
                unsubscribe()
                del self._mqtt_unsubscribe_callbacks[key]
                LOGGER.debug(f"Successfully unsubscribed from MQTT topics for {key}")
            except Exception as e:
                LOGGER.error(f"Error unsubscribing from MQTT for {key}: {e}")

    async def _async_update_data(self) -> None:
        """Update data."""
        return self.data

    async def config_entry_update_listener(self, hass: HomeAssistant, entry: MonitorMySolarEntry) -> None:
        """Update listener, called when the config entry options are changed."""
        await hass.config_entries.async_reload(entry.entry_id)
        
    def get_ignored_entity_suffixes(self) -> Set[str]:
        """Return the set of ignored entity suffixes for diagnostic purposes."""
        return self._ignored_entity_suffixes

    async def process_status_message(self, dongle_id: str, payload):
        """Process incoming status MQTT message and update the status sensor."""
        if payload is None or len(payload.strip()) == 0:
            return
        try:
            data = json.loads(payload)
        except ValueError:
            LOGGER.error(f"Invalid JSON payload received for status message from {dongle_id}: {payload}")
            return

        # Check if the message follows the new structure with 'Serialnumber' and 'payload'
        if "Serialnumber" in data and "payload" in data:
            serial_number = data["Serialnumber"]
            status_data = data["payload"]
        else:
            serial_number = None  # For backward compatibility
            status_data = data  # Old format

        entity_id = self.build_entity_id("sensor", dongle_id, "uptime")
        self.entities[entity_id] = status_data

        # The /status payload carries the real dongle firmware version (e.g.
        # "4.3.0.111S3"). Record it and, on the first status seen this session,
        # ask FW >= 4.3.0 dongles for a full snapshot — they only stream
        # change-data, so entities stay 'unknown' until this bootstrap runs.
        version = ""
        boot_count = None
        if isinstance(status_data, dict):
            version = status_data.get("version", "") or ""
            boot = status_data.get("boot")
            if isinstance(boot, dict):
                boot_count = boot.get("count")
        if version:
            self.current_fw_versions[dongle_id] = version

        # Detect a silent reboot: if boot.count changed since we last saw it (and
        # this isn't the first sighting), the dongle restarted without dropping its
        # MQTT session, so /availability never flipped. Force a fresh snapshot —
        # its in-memory change-data baseline reset on reboot.
        reboot_detected = False
        if isinstance(boot_count, int):
            previous = self._dongle_boot_count.get(dongle_id)
            if previous is not None and boot_count != previous:
                reboot_detected = True
                LOGGER.info(
                    "Detected reboot of %s (boot.count %s -> %s), refreshing snapshot",
                    dongle_id, previous, boot_count,
                )
            self._dongle_boot_count[dongle_id] = boot_count

        if reboot_detected:
            # A reboot (even one that kept the MQTT session, so /availability never
            # flipped) resets the dongle's change-data baseline — recover.
            await self.request_recovery_snapshot(dongle_id, "reboot detected")
        else:
            # First-status bootstrap (deduped once per session).
            await self.request_snapshot(dongle_id, version)

        # Push the update so status-derived sensors (uptime + the /status
        # diagnostic sensors) refresh. /status arrives ~every 30s — far less often
        # than the /input + /hold change-data that already drives this same push —
        # so the extra fan-out is marginal. Not gated on _hass_startup_complete so
        # the diagnostic sensors populate on the very first status, rather than
        # waiting up to a full heartbeat after startup finishes.
        self.async_set_updated_data(self.entities)

    async def process_message(self, dongle_id: str, topic, payload):
        """Process incoming MQTT message and update entity states."""
        if payload is None or len(payload.strip()) == 0:
            return

        # LWT/birth on <dongle>/availability is a plain "online"/"offline"
        # string, not JSON. Track it and skip the JSON decoder.
        if topic.endswith("/availability"):
            state = payload.strip().lower()
            was_online = self._dongle_availability.get(dongle_id)
            is_online = (state == "online")
            self._dongle_availability[dongle_id] = is_online
            LOGGER.debug(f"availability {dongle_id}={state}")
            # Force a fresh snapshot on ANY 'online' message except the very first
            # one we ever see (was_online is None -> the /status bootstrap handles
            # the initial populate). We can't rely on a clean offline->online
            # transition: on a fast restart the LWT 'offline' is often missed (or
            # the birth message is retained), so the state would read online->online
            # and entities would stay unavailable. request_recovery_snapshot is
            # debounced, so repeated 'online' messages don't spam the dongle.
            if is_online and was_online is not None:
                await self.request_recovery_snapshot(dongle_id, "availability online")
            return

        try:
            data = json.loads(payload)
            bank_name = topic.split('/')[-1]  # Gets 'inputbank1', 'holdbank2', etc.
            self.hass.bus.async_fire(f"{DOMAIN}_bank_updated", {"bank_name": bank_name, "dongle_id": dongle_id})
        except ValueError:
            LOGGER.error(f"Invalid JSON payload received from {dongle_id} on topic {topic}: {payload}")
            return

        # Durable write-confirmation channel (dongle FW >= 4.3.0):
        # <dongle>/setting/updated arrives on every successful write
        # regardless of who initiated it (HA itself, MMS, Lux server, HA
        # TCP, the local web UI). Envelope: {setting, value, reg, from, ts}.
        # We mirror the new value to the matching entity so HA's state
        # converges within ~1 ms instead of waiting for the next /hold
        # cycle. `from` lets us self-dedup if we just wrote it ourselves
        # (avoids overwriting an optimistic in-flight write).
        if topic.endswith("/setting/updated") and isinstance(data, dict):
            setting = data.get("setting")
            value = data.get("value")
            from_who = data.get("from") or ""
            if setting and value is not None:
                formatted_suffix = setting.lower().replace("-", "_").replace(":", "_")
                # Resolve the platform AND catalog entry so we can coerce the
                # value (FW >= 4.3.0 sends it as a string like "1.00") to the
                # entity's native type — an int index for selects, float for
                # numbers, etc. Without this a select lands a raw "1.00" that
                # matches no option and renders 'unknown'.
                entity_type, entry = self.find_catalog_entry(formatted_suffix)
                if entity_type is None:
                    entity_type = self.determine_entity_type(formatted_suffix)
                normalized = self.normalize_setting_value(entity_type, entry, value)
                entity_id = self.build_entity_id(entity_type, dongle_id, formatted_suffix)

                # Dedup the dual FW >= 4.3.0 confirmation: if HA itself just
                # wrote this same value, /response already applied it (and drove
                # the optimistic state). Skip the redundant refresh here so we
                # don't process the same write twice. Echoes for writes we didn't
                # make have no ledger entry and fall through normally.
                if self._is_own_recent_write(dongle_id, formatted_suffix, normalized):
                    LOGGER.debug(
                        f"setting/updated deduped (own write): {entity_id}={normalized!r}"
                    )
                    return

                self.entities[entity_id] = normalized
                self.async_set_updated_data(self.entities)
                LOGGER.debug(
                    f"setting/updated routed: {entity_id}={normalized!r} "
                    f"(raw={value!r}, type={entity_type}, from={from_who})"
                )
            return

        # Handle new payload structure while maintaining backward compatibility
        serial_number = None
        payload_data = {}
        events_data = {}
        fault_data = {}
        warning_data = {}

        if isinstance(data, dict):
            if "Serialnumber" in data:
                serial_number = data.get("Serialnumber")

            if "payload" in data:
                # New format with data wrapper
                payload_data = data["payload"]
                events_data = data.get("events", {})
                # Get fault and warning data from events object
                fault_data = events_data.get("fault", {})
                warning_data = events_data.get("warning", {})
            else:
                # Old format - direct key-value pairs
                payload_data = data
                
        # Handle special cases first
        if "SW_VERSION" in payload_data:
            fw_version = payload_data["SW_VERSION"]
            self.current_fw_versions[dongle_id] = fw_version
            # Set entity value
            entity_id = self.build_entity_id("update", dongle_id, "firmware_update")
            self.entities[entity_id] = fw_version

        # Inverter FWCode fallback path. v4.3+ dongles no longer publish
        # `holdbank1` so the legacy /firmwarecode/request → /response
        # handshake can race the dongle boot and time out at HA's 15s
        # firmware_timeout. The unified /hold topic carries FWCode in
        # every payload (it's part of the standard hold superset), so
        # scrape it here and feed it through save_firmware_code which
        # also persists it to the config entry.
        if "FWCode" in payload_data:
            fw_code = payload_data["FWCode"]
            if fw_code and self._firmware_codes.get(dongle_id) != fw_code:
                # Fire-and-forget — save_firmware_code is async but we're
                # already inside an async handler so schedule it.
                self.hass.async_create_task(
                    self.save_firmware_code(dongle_id, fw_code)
                )
                # If this dongle was waiting for the legacy handshake,
                # clear it from the pending set so the 15s timeout
                # doesn't fire the "default entities" warning.
                if hasattr(self, "_pending_dongles") and dongle_id in self._pending_dongles:
                    self._pending_dongles.discard(dongle_id)
                    LOGGER.debug(
                        f"FWCode {fw_code!r} resolved for {dongle_id} via /hold payload — pending cleared"
                    )

        # Update UI version - commented out as UI update entity has been removed
        # if "UI_VERSION" in payload_data:
        #     ui_version = payload_data["UI_VERSION"]
        #     self.current_ui_versions[dongle_id] = ui_version
        #     #LOGGER.debug(f"Current UI version set for {dongle_id}: {ui_version}")
        #     # Set entity value
        #     entity_id = f"update.{formatted_dongle_id}_ui_update"
        #     self.entities[entity_id] = ui_version

        # Process fault data
        if fault_data:
            # Check if this fault data is the same as the last one to prevent duplicate processing
            fault_key = f"{dongle_id}_fault"
            if fault_key in self._last_fault_warning_data and self._last_fault_warning_data[fault_key] == fault_data:
                # Skip duplicate fault data
                pass
            else:
                # LOGGER.debug(f"Processing fault data for {dongle_id}: {fault_data}")
                self._last_fault_warning_data[fault_key] = fault_data
                fault_value = fault_data.get("value", 0)
                entity_id = self.build_entity_id("sensor", dongle_id, "fault_status")

                if fault_value == 0:
                    self.entities[entity_id] = {
                        "value": 0,
                        "description": None  # This will trigger "No Fault" state
                    }
                else:
                    descriptions = fault_data.get("descriptions", ["Unknown Fault"])
                    timestamp = fault_data.get("timestamp", "Unknown")
                    self.entities[entity_id] = {
                        "value": fault_value,
                        "description": ", ".join(descriptions),
                        "start_time": timestamp,
                        "end_time": "Ongoing"
                    }

        # Process warning data
        if warning_data:
            # Check if this warning data is the same as the last one to prevent duplicate processing
            warning_key = f"{dongle_id}_warning"
            if warning_key in self._last_fault_warning_data and self._last_fault_warning_data[warning_key] == warning_data:
                # Skip duplicate warning data
                pass
            else:
                # LOGGER.debug(f"Processing warning data for {dongle_id}: {warning_data}")
                self._last_fault_warning_data[warning_key] = warning_data
                warning_value = warning_data.get("value", 0)
                entity_id = self.build_entity_id("sensor", dongle_id, "warning_status")

                if warning_value == 0:
                    self.entities[entity_id] = {
                        "value": 0,
                        "description": None  # This will trigger "No Warning" state
                    }
                else:
                    descriptions = warning_data.get("descriptions", ["Unknown Warning"])
                    timestamp = warning_data.get("timestamp", "Unknown")
                    self.entities[entity_id] = {
                        "value": warning_value,
                        "description": ", ".join(descriptions),
                        "start_time": timestamp,
                        "end_time": "Ongoing"
                    }
                
        # Process main sensor data - now with more efficient entity type determination
        # For GridBoss, we need to handle the nested structure properly
        if self.is_gridboss_dongle(dongle_id):
            # Process GridBoss nested structure correctly
            self._process_gridboss_nested_data(dongle_id, payload_data)
        else:
            # Process regular inverter data
            for entity_id_suffix, state in payload_data.items():
                # Skip if we've already handled these keys
                if entity_id_suffix in ("SW_VERSION", "UI_VERSION"):
                    continue
                
                # Process charge/discharge control settings for conditional entities
                if entity_id_suffix == "ubBatChgcontrol":
                    self.update_charge_control_setting(dongle_id, state)
                elif entity_id_suffix == "ubBatDischgControl":
                    self.update_discharge_control_setting(dongle_id, state)
                elif entity_id_suffix == "ACChargeType":
                    LOGGER.debug(f"Processing ACChargeType from MQTT: {state}")
                    self.update_charge_type_setting(dongle_id, state)
                    
                formatted_entity_id_suffix = entity_id_suffix.lower().replace("-", "_").replace(":", "_")
                entity_type = self.determine_entity_type(formatted_entity_id_suffix)
                entity_id = self.build_entity_id(entity_type, dongle_id, formatted_entity_id_suffix)
                self.entities[entity_id] = state

        # Process events data if present (new format)
        if events_data:
            for event_id, event_state in events_data.items():
                # Skip fault and warning which are handled separately
                if event_id in ("fault", "warning"):
                    continue

                formatted_event_id = event_id.lower().replace("-", "_").replace(":", "_")
                entity_id = self.build_entity_id("binary_sensor", dongle_id, formatted_event_id)
                self.entities[entity_id] = event_state
        
        # Update coordinator data after processing all entities
        self.async_set_updated_data(self.entities)
    

    def find_catalog_entry(self, entity_id_suffix):
        """Return (entity_type, entry_dict) for a setting key, or (None, None).

        Used by the /setting/updated durable-confirmation channel to learn a
        setting's platform AND its metadata (e.g. a select's option list) so the
        raw value can be normalized to the entity's native representation before
        it lands in the coordinator.
        """
        suffix_lower = entity_id_suffix.lower()
        brand_entities = ENTITIES.get(self.inverter_brand, {})
        if not brand_entities:
            return None, None
        for entity_type in ["sensor", "switch", "number", "time", "time_hhmm", "button", "select"]:
            if entity_type in brand_entities:
                for _bank, entries in brand_entities[entity_type].items():
                    for entry in entries:
                        if entry["unique_id"].lower() == suffix_lower:
                            resolved = "time" if entity_type == "time_hhmm" else entity_type
                            return resolved, entry
        return None, None

    def normalize_setting_value(self, entity_type, entry, value):
        """Coerce a /setting/updated raw value to the entity's native type.

        FW >= 4.3.0 emits every write on <dongle>/setting/updated with the value
        formatted as a STRING (e.g. "1.00" for a numeric register). Each platform
        expects a specific Python type in coordinator.entities:
          - select : int option index (decoded from "1.00" -> 1)
          - number : float (or int)
          - switch : int/bool 0/1
          - time   : string, left as-is
        Anything we can't confidently coerce is returned unchanged so the caller
        (and the entity's _handle_coordinator_update) can fall back safely.
        """
        if value is None:
            return None

        # A numeric-looking string like "1.00" -> number. Keep the parsed float
        # around for the int-index / float paths below.
        num = None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            num = float(value)
        elif isinstance(value, str):
            try:
                num = float(value.strip())
            except (ValueError, AttributeError):
                num = None

        if entity_type == "select":
            options = (entry or {}).get("options") or []
            # Already a valid option label? Leave it.
            if value in options:
                return value
            if num is not None:
                idx = int(round(num))
                if 0 <= idx < len(options):
                    return idx  # int index -> select decodes to the label
            return value  # unknown form; let the entity decide
        if entity_type == "number":
            if num is not None:
                # Preserve integers as int where the value is whole.
                return int(num) if num.is_integer() else num
            return value
        if entity_type == "switch":
            if num is not None:
                return 1 if num != 0 else 0
            return value
        # time / sensor / anything else: pass through untouched.
        return value

    def record_self_write(self, dongle_id: str, setting: str, value) -> None:
        """Note a value HA just wrote, so its /setting/updated echo can be deduped.

        `setting` is normalized to the same suffix form used when routing the
        echo. Called from the MQTT handler right after publishing a write.
        """
        suffix = setting.lower().replace("-", "_").replace(":", "_")
        entity_type, entry = self.find_catalog_entry(suffix)
        if entity_type is None:
            entity_type = self.determine_entity_type(suffix)
        normalized = self.normalize_setting_value(entity_type, entry, value)
        if not hasattr(self, "_self_write_ledger"):
            self._self_write_ledger = {}
        self._self_write_ledger[(dongle_id, suffix)] = (normalized, time.monotonic())

    def _is_own_recent_write(self, dongle_id: str, suffix: str, normalized_value) -> bool:
        """True if HA just wrote this exact (setting, value) within the window."""
        ledger = getattr(self, "_self_write_ledger", None)
        if ledger is None:
            return False
        entry = ledger.get((dongle_id, suffix))
        if not entry:
            return False
        recorded_value, ts = entry
        window = getattr(self, "_self_write_dedup_window", 10.0)
        if (time.monotonic() - ts) > window:
            # Stale — drop it so a later external write isn't wrongly deduped.
            ledger.pop((dongle_id, suffix), None)
            return False
        if recorded_value == normalized_value:
            # Consume it: the echo has now been accounted for.
            ledger.pop((dongle_id, suffix), None)
            return True
        return False

    def determine_entity_type(self, entity_id_suffix):
        """Determine the entity type based on the entity_id_suffix."""
        entity_id_suffix_lower = entity_id_suffix.lower()
        
        # Check if we've already logged this entity suffix before
        if entity_id_suffix_lower in self._ignored_entity_suffixes:
            return "sensor"  # Default to sensor without logging
        
        brand_entities = ENTITIES.get(self.inverter_brand, {})
        if not brand_entities:
            # Only log this once per brand
            if self.inverter_brand not in self._ignored_entity_suffixes:
                #LOGGER.debug(f"No entities defined for inverter brand: {self.inverter_brand}. Defaulting to 'sensor'.")
                self._ignored_entity_suffixes.add(self.inverter_brand)
            return "sensor"

        for entity_type in ["sensor", "switch", "number", "time", "time_hhmm", "button", "select"]:
            if entity_type in brand_entities:
                for bank_name, entities in brand_entities[entity_type].items():
                    for entity in entities:
                        unique_id_lower = entity["unique_id"].lower()
                        if unique_id_lower == entity_id_suffix_lower:
                            if entity_type == "time_hhmm":
                                return "time"
                            return entity_type

        # If we get here, we couldn't match the entity suffix
        # Log it once and add to ignore list
        #LOGGER.debug(f"Could not match entity_id_suffix '{entity_id_suffix_lower}'. Defaulting to 'sensor'.")
        self._ignored_entity_suffixes.add(entity_id_suffix_lower)
        return "sensor"