import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class InverterMQTTFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Inverter MQTT."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        _LOGGER.debug("Loading the user step form")

        if user_input is not None:
            _LOGGER.debug("User input received: %s", user_input)
            
            # If parallel inverters is selected, store the data and move to the parallel step
            if user_input.get("parallel_inverters", False):
                self.initial_data = user_input
                return await self.async_step_parallel()
            
            # If no parallel inverters, create a single dongle entry
            user_input["dongle_ids"] = [user_input["dongle_id"]]
            
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
                vol.Optional("parallel_inverters", default=False): bool,
            }
        )

        # Show the form with the schema
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_parallel(self, user_input=None):
        """Handle the parallel inverters step."""
        errors = {}

        if user_input is not None:
            # Process the dongle IDs
            dongle_ids = [self.initial_data["dongle_id"]]
            
            # Add additional dongle IDs
            for i in range(1, 4):  # Check for dongle_id_2, dongle_id_3, dongle_id_4
                additional_dongle = user_input.get(f"dongle_id_{i+1}")
                if additional_dongle and additional_dongle.strip():
                    dongle_ids.append(additional_dongle)
            
            # Combine all data
            combined_data = {**self.initial_data, **user_input, "dongle_ids": dongle_ids}
            
            # Create the entry with all the data
            return self.async_create_entry(
                title=f"{self.initial_data['inverter_brand']} - Multiple Dongles",
                data=combined_data,
            )

        # Create schema for additional dongles
        schema = vol.Schema(
            {
                vol.Optional("dongle_id_2"): str,
                vol.Optional("dongle_id_3"): str,
                vol.Optional("dongle_id_4"): str,
            }
        )

        return self.async_show_form(step_id="parallel", data_schema=schema, errors=errors)

    async def async_setup_entry(self, hass, entry):
        _LOGGER.info("Monitor My Solar Being Setup")
        return True
