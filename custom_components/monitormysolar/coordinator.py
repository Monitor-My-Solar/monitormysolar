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
        
        # Initialize per-dongle data structures
        self._firmware_codes: Dict[str, str] = {dongle_id: None for dongle_id in self._dongle_ids}
        self.entities: Dict[str, Any] = {}
        self.current_fw_versions: Dict[str, str] = {dongle_id: "" for dongle_id in self._dongle_ids}
        self.current_ui_versions: Dict[str, str] = {dongle_id: "" for dongle_id in self._dongle_ids}
        self._mqtt_unsubscribe_callbacks: Dict[str, Any] = {}
        self._ignored_entity_suffixes: Set[str] = set()  # To track entities we've already logged about
        self._pending_dongles: List[str] = self._dongle_ids.copy()  # Track dongles still needing setup
        self.server_versions = {}

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

    def get_firmware_code(self, dongle_id: str) -> str:
        """Get firmware code for a specific dongle."""
        return self._firmware_codes.get(dongle_id)

    @callback
    async def _async_handle_mqtt_message(self, msg) -> None:
        """Handle all MQTT messages."""
        topic = msg.topic
        
        # Extract dongle ID from the topic
        try:
            dongle_id = topic.split('/')[0]
            #LOGGER.debug(f"Received MQTT message on topic {topic} from dongle {dongle_id}")
            
            if topic.endswith("/firmwarecode/response"):
                await self._handle_firmware_code_response(dongle_id, msg)
            elif topic.endswith("/response"):
                await self.mqtt_handler.response_received(msg)
            elif topic.endswith("/status"):
                await self.process_status_message(dongle_id, msg.payload)
            else:
                await self.process_message(dongle_id, topic, msg.payload)
                
            self.async_set_updated_data(self.entities)
        except Exception as e:
            LOGGER.error(f"Error processing MQTT message on topic {topic}: {e}")
            # Still try to update data even if we encounter an error
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

        # Set up entities dictionary for each dongle
        for dongle_id in self._dongle_ids:
            formatted_dongle_id = self.get_formatted_dongle_id(dongle_id)
            for entityTypeName, entityTypes in brand_entities.items():
                for typeName, entities in entityTypes.items():
                    for entity in entities:
                        entity_id: str = f"{entityTypeName}.{formatted_dongle_id}_{entity['unique_id'].lower()}"
                        self.entities[entity_id] = None

        # Request firmware codes for all dongles
        await self.request_firmware_codes()
        
        # Set up update listener
        self.entry.async_on_unload(self.entry.add_update_listener(self.config_entry_update_listener))
        
        return True

    async def request_firmware_codes(self):
        """Request firmware codes for all dongles."""
        LOGGER.debug(f"Requesting firmware codes for {len(self._dongle_ids)} dongles")
        
        # Request firmware codes for all dongles
        for dongle_id in self._dongle_ids:
            if not self._firmware_codes.get(dongle_id):
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

        # Log all active subscriptions to verify
        LOGGER.debug(f"Active MQTT subscriptions: {list(self._mqtt_unsubscribe_callbacks.keys())}")

        # Set up timeout to handle case where firmware codes are not received
        async def firmware_timeout(_):
            if self._pending_dongles:
                LOGGER.error(f"Firmware code responses not received for dongles: {self._pending_dongles}")
                # Log active subscriptions for diagnostic purposes
                LOGGER.debug(f"Current active MQTT subscriptions: {list(self._mqtt_unsubscribe_callbacks.keys())}")
                # We don't reauth here anymore, as we'll still try to set up what we can
                
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

        # Update UI version
        if "UI_VERSION" in payload_data:
            ui_version = payload_data["UI_VERSION"]
            self.current_ui_versions[dongle_id] = ui_version
            #LOGGER.debug(f"Current UI version set for {dongle_id}: {ui_version}")
            # Set entity value
            entity_id = f"update.{formatted_dongle_id}_ui_update"
            self.entities[entity_id] = ui_version

        # Process fault data
        if fault_data:
            LOGGER.debug(f"Processing fault data for {dongle_id}: {fault_data}")
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
            LOGGER.debug(f"Processing warning data for {dongle_id}: {warning_data}")
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