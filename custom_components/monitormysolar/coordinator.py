from __future__ import annotations
import json
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
        
        # Get dongle IDs from config entry data (fallback to single dongle ID for backward compatibility)
        self._dongle_ids: List[str] = entry.data.get("dongle_ids", [entry.data.get("dongle_id")])
        # Get dongle IPs (may be empty strings if not provided)
        self._dongle_ips: List[str] = entry.data.get("dongle_ips", [""] * len(self._dongle_ids))
        
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
        self._has_gridboss = entry.data.get("has_gridboss", False)  # Track if GridBoss is enabled
        self._gridboss_dongle = entry.data.get("gridboss_dongle", "")  # Track which dongle is GridBoss
        self._last_fault_warning_data = {}  # Track last fault/warning data to prevent duplicate processing
        self._hass_startup_complete = False  # Track if Home Assistant has finished starting up
        self._smart_soc_volt_bits = {}  # Track SmartSOCVoltBits for each dongle
        self._smartload_bits = {}  # Track SmartLoad Bits for each dongle
        self._port_modes = {}  # Track Port Mode settings for each dongle

        super().__init__(
            hass,
            LOGGER,
            name="MonitorySolar Coordinator",
            setup_method=self.async_setup
        )

    def get_formatted_dongle_id(self, dongle_id: str) -> str:
        """Convert a dongle ID to the formatted version used in entity IDs."""
        return dongle_id.lower().replace("-", "_").replace(":", "_")
    

    @property
    def inverter_brand(self) -> str:
        """The brand of the inverter."""
        return cast(str, self.entry.data["inverter_brand"])
    
    @property
    def has_gridboss(self) -> bool:
        """Check if GridBoss is enabled."""
        return self._has_gridboss
    
    def is_gridboss_dongle(self, dongle_id: str) -> bool:
        """Check if a specific dongle is the GridBoss dongle."""
        # First check if firmware code indicates GridBoss (IAAB)
        firmware_code = self.get_firmware_code(dongle_id)
        if firmware_code == "IAAB":
            return True
        
        # If no firmware code yet, check config flow setting
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
        LOGGER.debug(f"Updated SmartSOCVoltBits for {dongle_id}: {smart_soc_volt_bits}")
        
        # If the bits changed, trigger entity updates
        if old_bits != smart_soc_volt_bits:
            self._trigger_entity_availability_update(dongle_id)
    
    def _trigger_entity_availability_update(self, dongle_id: str):
        """Trigger entity availability updates for a dongle."""
        # Don't trigger updates during startup
        if not self._hass_startup_complete:
            LOGGER.debug(f"Skipping entity availability update for {dongle_id} - HA startup not complete")
            return
        
        # Add a small delay to allow MQTT responses to be processed first
        # This prevents availability logic from blocking legitimate user actions
        from homeassistant.helpers.event import async_call_later
        async_call_later(self.hass, 2, self._async_update_entity_availability, dongle_id)
    
    async def _async_update_entity_availability(self, dongle_id: str):
        """Update entity availability states."""
        try:
            # Simply trigger a single coordinator update to refresh entity availability
            # The entities will check their availability in their available() property
            self.async_set_updated_data(self.entities)
            LOGGER.debug(f"Triggered entity availability update for {dongle_id}")
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
        LOGGER.debug(f"Updated SmartLoad Bits for {dongle_id}: {smartload_bits}")
        
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
        LOGGER.debug(f"Updated Port Modes for {dongle_id}: {port_modes}")
        
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
                LOGGER.debug(f"Entity {entity_unique_id}: SOC/Volt mode select, Port Mode={port_mode}, available")
                return True
            else:
                LOGGER.debug(f"Entity {entity_unique_id}: SOC/Volt mode select, Port Mode={port_mode}, not available")
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
        LOGGER.debug(f"Entity {entity_unique_id}: SmartLoad{smartload_number} Port Mode={port_mode}")
        
        # If Port Mode is "Does Not Operate" (0), no entities are available
        if port_mode == 0:
            LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=0, entity not available")
            return False
        
        # Step 2: Check entity type based on Port Mode
        if port_mode == 1:  # Smart Load mode
            # Smart Load entities are available
            if "SmartLoad" in entity_unique_id and "ACcouple" not in entity_unique_id:
                # Step 3: Check SOC/Volt vs Time mode for Smart Load entities
                if self._is_soc_volt_entity(entity_unique_id):
                    soc_volt_enabled = self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
                    LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, SOC/Volt entity, SOC/Volt enabled={soc_volt_enabled}")
                    return soc_volt_enabled
                elif self._is_time_entity(entity_unique_id):
                    time_enabled = not self.is_smartload_soc_volt_enabled(dongle_id, smartload_number)
                    LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, Time entity, Time enabled={time_enabled}")
                    return time_enabled
                else:
                    # Enable/Disable switches are always available when Port Mode is Smart Load
                    if "Enable" in entity_unique_id:
                        LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, Enable switch, always available")
                        return True
                    # Other entities are available if SmartLoad is enabled
                    smartload_enabled = self.is_smartload_enabled(dongle_id, smartload_number)
                    LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, Other entity, SmartLoad enabled={smartload_enabled}")
                    return smartload_enabled
            LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=1, but not a SmartLoad entity")
            return False
            
        elif port_mode == 2:  # AC Coupled mode
            # AC Coupled entities are available
            if "ACcouple" in entity_unique_id:
                # AC Coupled enable switches are always available when Port Mode is AC Coupled
                if "Enable" in entity_unique_id:
                    LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=2, AC Coupled Enable switch, always available")
                    return True
                # Other AC Coupled entities are available
                LOGGER.debug(f"Entity {entity_unique_id}: Port Mode=2, AC Coupled entity, available")
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
    
    def is_entity_available_for_smartload(self, dongle_id: str, entity_unique_id: str) -> bool:
        """Check if an entity should be available based on Port Mode, SOC/Volt settings, and SmartLoad enable state."""
        # Use the new hierarchical availability logic
        return self.is_entity_available_for_smartload_enable(dongle_id, entity_unique_id)

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
    
    def get_dongle_ip(self, dongle_id: str) -> str:
        """Get IP address for a specific dongle."""
        try:
            index = self._dongle_ids.index(dongle_id)
            return self._dongle_ips[index] if index < len(self._dongle_ips) else ""
        except ValueError:
            return ""
    
    def get_sync_settings_enabled(self) -> bool:
        """Get the current sync settings state."""
        return self._sync_settings_enabled
    
    def set_sync_settings_enabled(self, enabled: bool) -> None:
        """Set the sync settings state."""
        self._sync_settings_enabled = enabled
        LOGGER.debug(f"Sync settings state set to: {enabled}")
    
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
        
        LOGGER.debug(f"Recorded setting change: {dongle_id}/{unique_id} = {value} at {timestamp}")
    
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
            
            # Always process firmware code responses as they're needed for setup
            if topic.endswith("/firmwarecode/response"):
                await self._handle_firmware_code_response(dongle_id, msg)
            # Skip other message processing during startup to prevent excessive updates
            elif not self._hass_startup_complete:
                # Just store the message for later processing if needed
                pass
            else:
                # Process messages normally after startup is complete
                if topic.endswith("/response"):
                    await self.mqtt_handler.response_received(msg)
                elif topic.endswith("/status"):
                    await self.process_status_message(dongle_id, msg.payload)
                else:
                    await self.process_message(dongle_id, topic, msg.payload)
                    
                self.async_set_updated_data(self.entities)
        except Exception as e:
            LOGGER.error(f"Error processing MQTT message on topic {topic}: {e}")
            # Only update data after startup is complete
            if self._hass_startup_complete:
                self.async_set_updated_data(self.entities)

    async def _handle_firmware_code_response(self, dongle_id: str, msg) -> None:
        """Handle firmware code response."""
        LOGGER.debug(f"Received firmware code response for dongle {dongle_id}")
        try:
            data = json.loads(msg.payload)
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
    
    def _process_gridboss_nested_data(self, dongle_id: str, payload_data):
        """Process GridBoss nested payload structure - now simplified since payload has correct entity names."""
        formatted_dongle_id = self.get_formatted_dongle_id(dongle_id)
        
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
            entity_id = f"{entity_type}.{formatted_dongle_id}_{formatted_entity_id_suffix}"
            self.entities[entity_id] = state

    async def _create_entities_for_dongle(self, dongle_id: str):
        """Create entities for a specific dongle after firmware code is received."""
        formatted_dongle_id = self.get_formatted_dongle_id(dongle_id)
        is_gridboss = self.is_gridboss_dongle(dongle_id)
        
        # Get brand entities
        brand_entities = ENTITIES.get(self.inverter_brand, {})
        if not brand_entities:
            LOGGER.error(f"No entities defined for inverter brand: {self.inverter_brand}")
            return
        
        entities_created = 0
        for entityTypeName, entityTypes in brand_entities.items():
            for typeName, entities in entityTypes.items():
                for entity in entities:
                    # For GridBoss dongles, only create GridBoss-specific entities
                    if is_gridboss and not typeName.startswith("gridboss_"):
                        continue
                    # For non-GridBoss dongles, skip GridBoss-specific entities
                    elif not is_gridboss and typeName.startswith("gridboss_"):
                        continue
                        
                    entity_id: str = f"{entityTypeName}.{formatted_dongle_id}_{entity['unique_id'].lower()}"
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
            LOGGER.error(f"Invalid JSON payload received for status message from {dongle_id}")
            return

        # Check if the message follows the new structure with 'Serialnumber' and 'payload'
        if "Serialnumber" in data and "payload" in data:
            serial_number = data["Serialnumber"]
            status_data = data["payload"]
        else:
            serial_number = None  # For backward compatibility
            status_data = data  # Old format

        formatted_dongle_id = self.get_formatted_dongle_id(dongle_id)
        entity_id = f"sensor.{formatted_dongle_id}_uptime"
        self.entities[entity_id] = status_data
        
        # Don't update coordinator data for status messages - they're too frequent
        # The main message processing will handle coordinator updates

    async def process_message(self, dongle_id: str, topic, payload):
        """Process incoming MQTT message and update entity states."""
        if payload is None or len(payload.strip()) == 0:
            return
        
        try:
            data = json.loads(payload)
            bank_name = topic.split('/')[-1]  # Gets 'inputbank1', 'holdbank2', etc.
            self.hass.bus.async_fire(f"{DOMAIN}_bank_updated", {"bank_name": bank_name, "dongle_id": dongle_id})
        except ValueError:
            LOGGER.error(f"Invalid JSON payload received from {dongle_id}")
            return

        formatted_dongle_id = self.get_formatted_dongle_id(dongle_id)

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
            entity_id = f"update.{formatted_dongle_id}_firmware_update"
            self.entities[entity_id] = fw_version

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
                LOGGER.debug(f"Processing fault data for {dongle_id}: {fault_data}")
                self._last_fault_warning_data[fault_key] = fault_data
                fault_value = fault_data.get("value", 0)
                entity_id = f"sensor.{formatted_dongle_id}_fault_status"

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
                LOGGER.debug(f"Processing warning data for {dongle_id}: {warning_data}")
                self._last_fault_warning_data[warning_key] = warning_data
                warning_value = warning_data.get("value", 0)
                entity_id = f"sensor.{formatted_dongle_id}_warning_status"

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
                    
                formatted_entity_id_suffix = entity_id_suffix.lower().replace("-", "_").replace(":", "_")
                entity_type = self.determine_entity_type(formatted_entity_id_suffix)
                entity_id = f"{entity_type}.{formatted_dongle_id}_{formatted_entity_id_suffix}"
                self.entities[entity_id] = state
            
        # Process events data if present (new format)
        if events_data:
            for event_id, event_state in events_data.items():
                # Skip fault and warning which are handled separately
                if event_id in ("fault", "warning"):
                    continue
                    
                formatted_event_id = event_id.lower().replace("-", "_").replace(":", "_")
                entity_id = f"binary_sensor.{formatted_dongle_id}_{formatted_event_id}"
                self.entities[entity_id] = event_state
        
        # Update coordinator data after processing all entities
        self.async_set_updated_data(self.entities)
    

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