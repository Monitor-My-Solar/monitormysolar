import logging
import json
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.components import mqtt
from homeassistant.helpers import config_validation as cv
import asyncio
from .const import DOMAIN, CONF_ENABLE_DEVICE_GROUPING, DEFAULT_ENABLE_DEVICE_GROUPING, CONF_USE_INPUT_BOX, DEFAULT_USE_INPUT_BOX, CONF_DROP_DONGLE_ID, CONF_USE_BETA, DEFAULT_USE_BETA

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
            "Growatt": "Growatt",
            "Deye": "Deye / SunSynk / SolArk / NeoVolta"
        }
        
        brand_name = brand_names.get(brand, brand)
        
        # Use singular/plural based on dongle count
        if dongle_count == 1:
            return f"{brand_name} Inverter"
        else:
            return f"{brand_name} Inverters"

    async def async_step_user(self, user_input=None):
        """Handle the initial user step - brand selection and basic setup."""
        errors = {}

        _LOGGER.debug("Loading the user step form")

        if user_input is not None:
            _LOGGER.debug("User input received: %s", user_input)
            
            # Store initial data
            self.initial_data = user_input
            
            # Move to setup type selection step
            return await self.async_step_setup_type()

        _LOGGER.debug("Displaying the form with translations")

        # Create schema with brand selection as dropdown and update interval
        schema = vol.Schema(
            {
                vol.Required("inverter_brand", default="Solis"): vol.In(
                    ["Solis", "Lux", "Solax", "Growatt", "Deye"]
                ),
                vol.Optional("update_interval", default=60): vol.In(
                    {1: "1 second", 3: "3 seconds", 5: "5 seconds", 10: "10 seconds", 
                     30: "30 seconds", 60: "1 minute", 300: "5 minutes", 600: "10 minutes"}
                ),
            }
        )

        # Show the form with the schema
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_single_inverter(self, user_input=None):
        """Handle the single inverter setup step."""
        errors = {}

        _LOGGER.debug("Loading the single inverter step form")

        if user_input is not None:
            _LOGGER.debug("Single inverter input received: %s", user_input)
            
            # Normalize the dongle ID
            user_input["dongle_id"] = self._normalize_dongle_id(user_input["dongle_id"])

            # Determine entity naming scheme from install kind.
            # fresh    -> drop the dongle id from entity_ids (clean new scheme)
            # reconnect-> keep the dongle id so new entities adopt the OLD entity_ids
            #             and existing history/statistics line up automatically. The
            #             user can drop the dongle id later via the options flow, which
            #             performs a proper history-preserving registry rename.
            install_kind = user_input.pop("install_kind", "fresh")
            user_input[CONF_DROP_DONGLE_ID] = install_kind == "fresh"

            # Merge with initial data
            data = {**self.initial_data, **user_input}

            # Create dongle data structure for single inverter.
            # Single-dongle installs get NO entity_id prefix (clean names like
            # sensor.battery_soc) — we never ask. entity_prefix stays empty.
            dongle_data = [{
                "dongle_id": data["dongle_id"],
                "entity_prefix": "",
                "is_master": True,
                "is_slave": False,
                "is_gridboss": False,
                "is_gridboss_slave": False,
                "gridboss_bundle": None
            }]

            # Update data with dongle structure
            data.update({
                "dongle_data": dongle_data,
                "dongle_ids": [data["dongle_id"]],
            })
            
            # Create the entry
            return self.async_create_entry(
                title=f"{data['inverter_brand']} - {data['dongle_id']}",
                data=data,
            )

        _LOGGER.debug("Displaying the single inverter form")

        # Create schema for single inverter setup.
        # install_kind is REQUIRED: it decides whether existing Monitor My Solar
        # history should be preserved (reconnect) or a clean naming scheme used (fresh).
        schema = vol.Schema(
            {
                vol.Required("dongle_id"): str,
                vol.Required("install_kind", default="fresh"): vol.In({
                    "fresh": "Fresh install (no previous Monitor My Solar history)",
                    "reconnect": "Reconnecting an existing system (preserve my history)",
                }),
            }
        )

        # Show the form with the schema
        return self.async_show_form(
            step_id="single_inverter", 
            data_schema=schema, 
            errors=errors,
            description_placeholders={"brand": self.initial_data.get("inverter_brand", "Inverter")}
        )

    async def async_step_setup_type(self, user_input=None):
        """Handle the setup type selection step."""
        errors = {}

        _LOGGER.debug("Loading the setup type step form")

        if user_input is not None:
            _LOGGER.debug("Setup type input received: %s", user_input)
            
            # Merge with initial data
            data = {**self.initial_data, **user_input}
            self.initial_data = data
            
            # Determine next step based on selection
            setup_type = user_input.get("setup_type")
            if setup_type == "single":
                return await self.async_step_single_inverter()
            elif setup_type == "parallel":
                return await self.async_step_parallel()
            elif setup_type == "single_gridboss":
                return await self.async_step_single_gridboss()
            elif setup_type == "dual_gridboss":
                return await self.async_step_dual_gridboss()

        _LOGGER.debug("Displaying the setup type form")

        # Create schema for setup type selection
        schema = vol.Schema(
            {
                vol.Required("setup_type"): vol.In({
                    "single": "Single Inverter (Standard Setup)",
                    "parallel": "Parallel Inverters",
                    "single_gridboss": "Single GridBoss Setup",
                    "dual_gridboss": "Dual GridBoss Setup"
                }),
            }
        )

        # Show the form with the schema
        return self.async_show_form(
            step_id="setup_type", 
            data_schema=schema, 
            errors=errors,
            description_placeholders={"brand": self.initial_data.get("inverter_brand", "Inverter")}
        )

    async def async_step_parallel(self, user_input=None):
        """Handle the parallel inverters step."""
        errors = {}

        if user_input is not None:
            # Process the master dongle (from user input)
            master_dongle = user_input.get("master_dongle_id")

            if not master_dongle or not master_dongle.strip():
                errors["master_dongle_id"] = "Master dongle ID is required"
            else:
                # Normalize the master dongle ID
                master_dongle = self._normalize_dongle_id(master_dongle)
            
            if not errors:
                # Process slave dongles
                slave_dongles = []

                for i in range(1, 6):  # Up to 5 slaves
                    slave_dongle = user_input.get(f"slave_dongle_id_{i}")
                    if slave_dongle and slave_dongle.strip():
                        # Normalize the slave dongle ID
                        normalized_dongle = self._normalize_dongle_id(slave_dongle)
                        # Pair each slave's prefix with its dongle; fall back to the
                        # normalized dongle_id if left blank (avoids collisions).
                        slave_prefix = (
                            user_input.get(f"slave_prefix_{i}", "").strip()
                            or normalized_dongle
                        )
                        slave_dongles.append((normalized_dongle, slave_prefix))

                # Create dongle data with master/slave tracking
                dongle_data = []

                # Add master dongle
                dongle_data.append({
                    "dongle_id": master_dongle,
                    "entity_prefix": user_input.get("master_prefix", "").strip() or master_dongle,
                    "is_master": True,
                    "is_slave": False,
                    "is_gridboss": False,
                    "is_gridboss_slave": False,
                    "gridboss_bundle": None
                })

                # Add slave dongles
                for slave_dongle, slave_prefix in slave_dongles:
                    dongle_data.append({
                        "dongle_id": slave_dongle,
                        "entity_prefix": slave_prefix,
                        "is_master": False,
                        "is_slave": True,
                        "is_gridboss": False,
                        "is_gridboss_slave": False,
                        "gridboss_bundle": None
                    })

                # Update initial data
                self.initial_data.update({
                    "dongle_data": dongle_data,
                    "dongle_ids": [d["dongle_id"] for d in dongle_data],
                })
                
                # Create the entry
                return self.async_create_entry(
                    title=f"{self.initial_data['inverter_brand']} - Parallel Setup ({len(dongle_data)} inverters)",
                    data=self.initial_data,
                )

        # Create schema for master dongle and slave dongles
        schema = vol.Schema(
            {
                vol.Required("master_dongle_id"): str,
                vol.Optional("master_prefix"): str,
                vol.Optional("slave_dongle_id_1"): str,
                vol.Optional("slave_prefix_1"): str,
                vol.Optional("slave_dongle_id_2"): str,
                vol.Optional("slave_prefix_2"): str,
                vol.Optional("slave_dongle_id_3"): str,
                vol.Optional("slave_prefix_3"): str,
                vol.Optional("slave_dongle_id_4"): str,
                vol.Optional("slave_prefix_4"): str,
                vol.Optional("slave_dongle_id_5"): str,
                vol.Optional("slave_prefix_5"): str,
            }
        )

        return self.async_show_form(
            step_id="parallel",
            data_schema=schema, 
            errors=errors,
            description_placeholders={
                "brand": self.initial_data.get("inverter_brand", "Inverter")
            }
        )

    async def async_step_single_gridboss(self, user_input=None):
        """Handle the single GridBoss setup step."""
        errors = {}

        if user_input is not None:
            # Process the GridBoss dongle (from user input)
            gridboss_dongle = user_input.get("gridboss_dongle_id")

            if not gridboss_dongle or not gridboss_dongle.strip():
                errors["gridboss_dongle_id"] = "GridBoss dongle ID is required"
            else:
                # Normalize the GridBoss dongle ID
                gridboss_dongle = self._normalize_dongle_id(gridboss_dongle)
            
            if not errors:
                # Process slave dongles
                slave_dongles = []

                for i in range(1, 4):  # Up to 3 slaves for single GridBoss
                    slave_dongle = user_input.get(f"slave_dongle_id_{i}")
                    if slave_dongle and slave_dongle.strip():
                        # Normalize the slave dongle ID
                        normalized_dongle = self._normalize_dongle_id(slave_dongle)
                        # Pair each slave's prefix with its dongle; fall back to the
                        # normalized dongle_id if left blank (avoids collisions).
                        slave_prefix = (
                            user_input.get(f"slave_prefix_{i}", "").strip()
                            or normalized_dongle
                        )
                        slave_dongles.append((normalized_dongle, slave_prefix))

                # Create dongle data with GridBoss tracking
                dongle_data = []

                # Add GridBoss dongle
                dongle_data.append({
                    "dongle_id": gridboss_dongle,
                    "entity_prefix": user_input.get("gridboss_prefix", "").strip() or gridboss_dongle,
                    "is_master": False,
                    "is_slave": False,
                    "is_gridboss": True,
                    "is_gridboss_slave": False,
                    "gridboss_bundle": 1
                })

                # Add slave dongles
                for slave_dongle, slave_prefix in slave_dongles:
                    dongle_data.append({
                        "dongle_id": slave_dongle,
                        "entity_prefix": slave_prefix,
                        "is_master": False,
                        "is_slave": False,
                        "is_gridboss": False,
                        "is_gridboss_slave": True,
                        "gridboss_bundle": 1
                    })

                # Update initial data
                self.initial_data.update({
                    "dongle_data": dongle_data,
                    "dongle_ids": [d["dongle_id"] for d in dongle_data],
                    "has_gridboss": True,
                    "gridboss_dongle": gridboss_dongle
                })
                
                # Create the entry
                return self.async_create_entry(
                    title=f"{self.initial_data['inverter_brand']} - Single GridBoss Setup ({len(dongle_data)} inverters)",
                    data=self.initial_data,
                )

        # Create schema for GridBoss dongle and slave dongles
        schema = vol.Schema(
            {
                vol.Required("gridboss_dongle_id"): str,
                vol.Optional("gridboss_prefix"): str,
                vol.Optional("slave_dongle_id_1"): str,
                vol.Optional("slave_prefix_1"): str,
                vol.Optional("slave_dongle_id_2"): str,
                vol.Optional("slave_prefix_2"): str,
                vol.Optional("slave_dongle_id_3"): str,
                vol.Optional("slave_prefix_3"): str,
            }
        )

        return self.async_show_form(
            step_id="single_gridboss",
            data_schema=schema, 
            errors=errors,
            description_placeholders={
                "brand": self.initial_data.get("inverter_brand", "Inverter")
            }
        )

    async def async_step_dual_gridboss(self, user_input=None):
        """Handle the dual GridBoss setup step."""
        errors = {}

        if user_input is not None:
            # Process the first GridBoss dongle (from user input)
            gridboss1_dongle = user_input.get("gridboss1_dongle_id")

            if not gridboss1_dongle or not gridboss1_dongle.strip():
                errors["gridboss1_dongle_id"] = "First GridBoss dongle ID is required"
            else:
                # Normalize the first GridBoss dongle ID
                gridboss1_dongle = self._normalize_dongle_id(gridboss1_dongle)
            
            # Process the second GridBoss dongle
            gridboss2_dongle = user_input.get("gridboss2_dongle_id")

            if not gridboss2_dongle or not gridboss2_dongle.strip():
                errors["gridboss2_dongle_id"] = "Second GridBoss dongle ID is required"
            else:
                # Normalize the second GridBoss dongle ID
                gridboss2_dongle = self._normalize_dongle_id(gridboss2_dongle)
            
            if not errors:
                # Process slave dongles for GridBoss 1
                gridboss1_slaves = []

                for i in range(1, 4):  # Up to 3 slaves for GridBoss 1
                    slave_dongle = user_input.get(f"gridboss1_slave_dongle_id_{i}")
                    if slave_dongle and slave_dongle.strip():
                        normalized_dongle = self._normalize_dongle_id(slave_dongle)
                        slave_prefix = (
                            user_input.get(f"gridboss1_slave_prefix_{i}", "").strip()
                            or normalized_dongle
                        )
                        gridboss1_slaves.append((normalized_dongle, slave_prefix))

                # Process slave dongles for GridBoss 2
                gridboss2_slaves = []

                for i in range(1, 4):  # Up to 3 slaves for GridBoss 2
                    slave_dongle = user_input.get(f"gridboss2_slave_dongle_id_{i}")
                    if slave_dongle and slave_dongle.strip():
                        normalized_dongle = self._normalize_dongle_id(slave_dongle)
                        slave_prefix = (
                            user_input.get(f"gridboss2_slave_prefix_{i}", "").strip()
                            or normalized_dongle
                        )
                        gridboss2_slaves.append((normalized_dongle, slave_prefix))

                # Create dongle data with dual GridBoss tracking
                dongle_data = []

                # Add GridBoss 1
                dongle_data.append({
                    "dongle_id": gridboss1_dongle,
                    "entity_prefix": user_input.get("gridboss1_prefix", "").strip() or gridboss1_dongle,
                    "is_master": False,
                    "is_slave": False,
                    "is_gridboss": True,
                    "is_gridboss_slave": False,
                    "gridboss_bundle": 1
                })

                # Add GridBoss 1 slaves
                for slave_dongle, slave_prefix in gridboss1_slaves:
                    dongle_data.append({
                        "dongle_id": slave_dongle,
                        "entity_prefix": slave_prefix,
                        "is_master": False,
                        "is_slave": False,
                        "is_gridboss": False,
                        "is_gridboss_slave": True,
                        "gridboss_bundle": 1
                    })

                # Add GridBoss 2
                dongle_data.append({
                    "dongle_id": gridboss2_dongle,
                    "entity_prefix": user_input.get("gridboss2_prefix", "").strip() or gridboss2_dongle,
                    "is_master": False,
                    "is_slave": False,
                    "is_gridboss": True,
                    "is_gridboss_slave": False,
                    "gridboss_bundle": 2
                })

                # Add GridBoss 2 slaves
                for slave_dongle, slave_prefix in gridboss2_slaves:
                    dongle_data.append({
                        "dongle_id": slave_dongle,
                        "entity_prefix": slave_prefix,
                        "is_master": False,
                        "is_slave": False,
                        "is_gridboss": False,
                        "is_gridboss_slave": True,
                        "gridboss_bundle": 2
                    })

                # Update initial data
                self.initial_data.update({
                    "dongle_data": dongle_data,
                    "dongle_ids": [d["dongle_id"] for d in dongle_data],
                    "has_gridboss": True,
                    "gridboss_dongle": gridboss1_dongle  # Keep for backward compatibility
                })
                
                # Create the entry
                return self.async_create_entry(
                    title=f"{self.initial_data['inverter_brand']} - Dual GridBoss Setup ({len(dongle_data)} inverters)",
                    data=self.initial_data,
                )

        # Create schema for dual GridBoss setup - ordered logically
        schema = vol.Schema(
            {
                # GridBoss 1 and its slaves
                vol.Required("gridboss1_dongle_id"): str,
                vol.Optional("gridboss1_prefix"): str,
                vol.Optional("gridboss1_slave_dongle_id_1"): str,
                vol.Optional("gridboss1_slave_prefix_1"): str,
                vol.Optional("gridboss1_slave_dongle_id_2"): str,
                vol.Optional("gridboss1_slave_prefix_2"): str,
                vol.Optional("gridboss1_slave_dongle_id_3"): str,
                vol.Optional("gridboss1_slave_prefix_3"): str,
                # GridBoss 2 and its slaves
                vol.Required("gridboss2_dongle_id"): str,
                vol.Optional("gridboss2_prefix"): str,
                vol.Optional("gridboss2_slave_dongle_id_1"): str,
                vol.Optional("gridboss2_slave_prefix_1"): str,
                vol.Optional("gridboss2_slave_dongle_id_2"): str,
                vol.Optional("gridboss2_slave_prefix_2"): str,
                vol.Optional("gridboss2_slave_dongle_id_3"): str,
                vol.Optional("gridboss2_slave_prefix_3"): str,
            }
        )

        return self.async_show_form(
            step_id="dual_gridboss", 
            data_schema=schema, 
            errors=errors,
            description_placeholders={
                "brand": self.initial_data.get("inverter_brand", "Inverter")
            }
        )

    async def async_step_gridboss(self, user_input=None):
        """Handle the GridBoss configuration step."""
        errors = {}

        if user_input is not None:
            # Get the GridBoss dongle selection
            gridboss_dongle = user_input.get("gridboss_dongle", "")
            
            # Update initial data with GridBoss info
            self.initial_data["gridboss_dongle"] = gridboss_dongle
            
            # Create the entry with all the data
            return self.async_create_entry(
                title=f"{self.initial_data['inverter_brand']} - GridBoss Configuration",
                data=self.initial_data,
            )

        # Create schema for GridBoss dongle selection
        # Build the options based on available dongles
        dongle_options = {"": "None"}
        
        # Add first dongle
        dongle_options["dongle_id"] = f"First Dongle ({self.initial_data['dongle_id']})"
        
        # Add additional dongles if they exist
        dongle_ids = self.initial_data.get("dongle_ids", [])
        for i in range(1, len(dongle_ids)):
            dongle_options[f"dongle_id_{i+1}"] = f"Dongle {i+1} ({dongle_ids[i]})"

        schema = vol.Schema(
            {
                vol.Required("gridboss_dongle"): vol.In(dongle_options),
            }
        )

        return self.async_show_form(step_id="gridboss", data_schema=schema, errors=errors)

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
            "Growatt": "Growatt",
            "Deye": "Deye / SunSynk / SolArk / NeoVolta"
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
            menu_options=["manage_dongles", "update_settings", "restore_entities", "check_status"]
        )

    async def async_step_restore_entities(self, user_input=None):
        """Restore entities that a reload won't bring back (deleted or disabled).

        When a user deletes an entity from the UI, HA remembers the unique_id as
        deleted and refuses to recreate it on setup — reboots don't help. This
        step lists those (plus disabled ones), lets the user pick which to bring
        back, clears the blocking registry records, and reloads so the platforms
        recreate them fresh from the catalog.
        """
        from .migration import list_restorable_entities, async_restore_entities

        restorable = list_restorable_entities(self.hass, self.config_entry)

        if not restorable:
            return self.async_abort(reason="no_restorable_entities")

        if user_input is not None:
            selected = user_input.get("entities", [])
            if selected:
                await async_restore_entities(self.hass, self.config_entry, selected)
                # Reload so platform setup recreates any purged-deleted entities.
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        # Label each choice with its state so the user knows what they're getting.
        options = {
            item["key"]: f"{item['name']} ({item['state']}) — {item['entity_id']}"
            for item in restorable
        }

        schema = vol.Schema({
            vol.Optional("entities", default=list(options.keys())): cv.multi_select(options)
        })

        return self.async_show_form(
            step_id="restore_entities",
            data_schema=schema,
            description_placeholders={"count": str(len(restorable))},
        )
    
    async def async_step_manage_dongles(self, user_input=None):
        """Manage dongles - add, remove, or update."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add":
                return await self.async_step_add_dongle()
            elif action == "remove":
                return await self.async_step_remove_dongle()
            elif action == "replace":
                return await self.async_step_replace_dongle()

        schema = vol.Schema({
            vol.Required("action"): vol.In({
                "add": "Add new dongle",
                "remove": "Remove existing dongle",
                "replace": "Replace a dongle (transfer history to new dongle)",
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

            # Get current data
            new_data = dict(self.config_entry.data)
            dongle_ids = list(new_data.get("dongle_ids", []))

            # Check if dongle already exists
            if new_dongle_id in dongle_ids:
                errors["dongle_id"] = "dongle_already_exists"
            else:
                # Add new dongle
                dongle_ids.append(new_dongle_id)

                # Update data
                new_data["dongle_ids"] = dongle_ids

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
            vol.Required("dongle_id"): str
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

            # Find and remove dongle
            if dongle_to_remove in dongle_ids:
                index = dongle_ids.index(dongle_to_remove)
                dongle_ids.pop(index)

                # Update data
                new_data["dongle_ids"] = dongle_ids

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
    
    async def async_step_replace_dongle(self, user_input=None):
        """Replace a dongle, transferring all its entities and history to the new one."""
        from .migration import async_transfer_dongle_entities

        errors = {}
        current_dongles = self.config_entry.data.get("dongle_ids", [])

        if user_input is not None:
            old_dongle_id = user_input["old_dongle_id"]
            new_dongle_id = self._normalize_dongle_id(user_input["new_dongle_id"])

            if not new_dongle_id:
                errors["new_dongle_id"] = "dongle_id_required"
            elif new_dongle_id in current_dongles:
                errors["new_dongle_id"] = "dongle_already_exists"
            elif old_dongle_id not in current_dongles:
                errors["old_dongle_id"] = "dongle_not_found"
            else:
                # Transfer entities + history from the old dongle to the new one
                # (rewrites unique_ids via the entity registry, in place).
                transferred = await async_transfer_dongle_entities(
                    self.hass, self.config_entry, old_dongle_id, new_dongle_id
                )
                _LOGGER.info(
                    "Replaced dongle %s with %s, transferred %d entities",
                    old_dongle_id, new_dongle_id, transferred,
                )

                # Swap the old dongle for the new one in the config entry, preserving
                # its position and master/slave/gridboss role.
                new_data = dict(self.config_entry.data)
                dongle_ids = list(new_data.get("dongle_ids", []))
                dongle_data = [dict(d) for d in new_data.get("dongle_data", [])]

                idx = dongle_ids.index(old_dongle_id)
                dongle_ids[idx] = new_dongle_id
                for d in dongle_data:
                    if d.get("dongle_id") == old_dongle_id:
                        d["dongle_id"] = new_dongle_id

                new_data["dongle_ids"] = dongle_ids
                new_data["dongle_data"] = dongle_data
                # Keep gridboss_dongle pointer in sync if it referenced the old dongle.
                if new_data.get("gridboss_dongle") == old_dongle_id:
                    new_data["gridboss_dongle"] = new_dongle_id

                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})

        schema = vol.Schema({
            vol.Required("old_dongle_id"): vol.In(current_dongles),
            vol.Required("new_dongle_id"): str,
        })

        return self.async_show_form(
            step_id="replace_dongle",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "current_dongles": ", ".join(current_dongles)
            },
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

            # Update device grouping if provided
            if CONF_ENABLE_DEVICE_GROUPING in user_input:
                new_data[CONF_ENABLE_DEVICE_GROUPING] = user_input[CONF_ENABLE_DEVICE_GROUPING]

            # Update number input mode if provided
            if CONF_USE_INPUT_BOX in user_input:
                new_data[CONF_USE_INPUT_BOX] = user_input[CONF_USE_INPUT_BOX]

            # Update entity naming scheme if provided (single-dongle installs only).
            # Changing this triggers a history-preserving entity-registry rename on
            # reload (see migration.async_migrate_entity_ids).
            if CONF_DROP_DONGLE_ID in user_input:
                new_data[CONF_DROP_DONGLE_ID] = user_input[CONF_DROP_DONGLE_ID]

            # Update firmware track (prod/beta) if provided.
            if CONF_USE_BETA in user_input:
                new_data[CONF_USE_BETA] = user_input[CONF_USE_BETA]

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )

            # Reload the integration so device grouping / naming changes take effect
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        current_update_interval = self.config_entry.data.get("update_interval", 60)
        current_has_gridboss = self.config_entry.data.get("has_gridboss", False)
        current_device_grouping = self.config_entry.data.get(
            CONF_ENABLE_DEVICE_GROUPING, DEFAULT_ENABLE_DEVICE_GROUPING
        )
        current_use_input_box = self.config_entry.data.get(
            CONF_USE_INPUT_BOX, DEFAULT_USE_INPUT_BOX
        )
        current_drop_dongle_id = self.config_entry.data.get(CONF_DROP_DONGLE_ID, False)
        current_use_beta = self.config_entry.data.get(CONF_USE_BETA, DEFAULT_USE_BETA)

        # Dropping the dongle id is only meaningful for single-dongle installs;
        # multi-dongle needs the dongle id to disambiguate entity_ids.
        is_single_dongle = len(self.config_entry.data.get("dongle_ids", [])) == 1

        schema_dict = {
            vol.Optional("update_interval", default=current_update_interval): vol.In(
                {1: "1 second", 3: "3 seconds", 5: "5 seconds", 10: "10 seconds",
                 30: "30 seconds", 60: "1 minute", 300: "5 minutes", 600: "10 minutes"}
            ),
            vol.Optional("has_gridboss", default=current_has_gridboss): bool,
            vol.Optional(CONF_ENABLE_DEVICE_GROUPING, default=current_device_grouping): bool,
            vol.Optional(CONF_USE_INPUT_BOX, default=current_use_input_box): bool,
            vol.Optional(CONF_USE_BETA, default=current_use_beta): bool,
        }
        if is_single_dongle:
            schema_dict[
                vol.Optional(CONF_DROP_DONGLE_ID, default=current_drop_dongle_id)
            ] = bool

        schema = vol.Schema(schema_dict)

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
