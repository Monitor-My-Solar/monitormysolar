# Common Issues

This page covers the most frequently encountered issues and their solutions.

## Installation Issues

### Integration Not Found After Installation

**Symptoms:**
- Can't find "Monitor My Solar" when adding integration
- Integration missing from list

**Solutions:**
1. **Restart Home Assistant** - Required after HACS installation
2. **Clear browser cache** - Ctrl+F5 or Cmd+Shift+R
3. **Check installation location**:
   ```
   /config/custom_components/monitormysolar/
   ├── __init__.py
   ├── manifest.json
   └── (other files)
   ```
4. **Check logs** for import errors:
   ```
   Logger: homeassistant.loader
   Error importing custom_components.monitormysolar
   ```

### HACS Download Fails

**Symptoms:**
- Download button doesn't work
- Error during download

**Solutions:**
1. Update HACS to latest version
2. Check GitHub API rate limits
3. Try manual installation method
4. Verify internet connectivity

## Configuration Issues

### No Entities Created

**Symptoms:**
- Integration added successfully but no entities appear
- Devices show 0 entities

**Solutions:**

1. **Check firmware code response**:
   - Enable debug logging
   - Look for: `Firmware code received for dongle-XX: XXXX`
   - If missing, dongle not responding

2. **Verify dongle ID format**:
   - Must be lowercase: `dongle-12:34:56:78:90:ab`
   - Not `Dongle-12:34:56:78:90:AB` ❌

3. **Check MQTT connection**:
   - Dongle web interface should show "Connected"
   - Verify MQTT broker is running
   - Check username/password

4. **Wait for timeout**:
   - Integration waits 20 seconds for firmware code
   - Check logs after this period

### Entities Show "Unavailable"

**Symptoms:**
- All entities exist but show "Unavailable"
- No data updates

**Solutions:**

1. **Verify MQTT messages**:
   - Install MQTT Explorer
   - Connect to broker
   - Look for topics: `dongle-XX:XX:XX:XX:XX:XX/#`

2. **Check network connectivity**:
   - Ping dongle IP
   - Access dongle web interface
   - Verify no firewall blocking

3. **Restart sequence**:
   - Restart dongle (power cycle)
   - Restart MQTT broker
   - Reload integration

### Wrong Firmware Code / Missing Entities

**Symptoms:**
- Some expected entities missing
- Wrong inverter features shown

**Solutions:**

1. **Update dongle firmware**:
   - Minimum version 3.0.0 required
   - Check for updates in dongle web interface

2. **Verify inverter model**:
   - Check physical inverter model
   - Compare with firmware code received
   - Contact support if mismatch

## Upgrade Issues

### AttributeError: 'current_ui_versions'

**Symptoms after upgrading to v3.0.0:**
```
AttributeError: 'MonitorMySolar' object has no attribute 'current_ui_versions'
```

**Solutions:**

1. **Restart Home Assistant completely** (not just reload)
2. If persists:
   - Remove integration
   - Restart Home Assistant
   - Re-add integration with same settings

### Duplicate Devices After Upgrade

**Symptoms:**
- New devices created instead of updating existing
- Old entities become unavailable

**Solutions:**

1. **Remove old devices**:
   - Settings → Devices & Services → Devices
   - Delete devices with "unavailable" entities
   - Keep new devices with working entities

2. **Update dashboards and automations** to use new entity IDs

## MQTT Issues

### Dongle Won't Connect to MQTT

**Symptoms:**
- Dongle shows "Disconnected" or "Connecting"
- No MQTT messages received

**Solutions:**

1. **Check MQTT URL format**:
   - Correct: `mqtt://192.168.1.100:1883`
   - Wrong: `192.168.1.100:1883` ❌
   - Wrong: `http://192.168.1.100:1883` ❌

2. **Verify credentials**:
   - Username and password are case-sensitive
   - No special characters that need escaping
   - Test with MQTT Explorer first

3. **Check MQTT broker settings**:
   - Allow anonymous: false
   - Listener on port 1883
   - No IP restrictions

4. **Network issues**:
   - Dongle and HA on same network
   - No VLAN isolation
   - Router not blocking traffic

