# Initial Setup

This guide covers the initial configuration of your Monitor My Solar integration.

## Before You Begin

Ensure you have:
- ✅ Installed the integration via HACS or manually
- ✅ Configured your MQTT broker
- ✅ Your dongle connected to your network
- ✅ Access to your dongle's web interface

## Step 1: Configure Your Dongle

### Access Dongle Web Interface

1. Find your dongle's IP address (check your router's DHCP list)
2. Open a web browser and navigate to: `http://[DONGLE-IP]`
3. Default credentials (if any) are usually printed on the dongle

### Enable MQTT Connection

1. Navigate to **Settings** or **MQTT Configuration**
2. Enable **"Local MQTT Server"**
3. Configure these settings:

| Setting | Value |
|---------|-------|
| MQTT Server | `mqtt://[HOME-ASSISTANT-IP]:1883` |
| Username | Your MQTT username |
| Password | Your MQTT password |
| Client ID | Leave default or use dongle ID |
| Topic Prefix | Leave as dongle ID |

4. Click **Save**
5. Wait for status to show **"Connected"**

⚠️ **Important**: The dongle ID must be lowercase (e.g., `dongle-12:34:56:78:90:ab`)

## Step 2: Add Integration to Home Assistant

### Configuration Wizard

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Monitor My Solar"**
4. Fill in the configuration form:

### Configuration Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Inverter Brand** | Select your inverter manufacturer | LuxPower |
| **Dongle ID** | From dongle web interface (lowercase!) | dongle-12:34:56:78:90:ab |
| **Dongle IP** | IP address for firmware updates | 192.168.1.150 |
| **Parallel Inverters** | Check if you have multiple inverters | ☐ |
| **Update Interval** | How often to write to database | 1 minute |
| **GridBoss Connected** | Check if using GridBoss (IAAB only) | ☐ |

### Single Inverter Setup

For a single inverter:
1. Enter your dongle ID
2. Optionally enter dongle IP (for firmware updates)
3. Leave "Parallel Inverters" unchecked
4. Click **Submit**

### Multiple Inverters Setup

For parallel inverters:
1. Check "Parallel Inverters"
2. Click **Submit**
3. On the next screen, enter additional dongle IDs
4. Click **Submit**

## Step 3: Verify Setup

### Check Entity Creation

After successful setup:
1. Go to **Settings** → **Devices & Services**
2. Click on your Monitor My Solar integration
3. You should see:
   - 1 device per dongle
   - Multiple entities per device (sensors, switches, etc.)

### Verify MQTT Communication

1. Go to **Developer Tools** → **States**
2. Filter by your dongle ID
3. Entities should show real-time values
4. If entities show "Unknown" or "Unavailable", check:
   - MQTT broker connection
   - Dongle MQTT settings
   - Network connectivity

## Step 4: Configure Dashboard

### Quick Dashboard Setup

1. Go to your dashboard
2. Click **Edit Dashboard** (three dots menu)
3. Click **"+ Add Card"**
4. Choose **"Entities"** card
5. Add key entities:

```yaml
type: entities
title: Solar Inverter
entities:
  - sensor.dongle_XX_XX_XX_XX_XX_XX_ppv
  - sensor.dongle_XX_XX_XX_XX_XX_XX_vbat
  - sensor.dongle_XX_XX_XX_XX_XX_XX_soc
  - sensor.dongle_XX_XX_XX_XX_XX_XX_pinv
  - sensor.dongle_XX_XX_XX_XX_XX_XX_pload
```

### Energy Dashboard Integration

1. Go to **Settings** → **Dashboards** → **Energy**
2. Configure:
   - **Grid Consumption**: `sensor.dongle_XX_pgrid` (positive values)
   - **Return to Grid**: `sensor.dongle_XX_pgrid` (negative values)
   - **Solar Production**: `sensor.dongle_XX_ppv`
   - **Battery**: `sensor.dongle_XX_pbat`

## Common Setup Issues

### No Entities Created

**Symptoms**: Integration added but no entities appear

**Solutions**:
1. Check MQTT broker logs for connection from dongle
2. Verify dongle ID is lowercase
3. Check firmware code is being received (logs)
4. Restart Home Assistant

### Entities Show "Unavailable"

**Symptoms**: Entities exist but show no data

**Solutions**:
1. Verify MQTT messages arriving:
   - Install MQTT Explorer
   - Connect to your broker
   - Check for topics: `dongle-XX:XX:XX:XX:XX:XX/#`
2. Check dongle web interface shows "Connected"
3. Verify network connectivity

### Wrong Firmware Code

**Symptoms**: Missing expected entities

**Solutions**:
1. Check logs for firmware code received
2. Verify dongle firmware version (v3.0.0+)
3. Contact support if firmware code unexpected

## Next Steps

- [Supported Entities](Supported-Entities) - Understand available entities
- [Multi-Inverter Setup](Multi-Inverter-Setup) - Add more inverters
- [GridBoss Configuration](GridBoss-Configuration) - Enable GridBoss features
- [Energy Dashboard](Energy-Dashboard) - Set up energy monitoring

## Getting Help

If you encounter issues:
1. Check [Common Issues](Common-Issues)
2. Enable [Debug Logging](Debug-Logging)
3. Search [GitHub Issues](https://github.com/Monitor-My-Solar/monitormysolar/issues)
4. Create a new issue with:
   - Home Assistant version
   - Integration version
   - Dongle firmware version
   - Debug logs