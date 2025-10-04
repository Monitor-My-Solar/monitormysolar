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

The Monitor My Solar integration uses a multi-step configuration wizard to guide you through setup.

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Monitor My Solar"**
4. Follow the configuration wizard steps:

### Step 1: Basic Configuration

| Field | Description | Example |
|-------|-------------|---------|
| **Inverter Brand** | Select your inverter manufacturer | LuxPower, Solis, Solax, Growatt |
| **Update Interval** | How often to write to database | 1 minute (default) |

### Step 2: Setup Type Selection

Choose your setup type:

| Option | Description | Use Case |
|--------|-------------|----------|
| **Single Inverter (Standard Setup)** | One inverter with one dongle | Basic single inverter setup |
| **Parallel Inverters** | Multiple inverters in parallel | 2-6 inverters working together |
| **Single GridBoss Setup** | One GridBoss with up to 3 slave inverters | GridBoss distribution system |
| **Dual GridBoss Setup** | Two GridBoss units with slaves | Large GridBoss distribution system |

### Step 3: Dongle Configuration

Based on your setup type, you'll configure your dongles:

#### Single Inverter Setup
| Field | Description | Example |
|-------|-------------|---------|
| **Dongle ID** | From dongle web interface | dongle-12:34:56:78:90:ab |
| **Dongle IP** | IP address for firmware updates (optional) | 192.168.1.150 |

#### Parallel Inverters Setup
| Field | Description | Example |
|-------|-------------|---------|
| **Master Dongle ID** | Primary dongle ID | dongle-12:34:56:78:90:ab |
| **Master Dongle IP** | Master dongle IP (optional) | 192.168.1.150 |
| **Slave Dongle ID 1-5** | Additional dongle IDs (optional) | dongle-12:34:56:78:90:ac |

#### Single GridBoss Setup
| Field | Description | Example |
|-------|-------------|---------|
| **GridBoss Dongle ID** | GridBoss dongle ID | dongle-12:34:56:78:90:ab |
| **GridBoss Dongle IP** | GridBoss dongle IP (optional) | 192.168.1.150 |
| **Slave Dongle ID 1-3** | Slave inverter dongle IDs (optional) | dongle-12:34:56:78:90:ac |

#### Dual GridBoss Setup
| Field | Description | Example |
|-------|-------------|---------|
| **GridBoss 1 Dongle ID** | First GridBoss dongle ID | dongle-12:34:56:78:90:ab |
| **GridBoss 1 Dongle IP** | First GridBoss dongle IP (optional) | 192.168.1.150 |
| **GridBoss 1 Slave IDs** | Up to 3 slave dongle IDs (optional) | dongle-12:34:56:78:90:ac |
| **GridBoss 2 Dongle ID** | Second GridBoss dongle ID | dongle-12:34:56:78:90:ad |
| **GridBoss 2 Dongle IP** | Second GridBoss dongle IP (optional) | 192.168.1.151 |
| **GridBoss 2 Slave IDs** | Up to 3 slave dongle IDs (optional) | dongle-12:34:56:78:90:ae |

### Dongle ID Format

The integration automatically normalizes dongle IDs to the correct format:
- **Input**: `12:34:56:78:90:ab` or `dongle-12:34:56:78:90:ab` or `1234567890ab`
- **Normalized**: `dongle-12:34:56:78:90:AB`

⚠️ **Important**: Dongle IDs are case-insensitive and will be automatically formatted.

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

## Step 4: Post-Setup Configuration

### Integration Options

After initial setup, you can access additional configuration options:

1. Go to **Settings** → **Devices & Services**
2. Click on your Monitor My Solar integration
3. Click the **"Configure"** button (gear icon)
4. Choose from these options:

#### Manage Dongles
- **Add new dongle**: Add additional dongles to your setup
- **Remove existing dongle**: Remove dongles (minimum 1 required)
- **Update dongle IPs**: Change IP addresses for firmware updates

#### Update Settings
- **Update Interval**: Change how often data is written to database
- **GridBoss Settings**: Enable/disable GridBoss features

#### Check Status
- **Dongle Connectivity**: Test if dongles are responding
- **Firmware Information**: View firmware codes and versions
- **Entity Count**: See total number of entities created
- **Setup Errors**: Review any configuration issues

### Connection Testing

The integration automatically tests dongle connections when:
- Adding new dongles
- Checking status
- During initial setup

If a dongle doesn't respond:
1. Check network connectivity
2. Verify MQTT broker connection
3. Confirm dongle is powered and connected
4. Check dongle web interface shows "Connected"

## Step 5: Configure Dashboard

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

### Configuration Wizard Issues

**Symptoms**: Can't complete setup wizard or wrong setup type selected

**Solutions**:
1. **Wrong Setup Type**: Use the integration options to reconfigure:
   - Go to integration settings → Configure
   - Choose "Update Settings" to change GridBoss settings
   - Use "Manage Dongles" to add/remove dongles
2. **Missing Dongle IDs**: Ensure you have all dongle IDs from web interfaces
3. **Invalid Dongle Format**: The integration auto-normalizes IDs, but ensure they're valid MAC addresses

### No Entities Created

**Symptoms**: Integration added but no entities appear

**Solutions**:
1. Check MQTT broker logs for connection from dongle
2. Verify dongle ID format (integration auto-normalizes)
3. Check firmware code is being received (logs)
4. Use "Check Status" in integration options to test connectivity
5. Restart Home Assistant

### Entities Show "Unavailable"

**Symptoms**: Entities exist but show no data

**Solutions**:
1. Verify MQTT messages arriving:
   - Install MQTT Explorer
   - Connect to your broker
   - Check for topics: `dongle-XX:XX:XX:XX:XX:XX/#`
2. Check dongle web interface shows "Connected"
3. Verify network connectivity
4. Use "Check Status" to test dongle connectivity

### Wrong Firmware Code

**Symptoms**: Missing expected entities

**Solutions**:
1. Check logs for firmware code received
2. Verify dongle firmware version (v3.0.0+)
3. Use "Check Status" to view firmware information
4. Contact support if firmware code unexpected

### GridBoss Setup Issues

**Symptoms**: GridBoss features not working or missing entities

**Solutions**:
1. Verify you selected the correct GridBoss setup type
2. Check GridBoss dongle is responding (use "Check Status")
3. Ensure slave dongles are properly configured
4. Verify GridBoss firmware supports the features you're trying to use

### Multi-Dongle Setup Issues

**Symptoms**: Some dongles not working in parallel/GridBoss setup

**Solutions**:
1. Test each dongle individually using "Check Status"
2. Verify all dongles are on the same network
3. Check MQTT broker can reach all dongles
4. Use "Manage Dongles" to add/remove problematic dongles

## Next Steps

- [Supported Entities](Supported-Entities) - Understand available entities
- [Conditional Entity System](Conditional-Entity-System) - Learn about dynamic entity availability
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