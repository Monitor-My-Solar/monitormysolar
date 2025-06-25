from homeassistant.core import HomeAssistant
import asyncio
from homeassistant.components import mqtt
from .const import LOGGER, PLATFORMS
from .coordinator import MonitorMySolar, MonitorMySolarEntry

async def async_setup_entry(hass: HomeAssistant, entry: MonitorMySolarEntry):
    """Set up Monitor My Solar from a config entry."""
    inverter_brand = entry.data.get('inverter_brand')
    dongle_ids = entry.data.get('dongle_ids', [entry.data.get('dongle_id')])
    
    LOGGER.info(f"Setting up Monitor My Solar for {inverter_brand} with {len(dongle_ids)} dongles")

    # Step 1: Initialize the coordinator with minimal setup
    coordinator = MonitorMySolar(hass, entry)
    entry.runtime_data = coordinator
    
    # Step 2: Request firmware codes for all dongles and wait for them
    # Initialize the coordinator but don't wait for data refresh
    try:
        await coordinator.async_setup()
    except Exception as e:
        error_msg = f"Error during coordinator setup: {e}"
        LOGGER.error(error_msg)
        coordinator._setup_errors.append(error_msg)
    
    # Wait for all firmware codes to be received (or timeout)
    LOGGER.debug("Waiting for firmware codes to be received for all dongles...")
    try:
        # Wait up to 20 seconds for firmware codes
        for attempt in range(20):
            if not coordinator._pending_dongles:
                LOGGER.debug("All firmware codes received successfully")
                break
            
            # If we're halfway through the timeout and still have pending dongles, try requesting again
            if attempt == 10 and coordinator._pending_dongles:
                error_msg = f"Still waiting for firmware codes from: {coordinator._pending_dongles}, sending request again"
                LOGGER.debug(error_msg)
                # Try requesting firmware codes again for the pending dongles
                for dongle_id in coordinator._pending_dongles:
                    try:
                        await mqtt.async_publish(
                            hass, f"{dongle_id}/firmwarecode/request", ""
                        )
                        LOGGER.debug(f"Resent firmware code request to {dongle_id}/firmwarecode/request")
                    except Exception as e:
                        error_msg = f"Error sending firmware request to {dongle_id}: {e}"
                        LOGGER.error(error_msg)
                        coordinator._setup_errors.append(error_msg)
            
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # Handle if the setup is cancelled
        error_msg = "Setup was cancelled while waiting for firmware codes"
        LOGGER.warning(error_msg)
        coordinator._setup_errors.append(error_msg)
        return False
    
    # Log status of firmware code reception
    if coordinator._pending_dongles:
        error_msg = f"Missing firmware codes from: {coordinator._pending_dongles}"
        LOGGER.warning(f"Proceeding with setup despite {error_msg}")
        coordinator._setup_errors.append(error_msg)
    else:
        LOGGER.debug("Successfully received firmware codes from all dongles")
    
    # Step 3: Now that we have tried to get firmware codes, set up the platforms
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception as e:
        LOGGER.error(f"Error setting up platforms: {e}")
        return False
    
    # Step 4: Mark setup as complete
    LOGGER.info(f"Monitor My Solar setup completed successfully for {len(dongle_ids)} dongles")
    
    # Step 5: Start listening to all MQTT topics for all dongles
    # Only do this once to avoid duplicate subscriptions
    await coordinator.start_mqtt_subscription()
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: MonitorMySolarEntry) -> bool:
    """Unload a config entry."""
    LOGGER.info(f"Unloading Monitor My Solar integration for {entry.data.get('inverter_brand')}")
    
    # Get the coordinator instance
    coordinator = entry.runtime_data
    
    if coordinator:
        # First stop MQTT subscription to prevent new data coming in
        await coordinator.stop_mqtt_subscription()
        
        # Use the correct unload method
        try:
            # Unload all platforms
            unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
            return unload_ok
        except Exception as e:
            LOGGER.error(f"Error unloading entry: {e}")
            return False
    
    return True
