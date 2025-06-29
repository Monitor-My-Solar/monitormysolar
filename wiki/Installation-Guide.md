# Installation Guide

This guide walks you through installing the Monitor My Solar integration in Home Assistant.

## Prerequisites

Before starting, ensure you have:

1. ✅ **Monitor My Solar Dongle** (v3.0.0+ firmware)
2. ✅ **Home Assistant** (2024.1.0 or newer)
3. ✅ **MQTT Broker** (Mosquitto recommended)
4. ✅ **HACS** (Home Assistant Community Store)

## Step 1: Install MQTT Broker

If you don't have an MQTT broker installed:

1. Go to **Settings** → **Add-ons** → **Add-on Store**
2. Search for "Mosquitto broker"
3. Click **Install**
4. Start the add-on
5. Go to **Configuration** tab and add a user:
```yaml
logins:
  - username: mqtt_user
    password: your_secure_password
```

## Step 2: Configure MQTT Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "MQTT"
4. Enter your broker details:
   - Broker: `localhost` (if using Mosquitto add-on)
   - Port: `1883`
   - Username & Password (from Step 1)

## Step 3: Install via HACS

### Option A: HACS Default Repository
1. Open HACS
2. Click **Integrations**
3. Click **+ Explore & Download Repositories**
4. Search for "Monitor My Solar"
5. Click **Download**
6. Select the latest version
7. Click **Download**
8. Restart Home Assistant

### Option B: Manual HACS Installation
1. Open HACS
2. Click **Integrations**
3. Click the 3 dots menu → **Custom repositories**
4. Add repository:
   - URL: `https://github.com/Monitor-My-Solar/monitormysolar`
   - Category: `Integration`
5. Click **Add**
6. Search for "Monitor My Solar" and install

## Step 4: Manual Installation (Alternative)

If not using HACS:

1. Download the latest release from [GitHub](https://github.com/Monitor-My-Solar/monitormysolar/releases)
2. Extract the `monitormysolar` folder
3. Copy to `custom_components` directory:
```bash
# Navigate to your Home Assistant config directory
cd /config

# Create custom_components if it doesn't exist
mkdir -p custom_components

# Copy the integration
cp -r monitormysolar custom_components/
```
4. Restart Home Assistant

## Step 5: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Monitor My Solar"
4. Follow the configuration wizard

## Next Steps

- [Initial Setup](Initial-Setup) - Configure your first dongle
- [Multi-Inverter Setup](Multi-Inverter-Setup) - Add additional inverters
- [GridBoss Configuration](GridBoss-Configuration) - Enable GridBoss features

## Troubleshooting Installation

### Integration Not Found
- Ensure you've restarted Home Assistant after installation
- Check the custom_components directory structure
- Verify no errors in Home Assistant logs

### HACS Issues
- Update HACS to the latest version
- Clear browser cache
- Try manual installation method

### Permission Errors
- Ensure proper file permissions:
```bash
chmod -R 755 custom_components/monitormysolar
```

## Updating the Integration

### Via HACS
1. Open HACS → Integrations
2. Find "Monitor My Solar"
3. Click **Update** when available
4. Restart Home Assistant

### Manual Update
1. Download new version
2. Replace the `monitormysolar` folder
3. Restart Home Assistant

⚠️ **Important**: Always check the [Migration Guide](Migration-Guide) when updating between major versions.