### MQTT Messages But No Updates

**Symptoms:**
- MQTT Explorer shows messages
- Entities still unavailable

**Solutions:**

1. **Check topic format**:
   - Should be: `dongle-XX:XX:XX:XX:XX:XX/topic`
   - Lowercase dongle ID required

2. **Verify message format**:
   - Should be valid JSON
   - Check for corruption

3. **Integration subscription**:
   - Reload integration
   - Check logs for subscription errors

## Multi-Inverter Issues

### Second Dongle Not Responding

**Symptoms:**
- First dongle works, additional dongles don't
- Timeout adding new dongle

**Solutions:**

1. **Check unique dongle IDs**:
   - Each dongle must have unique ID
   - No duplicate IDs allowed

2. **Test individually**:
   - Remove multi-inverter setup
   - Test each dongle separately
   - Then recombine

3. **MQTT conflicts**:
   - Ensure different client IDs
   - Check for topic collisions

### Sync Settings Not Working

**Symptoms:**
- Settings don't propagate between inverters
- Sync status shows errors

**Solutions:**

1. **Enable sync switch**: `switch.combined_sync_settings`
2. **Check firmware versions** - All must match
3. **Verify all inverters online**
4. **Manual sync**: Use combined entities to force update

## Performance Issues

### Database Growing Too Fast

**Symptoms:**
- Database size increasing rapidly
- System slowdowns

**Solutions:**

1. **Adjust update interval**:
   - Configure → Update Settings
   - Choose longer interval (5 min, 10 min)

2. **Exclude from recorder**:
   ```yaml
   recorder:
     exclude:
       entities:
         - sensor.dongle_*_ezpv_today
         - sensor.dongle_*_ezpv2_today
   ```

3. **Use filters**:
   ```yaml
   recorder:
     include:
       entities:
         - sensor.dongle_*_ppv
         - sensor.dongle_*_soc
   ```

### UI Updates Lag

**Symptoms:**
- Dashboard updates slowly
- Delays in state changes

**Solutions:**

1. **Reduce dashboard complexity**:
   - Use fewer real-time cards
   - Implement update intervals

2. **Check network latency**:
   - Ping dongle
   - Monitor MQTT broker load

## GridBoss Issues

### GridBoss Entities Not Appearing

**Symptoms:**
- GridBoss enabled but no entities
- Only standard entities visible

**Solutions:**

1. **Verify firmware code**: Must be `IAAB`
2. **Enable in configuration**:
   - Configure → Update Settings
   - Check "GridBoss Connected"
3. **Restart Home Assistant** after enabling
4. **Check MQTT topics**: Should see `gridboss_*` topics

### Load Control Not Working

**Symptoms:**
- Load switches don't control loads
- No power readings from loads

**Solutions:**

1. **Check physical wiring**:
   - Loads connected to GridBoss outputs
   - Proper CT placement

2. **Verify load enabled**:
   - Both software switch and physical connection

3. **Check power limits**:
   - May be set to 0
   - Increase limit values

## General Troubleshooting Steps

### 1. Enable Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.monitormysolar: debug
```

### 2. Check Integration Status

1. Settings → Devices & Services
2. Find Monitor My Solar
3. Click "Configure" → "Check Status"
4. Review connection status and errors

### 3. Collect Diagnostic Info

When reporting issues, include:
- Home Assistant version
- Integration version
- Dongle firmware version
- Debug logs
- MQTT Explorer screenshots
- Error messages

### 4. Test Connectivity

```bash
# Test dongle reachability
ping dongle-ip-address

# Test MQTT broker
mosquitto_sub -h broker-ip -u username -P password -t "#" -v
```

## Getting Further Help

If issues persist:

1. Search [existing issues](https://github.com/Monitor-My-Solar/monitormysolar/issues)
2. Create new issue with:
   - Clear problem description
   - Steps to reproduce
   - Diagnostic information
   - What you've already tried
3. Join [Home Assistant Community](https://community.home-assistant.io/)
4. Contact [Monitor My Solar support](https://monitormy.solar/support)