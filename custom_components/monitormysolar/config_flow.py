import logging
import json
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.components import mqtt
import asyncio
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class InverterMQTTFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Inverter MQTT."""

    VERSION = 1
    
    def _normalize_dongle_id(self, dongle_id):
        """Normalize dongle ID to format: dongle-XX:XX:XX:XX:XX:XX."""
        if not dongle_id:
            return ""
        
        # Remove any whitespace
        dongle_id = dongle_id.strip()
        
        # Extract MAC address part (everything after 'dongle-' or the whole string if no prefix)
        if dongle_id.lower().startswith("dongle-"):
            mac_part = dongle_id[7:]  # Remove 'dongle-' prefix
        else:
            mac_part = dongle_id
        
        # Normalize MAC address: remove non-alphanumeric chars and ensure uppercase
        mac_part = ''.join(c for c in mac_part if c.isalnum()).upper()
        
        # Insert colons if not present (assuming 12 character MAC)
        if len(mac_part) == 12 and ':' not in mac_part:
            mac_part = ':'.join(mac_part[i:i+2] for i in range(0, 12, 2))
        
        # Return normalized format
        return f"dongle-{mac_part}"
    
    def _get_inverter_title(self, brand, dongle_count=1):
        """Generate a proper title based on brand and number of dongles."""
        # Map brand codes to proper names
        brand_names = {
            "Lux": "LuxPower",
            "Solis": "Solis",
            "Solax": "Solax",
            "Growatt": "Growatt"
        }
        
        brand_name = brand_names.get(brand, brand)
        
        # Use singular/plural based on dongle count
        if dongle_count == 1:
            return f"{brand_name} Inverter"
        else:
            return f"{brand_name} Inverters"

    async def async_step_user(self, user_input=None):
        errors = {}

        _LOGGER.debug("Loading the user step form")

        if user_input is not None:
            _LOGGER.debug("User input received: %s", user_input)
            
            # Normalize the dongle ID
            user_input["dongle_id"] = self._normalize_dongle_id(user_input["dongle_id"])
            
            # If parallel inverters is selected, store the data and move to the parallel step
            if user_input.get("parallel_inverters", False):
                self.initial_data = user_input
                return await self.async_step_parallel()
            
            # If no parallel inverters, create a single dongle entry
            user_input["dongle_ids"] = [user_input["dongle_id"]]
            user_input["dongle_ips"] = [user_input.get("dongle_ip", "")]
            
            # Once the user submits the form, create the entry
            return self.async_create_entry(
                title=f"{user_input['inverter_brand']} - {user_input['dongle_id']}",
                data=user_input,
            )

        _LOGGER.debug("Displaying the form with translations")

        # Create base schema with core fields
        schema = vol.Schema(
            {
                vol.Required("inverter_brand", default="Solis"): vol.In(
                    ["Solis", "Lux", "Solax", "Growatt"]
                ),
                vol.Required("dongle_id"): str,
                vol.Optional("dongle_ip"): str,
                vol.Optional("parallel_inverters", default=False): bool,
                vol.Optional("update_interval", default=60): vol.In(
                    {1: "1 second", 3: "3 seconds", 5: "5 seconds", 10: "10 seconds", 
                     30: "30 seconds", 60: "1 minute", 300: "5 minutes", 600: "10 minutes"}
                ),
                vol.Optional("has_gridboss", default=False): bool,
            }
        )

        # Show the form with the schema
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_parallel(self, user_input=None):
        """Handle the parallel inverters step."""
        errors = {}

        if user_input is not None:
            # Process the dongle IDs and IPs
            dongle_ids = [self.initial_data["dongle_id"]]
            dongle_ips = [self.initial_data.get("dongle_ip", "")]
            
            # Add additional dongle IDs and IPs
            for i in range(1, 4):  # Check for dongle_id_2, dongle_id_3, dongle_id_4
                additional_dongle = user_input.get(f"dongle_id_{i+1}")
                if additional_dongle and additional_dongle.strip():
                    # Normalize the additional dongle ID
                    normalized_dongle = self._normalize_dongle_id(additional_dongle)
                    dongle_ids.append(normalized_dongle)
                    # Get corresponding IP or empty string
                    additional_ip = user_input.get(f"dongle_ip_{i+1}", "")
                    dongle_ips.append(additional_ip)
            
            # Combine all data
            combined_data = {**self.initial_data, **user_input, "dongle_ids": dongle_ids, "dongle_ips": dongle_ips}
            
            # Create the entry with all the data
            return self.async_create_entry(
                title=f"{self.initial_data['inverter_brand']} - Multiple Dongles",
                data=combined_data,
            )

        # Create schema for additional dongles
        schema = vol.Schema(
            {
                vol.Optional("dongle_id_2"): str,
                vol.Optional("dongle_ip_2"): str,
                vol.Optional("dongle_id_3"): str,
                vol.Optional("dongle_ip_3"): str,
                vol.Optional("dongle_id_4"): str,
                vol.Optional("dongle_ip_4"): str,
            }
        )

        return self.async_show_form(step_id="parallel", data_schema=schema, errors=errors)

    async def async_setup_entry(self, hass, entry):
        _LOGGER.info("Monitor My Solar Being Setup")
        return True
    
    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return InverterMQTTOptionsFlowHandler(config_entry)


class InverterMQTTOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Monitor My Solar."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry
        self.installation_errors = []
    
    @property
    def config_entry(self):
        """Return the config entry."""
        return self._config_entry
    
    def _normalize_dongle_id(self, dongle_id):
        """Normalize dongle ID to format: dongle-XX:XX:XX:XX:XX:XX."""
        if not dongle_id:
            return ""
        
        # Remove any whitespace
        dongle_id = dongle_id.strip()
        
        # Extract MAC address part (everything after 'dongle-' or the whole string if no prefix)
        if dongle_id.lower().startswith("dongle-"):
            mac_part = dongle_id[7:]  # Remove 'dongle-' prefix
        else:
            mac_part = dongle_id
        
        # Normalize MAC address: remove non-alphanumeric chars and ensure uppercase
        mac_part = ''.join(c for c in mac_part if c.isalnum()).upper()
        
        # Insert colons if not present (assuming 12 character MAC)
        if len(mac_part) == 12 and ':' not in mac_part:
            mac_part = ':'.join(mac_part[i:i+2] for i in range(0, 12, 2))
        
        # Return normalized format
        return f"dongle-{mac_part}"
    
    def _get_inverter_title(self, brand, dongle_count=1):
        """Generate a proper title based on brand and number of dongles."""
        # Map brand codes to proper names
        brand_names = {
            "Lux": "LuxPower",
            "Solis": "Solis",
            "Solax": "Solax",
            "Growatt": "Growatt"
        }
        
        brand_name = brand_names.get(brand, brand)
        
        # Use singular/plural based on dongle count
        if dongle_count == 1:
            return f"{brand_name} Inverter"
        else:
            return f"{brand_name} Inverters"

    async def async_step_init(self, user_input=None):
        """Manage the options - main menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["manage_dongles", "update_settings", "check_status"]
        )
    
    async def async_step_manage_dongles(self, user_input=None):
        """Manage dongles - add, remove, or update."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add":
                return await self.async_step_add_dongle()
            elif action == "remove":
                return await self.async_step_remove_dongle()
            elif action == "update":
                return await self.async_step_update_dongles()
        
        schema = vol.Schema({
            vol.Required("action"): vol.In({
                "add": "Add new dongle",
                "remove": "Remove existing dongle",
                "update": "Update dongle IPs"
            })
        })
        
        return self.async_show_form(
            step_id="manage_dongles",
            data_schema=schema,
            description_placeholders={
                "current_dongles": ", ".join(self.config_entry.data.get("dongle_ids", []))
            }
        )
    
    async def async_step_add_dongle(self, user_input=None):
        """Add a new dongle."""
        errors = {}
        
        if user_input is not None:
            # Normalize the new dongle ID
            new_dongle_id = self._normalize_dongle_id(user_input["dongle_id"])
            new_dongle_ip = user_input.get("dongle_ip", "")
            
            # Get current data
            new_data = dict(self.config_entry.data)
            dongle_ids = list(new_data.get("dongle_ids", []))
            dongle_ips = list(new_data.get("dongle_ips", []))
            
            # Check if dongle already exists
            if new_dongle_id in dongle_ids:
                errors["dongle_id"] = "dongle_already_exists"
            else:
                # Add new dongle
                dongle_ids.append(new_dongle_id)
                dongle_ips.append(new_dongle_ip)
                
                # Update data
                new_data["dongle_ids"] = dongle_ids
                new_data["dongle_ips"] = dongle_ips
                
                # Test connection to new dongle
                if await self._test_dongle_connection(new_dongle_id):
                    # Update entry with new data
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, 
                        data=new_data
                    )
                    
                    # Reload the integration
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                    
                    return self.async_create_entry(title="", data={})
                else:
                    errors["base"] = "dongle_not_responding"
        
        schema = vol.Schema({
            vol.Required("dongle_id"): str,
            vol.Optional("dongle_ip"): str
        })
        
        return self.async_show_form(
            step_id="add_dongle",
            data_schema=schema,
            errors=errors
        )
    
    async def async_step_remove_dongle(self, user_input=None):
        """Remove a dongle."""
        current_dongles = self.config_entry.data.get("dongle_ids", [])
        
        if len(current_dongles) <= 1:
            return self.async_abort(reason="cannot_remove_last_dongle")
        
        if user_input is not None:
            dongle_to_remove = user_input["dongle_id"]
            
            # Get current data
            new_data = dict(self.config_entry.data)
            dongle_ids = list(new_data.get("dongle_ids", []))
            dongle_ips = list(new_data.get("dongle_ips", []))
            
            # Find and remove dongle
            if dongle_to_remove in dongle_ids:
                index = dongle_ids.index(dongle_to_remove)
                dongle_ids.pop(index)
                if index < len(dongle_ips):
                    dongle_ips.pop(index)
                
                # Update data
                new_data["dongle_ids"] = dongle_ids
                new_data["dongle_ips"] = dongle_ips
                
                # Update entry with new data
                self.hass.config_entries.async_update_entry(
                    self.config_entry, 
                    data=new_data
                )
                
                # Reload the integration
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                
                return self.async_create_entry(title="", data={})
        
        schema = vol.Schema({
            vol.Required("dongle_id"): vol.In(current_dongles)
        })
        
        return self.async_show_form(
            step_id="remove_dongle",
            data_schema=schema
        )
    
    async def async_step_update_dongles(self, user_input=None):
        """Update dongle IPs."""
        if user_input is not None:
            # Update the config entry with new data
            new_data = dict(self.config_entry.data)
            
            # Update dongle IPs if provided
            if "dongle_ips" in self.config_entry.data:
                dongle_ips = []
                for i, dongle_id in enumerate(self.config_entry.data["dongle_ids"]):
                    ip_key = f"dongle_ip_{i+1}" if i > 0 else "dongle_ip"
                    dongle_ips.append(user_input.get(ip_key, ""))
                new_data["dongle_ips"] = dongle_ips
            
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            return self.async_create_entry(title="", data={})

        # Build schema based on current configuration
        dongle_ids = self.config_entry.data.get("dongle_ids", [])
        dongle_ips = self.config_entry.data.get("dongle_ips", [""] * len(dongle_ids))
        
        schema_dict = {}
        for i, dongle_id in enumerate(dongle_ids):
            current_ip = dongle_ips[i] if i < len(dongle_ips) else ""
            if i == 0:
                schema_dict[vol.Optional("dongle_ip", default=current_ip)] = str
            else:
                schema_dict[vol.Optional(f"dongle_ip_{i+1}", default=current_ip)] = str
        
        return self.async_show_form(
            step_id="update_dongles",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "dongle_ids": ", ".join(dongle_ids)
            }
        )
    
    async def async_step_update_settings(self, user_input=None):
        """Update general settings."""
        if user_input is not None:
            new_data = dict(self.config_entry.data)
            
            # Update update_interval if provided
            if "update_interval" in user_input:
                new_data["update_interval"] = user_input["update_interval"]
            
            # Update has_gridboss if provided
            if "has_gridboss" in user_input:
                new_data["has_gridboss"] = user_input["has_gridboss"]
            
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            return self.async_create_entry(title="", data={})
        
        current_update_interval = self.config_entry.data.get("update_interval", 60)
        
        current_has_gridboss = self.config_entry.data.get("has_gridboss", False)
        
        schema = vol.Schema({
            vol.Optional("update_interval", default=current_update_interval): vol.In(
                {1: "1 second", 3: "3 seconds", 5: "5 seconds", 10: "10 seconds", 
                 30: "30 seconds", 60: "1 minute", 300: "5 minutes", 600: "10 minutes"}
            ),
            vol.Optional("has_gridboss", default=current_has_gridboss): bool
        })
        
        return self.async_show_form(
            step_id="update_settings",
            data_schema=schema
        )
    
    async def async_step_check_status(self, user_input=None):
        """Check installation status and dongle connectivity."""
        # Get coordinator
        coordinator = self.config_entry.runtime_data
        
        # Collect status information
        status_info = await self._collect_status_info(coordinator)
        
        return self.async_show_form(
            step_id="check_status",
            data_schema=vol.Schema({}),
            description_placeholders=status_info
        )
    
    async def _test_dongle_connection(self, dongle_id):
        """Test if a dongle is responding."""
        try:
            # Subscribe to the dongle's firmware code response topic
            response_received = asyncio.Event()
            firmware_code = None
            
            async def check_response(msg):
                nonlocal firmware_code
                try:
                    _LOGGER.debug(f"Received MQTT message on topic {msg.topic}: {msg.payload}")
                    data = json.loads(msg.payload)
                    firmware_code = data.get("FWCode")
                    if firmware_code:
                        _LOGGER.debug(f"Received firmware code {firmware_code} for dongle {dongle_id}")
                except Exception as e:
                    _LOGGER.error(f"Error parsing firmware response: {e}")
                response_received.set()
            
            # Subscribe to firmware code response FIRST
            topic = f"{dongle_id}/firmwarecode/response"
            _LOGGER.debug(f"Subscribing to topic: {topic}")
            unsubscribe = await mqtt.async_subscribe(
                self.hass, 
                topic, 
                check_response
            )
            
            # Give subscription time to establish
            await asyncio.sleep(0.1)
            
            # Now request firmware code
            request_topic = f"{dongle_id}/firmwarecode/request"
            _LOGGER.debug(f"Publishing firmware code request to: {request_topic}")
            await mqtt.async_publish(
                self.hass, 
                request_topic, 
                ""
            )
            
            # Wait for response (10 seconds timeout to match coordinator)
            try:
                await asyncio.wait_for(response_received.wait(), timeout=10)
                result = firmware_code is not None
                if result:
                    _LOGGER.info(f"Dongle {dongle_id} responded with firmware code: {firmware_code}")
                else:
                    _LOGGER.warning(f"Dongle {dongle_id} responded but no firmware code found")
            except asyncio.TimeoutError:
                _LOGGER.warning(f"Dongle {dongle_id} did not respond within 10 seconds")
                result = False
            
            # Unsubscribe
            unsubscribe()
            
            return result
            
        except Exception as e:
            _LOGGER.error(f"Error testing dongle connection: {e}")
            return False
    
    async def _collect_status_info(self, coordinator):
        """Collect status information about the installation."""
        info = {}
        
        if coordinator:
            # Get dongle statuses
            dongle_statuses = []
            for dongle_id in self.config_entry.data.get("dongle_ids", []):
                firmware_code = coordinator.get_firmware_code(dongle_id) or "Unknown"
                fw_version = coordinator.current_fw_versions.get(dongle_id, "Unknown")
                
                # Test connectivity
                is_connected = await self._test_dongle_connection(dongle_id)
                status = "✅ Connected" if is_connected else "❌ Not responding"
                
                dongle_statuses.append(
                    f"{dongle_id}: {status}\n"
                    f"  Firmware: {firmware_code} v{fw_version}"
                )
            
            info["dongle_statuses"] = "\n\n".join(dongle_statuses)
            info["total_entities"] = str(len(coordinator.entities))
            
            # Check for any errors during setup
            if hasattr(coordinator, '_setup_errors'):
                info["setup_errors"] = "\n".join(coordinator._setup_errors) or "None"
            else:
                info["setup_errors"] = "None"
        else:
            info["dongle_statuses"] = "Coordinator not initialized"
            info["total_entities"] = "0"
            info["setup_errors"] = "Unable to check"
        
        return info
