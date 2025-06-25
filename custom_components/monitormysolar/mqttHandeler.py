import asyncio
from datetime import datetime
import json
from homeassistant.core import HomeAssistant
from homeassistant.components.mqtt import async_publish
from homeassistant.components import mqtt

from .const import DOMAIN, LOGGER

class MQTTHandler:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.last_time_update = None
        self.response_received_event = asyncio.Event()
        self._processing = False  # To track if a command is currently being processed
        self._lock = asyncio.Lock()  # A lock to ensure only one command is processed at a time
        self.current_entity = None  # Store the current entity
        self._unsubscribe_response = None
        self._pending_dongles = set()  # Track which dongles we're waiting for responses from
        self._dongle_responses = {}  # Store responses from each dongle

    async def send_update(self, dongle_id, unique_id, value, entity):
        now = datetime.now()
        LOGGER.info(f"Sending update for {entity.entity_id} with value {value}")

        # Rate limiting logic: only allow one update per 1 second per entity
        if self.last_time_update and (now - self.last_time_update).total_seconds() < 1:
            LOGGER.info(f"Rate limit hit for {entity.entity_id}. Dropping update.")
            return

        async with self._lock:  # Ensure only one command is processed at a time
            if self._processing:
                LOGGER.info(f"Already processing an update for {entity.entity_id}.")
                return

            self._processing = True
            self.last_time_update = now
            self.current_entity = entity  # Store the entity to be used later in the response handling

            try:
                success = await self._process_command(dongle_id, unique_id, value, entity)
                return success
            finally:
                # Clear variables after processing the command
                self._processing = False
                self.response_received_event.clear()
                self.current_entity = None  # Clear entity after processing

    async def _process_command(self, dongle_id, unique_id, value, entity):
        modified_dongle_id = dongle_id.replace("_", "-").split("-")
        modified_dongle_id[1] = modified_dongle_id[1].upper()
        modified_dongle_id = "-".join(modified_dongle_id)

        topic = f"{modified_dongle_id}/update"
        
        # Updated payload with setting, value, and from: homeassistant
        payload = json.dumps({
            "setting": unique_id, 
            "value": value, 
            "from": "homeassistant"
        })
        
        LOGGER.info(f"Sending MQTT update: {topic} - {payload} at {datetime.now()}")
        await mqtt.async_publish(self.hass, topic, payload)

        self.response_received_event.clear()  # Reset the event before sending the update

        # Clean up any existing subscription
        if self._unsubscribe_response:
            self._unsubscribe_response()
            self._unsubscribe_response = None

        response_topic = f"{modified_dongle_id}/response"
        # Create a single subscription and store the unsubscribe function
        self._unsubscribe_response = await mqtt.async_subscribe(
            self.hass, 
            response_topic, 
            self.response_received
        )

        try:
            await asyncio.wait_for(self.response_received_event.wait(), timeout=15)
            LOGGER.debug(f"Response received or timeout for {entity.entity_id} at {datetime.now()}")
            return True
        except asyncio.TimeoutError:
            LOGGER.error(f"No response received for {entity.entity_id} within the timeout period.")
            self.hass.loop.call_soon_threadsafe(entity.revert_state)
            return False
        finally:
            # Unsubscribe from the response topic
            if self._unsubscribe_response:
                self._unsubscribe_response()
                self._unsubscribe_response = None

    async def send_update_to_multiple_dongles(self, dongle_ids, unique_id, value, entity):
        """Send the same update to multiple dongles and wait for all responses."""
        now = datetime.now()
        LOGGER.info(f"Sending update to multiple dongles for {entity.entity_id} with value {value}")
        
        # Rate limiting logic
        if self.last_time_update and (now - self.last_time_update).total_seconds() < 1:
            LOGGER.info(f"Rate limit hit for {entity.entity_id}. Dropping update.")
            return False
            
        async with self._lock:
            if self._processing:
                LOGGER.info(f"Already processing an update for {entity.entity_id}.")
                return False
                
            self._processing = True
            self.last_time_update = now
            self.current_entity = entity
            
            try:
                # Store original dongle IDs for response matching
                self._pending_dongles = set(dongle_ids)
                self._dongle_responses = {}
                success = True
                
                LOGGER.info(f"Expecting responses from {len(dongle_ids)} dongles: {dongle_ids}")
                
                # Set up subscriptions for all dongles first
                unsubscribe_functions = []
                for dongle_id in dongle_ids:
                    modified_dongle_id = dongle_id.replace("_", "-").split("-")
                    modified_dongle_id[1] = modified_dongle_id[1].upper()
                    modified_dongle_id = "-".join(modified_dongle_id)
                    
                    response_topic = f"{modified_dongle_id}/response"
                    unsubscribe = await mqtt.async_subscribe(
                        self.hass,
                        response_topic,
                        self.response_received_multi_dongle
                    )
                    unsubscribe_functions.append(unsubscribe)
                
                # Now send updates to all dongles
                for dongle_id in dongle_ids:
                    modified_dongle_id = dongle_id.replace("_", "-").split("-")
                    modified_dongle_id[1] = modified_dongle_id[1].upper()
                    modified_dongle_id = "-".join(modified_dongle_id)
                    
                    topic = f"{modified_dongle_id}/update"
                    payload = json.dumps({
                        "setting": unique_id,
                        "value": value,
                        "from": "homeassistant"
                    })
                    
                    LOGGER.info(f"Sending MQTT update to dongle {dongle_id}: {topic} - {payload}")
                    await mqtt.async_publish(self.hass, topic, payload)
                
                # Wait for all responses or timeout
                try:
                    # We'll wait for all dongles to respond or for a timeout
                    await asyncio.wait_for(self._wait_for_all_responses(), timeout=15)
                    LOGGER.info(f"Received responses from all dongles for {entity.entity_id}")
                    
                    # Check if any dongle reported failure
                    for dongle_id, status in self._dongle_responses.items():
                        if status != 'success':
                            LOGGER.error(f"Dongle {dongle_id} reported failure for {entity.entity_id}")
                            success = False
                    
                except asyncio.TimeoutError:
                    LOGGER.error(f"Timeout waiting for responses from dongles: {self._pending_dongles}")
                    success = False
                
                # If any dongle failed, revert state
                if not success:
                    self.hass.loop.call_soon_threadsafe(entity.revert_state)
                
                return success
            finally:
                # Clean up
                for unsubscribe in unsubscribe_functions:
                    unsubscribe()
                self._processing = False
                self._pending_dongles = set()
                self._dongle_responses = {}
                self.current_entity = None
    
    async def _wait_for_all_responses(self):
        """Wait until all pending dongles have responded."""
        while self._pending_dongles:
            # Create event that will be set when a dongle response is received
            event = asyncio.Event()
            
            # Store the event to be triggered when a response arrives
            self._response_event = event
            
            # Wait for a response
            await event.wait()
            
            # Reset the event for the next iteration
            self._response_event = None
    
    async def response_received_multi_dongle(self, msg):
        """Handle response from a dongle in a multi-dongle update scenario."""
        entity = self.current_entity
        if not entity:
            return
            
        LOGGER.info(f"Received multi-dongle response for topic {msg.topic}: {msg.payload}")
        
        # Extract dongle ID from the topic
        # Topic format is "{modified_dongle_id}/response"
        topic_parts = msg.topic.split('/')
        if len(topic_parts) < 2:
            return
        
        modified_dongle_id = topic_parts[0]
        
        # The modified_dongle_id from topic is like "dongle-12:34:56:78:90:12"
        # We need to match this against the original dongle IDs in _pending_dongles
        # which should also be in the format "dongle-12:34:56:78:90:12"
        
        # For response matching, we use the modified_dongle_id as-is
        dongle_id_for_matching = modified_dongle_id
        
        # Log the conversion for debugging
        LOGGER.debug(f"Response received from dongle: {dongle_id_for_matching}")
        
        try:
            response = json.loads(msg.payload)
            status = response.get('status')
            
            # Remove dongle from pending set
            if dongle_id_for_matching in self._pending_dongles:
                self._pending_dongles.remove(dongle_id_for_matching)
                # Store response with the original dongle ID
                self._dongle_responses[dongle_id_for_matching] = status
                LOGGER.info(f"Received response from {dongle_id_for_matching} (status: {status}). Still waiting for: {self._pending_dongles}")
            else:
                LOGGER.warning(f"Received unexpected response from {dongle_id_for_matching} - was not in pending list: {self._pending_dongles}")
                
            # If this was the last pending dongle, signal success
            if not self._pending_dongles and self._response_event:
                LOGGER.info(f"All dongles have responded. Responses: {self._dongle_responses}")
                self._response_event.set()
                
        except json.JSONDecodeError:
            LOGGER.error(f"Failed to decode JSON response for dongle {dongle_id_for_matching}: {msg.payload}")
            
            # Handle error case
            if dongle_id_for_matching in self._pending_dongles:
                self._pending_dongles.remove(dongle_id_for_matching)
                # Count this as a response, but with failure
                self._dongle_responses[dongle_id_for_matching] = 'error'
                LOGGER.info(f"Marked {dongle_id_for_matching} as error. Still waiting for: {self._pending_dongles}")
                
            if not self._pending_dongles and self._response_event:
                LOGGER.info(f"All dongles have responded (with errors). Responses: {self._dongle_responses}")
                self._response_event.set()

    async def response_received(self, msg):
        """Handle the response received message."""
        entity = self.current_entity
        if not entity:
            return

        LOGGER.info(f"Received response for topic {msg.topic} at {datetime.now()}: {msg.payload}")
        try:
            response = json.loads(msg.payload)
            
            if response.get('status') == 'success':
                LOGGER.info(f"Successfully updated state of entity {entity.entity_id}.")
                # Keep the current state as it was already optimistically updated
                self.hass.loop.call_soon_threadsafe(entity.async_write_ha_state)
            else:
                LOGGER.error(f"Failed to update state for {entity.entity_id}, reverting state.")
                self.hass.loop.call_soon_threadsafe(entity.revert_state)
        except json.JSONDecodeError:
            LOGGER.error(f"Failed to decode JSON response for {entity.entity_id}: {msg.payload}")
            self.hass.loop.call_soon_threadsafe(entity.revert_state)
        finally:
            # Unsubscribe and clear the event
            if self._unsubscribe_response:
                self._unsubscribe_response()
                self._unsubscribe_response = None
            self.response_received_event.set()

    async def send_multiple_updates(self, dongle_id, payload_dict, entity):
        """Handle multiple settings updates."""
        now = datetime.now()
        LOGGER.info(f"Sending multiple updates for {entity.entity_id} with payload {payload_dict}")

        if self.last_time_update and (now - self.last_time_update).total_seconds() < 1:
            LOGGER.info(f"Rate limit hit for {entity.entity_id}. Dropping update.")
            return

        async with self._lock:
            if self._processing:
                LOGGER.info(f"Already processing an update for {entity.entity_id}.")
                return

            self._processing = True
            self.last_time_update = now
            self.current_entity = entity

            try:
                success = await self._process_multiple_commands(dongle_id, payload_dict, entity)
                return success
            finally:
                self._processing = False
                self.response_received_event.clear()
                self.current_entity = None

    async def _process_multiple_commands(self, dongle_id, payload_dict, entity):
        """Process multiple commands in a single payload."""
        modified_dongle_id = dongle_id.replace("_", "-").split("-")
        modified_dongle_id[1] = modified_dongle_id[1].upper()
        modified_dongle_id = "-".join(modified_dongle_id)

        topic = f"{modified_dongle_id}/update"
        
        # Create payload with multiple settings
        settings = []
        for setting, value in payload_dict.items():
            settings.append({
                "setting": setting,
                "value": value
            })
        
        payload = json.dumps({
            "settings": settings,
            "from": "homeassistant"
        })
        
        LOGGER.info(f"Sending multiple MQTT updates: {topic} - {payload} at {datetime.now()}")
        await mqtt.async_publish(self.hass, topic, payload)

        self.response_received_event.clear()

        response_topic = f"{modified_dongle_id}/response"
        await mqtt.async_subscribe(self.hass, response_topic, self.response_received)

        try:
            await asyncio.wait_for(self.response_received_event.wait(), timeout=15)
            LOGGER.debug(f"Response received or timeout for {entity.entity_id} at {datetime.now()}")
            return True
        except asyncio.TimeoutError:
            LOGGER.error(f"No response received for {entity.entity_id} within the timeout period.")
            self.hass.loop.call_soon_threadsafe(entity.revert_state)
            return False