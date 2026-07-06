# Monitor My Solar - Home Assistant Integration

[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](https://github.com/Monitor-My-Solar/monitormysolar)
[![Tests](https://github.com/Monitor-My-Solar/monitormysolar/actions/workflows/tests.yaml/badge.svg?branch=main)](https://github.com/Monitor-My-Solar/monitormysolar/actions/workflows/tests.yaml)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A powerful Home Assistant integration for solar inverter monitoring and control through Monitor My Solar hardware dongles.

## Dongle firmware 4.3.0+ recommended for v4.0.0.
- The integration still works with older dongle firmware, but the best experience
  (change-only data streaming, instant write confirmation, and over-the-air
  firmware updates) needs **firmware 4.3.0 or newer**.
- **Firmware updates from Home Assistant now require firmware 4.3.0+.** If your
  dongle is older, update it to 4.3.0 by the previous method or mobile app first.
- The dongle's IP address is **no longer needed** for anything in v4.0.0.

See the [CHANGELOG](custom_components/monitormysolar/CHANGELOG.md) for the full v4.0.0 notes.


## 🌟 Features

- **Real-time monitoring** of all inverter parameters
- **Full control** over inverter settings
- **Multi-inverter support** with automatic synchronization
- **GridBoss support** for advanced distribution monitoring
- **Conditional Entity System** - Smart entity availability based on configuration
- **Over-the-air firmware updates over MQTT** with live progress (firmware 4.3.0+)
- **No cloud dependency** - fully local control

## 📋 Supported Inverters

| Brand | Status | GridBoss Support |
|-------|--------|------------------|
| LuxPower | ✅ Fully Supported | ✅ GridBoss (I-family firmware) |
| Deye / SunSynk / SolArk / NeoVolta | ✅ Supported | ❌ |
| Solis | 🔜 Coming Soon | ❌ |
| Solax | 🔜 Coming Soon | ❌ |
| Growatt | 🔜 Coming Soon | ❌ |

## 🚀 Quick Start

### Prerequisites

1. **Monitor My Solar Dongle** - Purchase from [monitormy.solar](https://monitormy.solar)
2. **Home Assistant** with MQTT broker (Mosquitto recommended)
3. **HACS** installed for easy integration management

### ⚠️ Important Requirements

- MQTT broker must have username/password authentication
- Use 24-hour time format in Home Assistant (due to HA core bug)
- Dongle ID must be lowercase (e.g., `dongle-12:34:56:78:90:ab`)
- No SSL support for MQTT connections

## 📦 Installation

### Step 1: Install via HACS

1. Open HACS in Home Assistant
2. Click **"+ Explore & Download Repositories"**
3. Search for **"Monitor My Solar"**
4. Click **Download**
5. Restart Home Assistant

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/hacs.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/hacs.png?raw=true" alt="HACS Search Results" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

### Step 2: Configure Your Dongle

1. Access your dongle's web interface: `http://[DONGLE-IP]`
2. Enable **"Local MQTT Server"**
3. Configure MQTT settings:
   - Server: `mqtt://[HOME-ASSISTANT-IP]:1883`
   - Username: Your MQTT username
   - Password: Your MQTT password
4. Click **Save** and wait for "Connected" status

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/donglemqtt.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/donglemqtt.png?raw=true" alt="Dongle MQTT Setup" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

### Step 3: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Monitor My Solar"**
4. Complete the 3-step setup:

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/integration.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/integration.png?raw=true" alt="Integration Setup" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

#### Step 1: Basic Configuration
| Field | Description | Example |
|-------|-------------|---------|
| Inverter Brand | Select your inverter manufacturer | LuxPower |
| Update Interval | How often to update data | 1 minute |

#### Step 2: Setup Type Selection
Choose your configuration:
- **Single Inverter** - Standard single inverter setup
- **Parallel Inverters** - Multiple inverters working together
- **Single GridBoss** - One inverter with GridBoss distribution
- **Dual GridBoss** - Two GridBoss units for larger systems

#### Step 3: Dongle Configuration
Configure your dongle(s) based on setup type:

**Single Inverter:**
| Field | Description | Example |
|-------|-------------|---------|
| Dongle ID | From dongle web interface | dongle-12:34:56:78:90:ab |

> Note: The dongle IP address is no longer collected. Firmware updates and admin
> actions run over MQTT in v4.0.0.

**Parallel Inverters:**
- Master dongle ID (required)
- Up to 5 slave dongle IDs (optional)

**GridBoss Setup:**
- GridBoss dongle ID (required)
- Up to 3 slave dongle IDs (optional)

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/page1.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/page1.png?raw=true" alt="Integration Setup" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>
<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/setup_type.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/setup_type.png?raw=true" alt="Integration Setup" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

## 🆕 GridBoss Configuration

GridBoss support is available for LuxPower GridBoss units (I-family firmware). A
GridBoss unit is detected automatically from its firmware, so it appears as its own
device with only its relevant entities.

### GridBoss Setup Types

**Single GridBoss Setup:**
- One GridBoss unit with up to 3 slave inverters
- Perfect for residential installations
- Provides 4 SmartLoads and 4 AC Coupling ports

**Dual GridBoss Setup:**
- Two GridBoss units with up to 3 slaves each
- Ideal for larger commercial installations
- Provides 8 SmartLoads and 8 AC Coupling ports total

### GridBoss detection

GridBoss units are detected from their firmware, so there is no manual "GridBoss
Connected" toggle to set. Choose the Single GridBoss or Dual GridBoss setup type
when adding the integration, and enter the GridBoss dongle ID(s).



### GridBoss Features

- **Easy House Backup**: Easily backup your house loads
- **Smart Load Control**: Manage up to 4 configurable SmartLoads
- **Generator Integration**: Auto start/stop control
- **AC Coupling**: Monitor up to 4 external solar systems
- **Split-Phase Monitoring**: Individual L1, L2 tracking (USA standard)
- **Advanced Scheduling**: Time-based automation with multiple schedules
- **Port Exclusivity**: Each port can be SmartLoad OR AC Coupling (not both)

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/gridboss-overview.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/gridboss-overview.png?raw=true" alt="GridBoss Overview" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>



## 🔧 Configuration Options

Access via **Configure** button on the integration:

### 1. Manage Dongles
- Add parallel inverters
- Remove dongles
- Replace a dongle (transfers all entities and history to the new one)

### Restore Deleted Entities
- Bring back entities that were deleted or disabled, without deleting and re-adding
  the whole integration.

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/images/configflow.png" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/images/configflow.png" alt="Integration Setup" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

### 2. Update Settings
- Use input box for numbers (instead of sliders)
- Enable device grouping (organise entities into sub-devices)
- Add the dongle ID to entity names (single-dongle installs)
- Use Beta Firmware track

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/updateSettings.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/updateSettings.png?raw=true" alt="Update Settings" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

### 3. Check Status
- View connection status
- Check firmware versions
- Monitor entity counts

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/healthcheck.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/healthcheck.png?raw=true" alt="Integration Helth check" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

## 🔄 Firmware Updates

Firmware updates run **over MQTT** (firmware 4.3.0+ required), no dongle IP needed.

1. Click on the update entity
2. View available updates and release notes
3. Click **Install** to update
4. Monitor real-time progress; the dongle reboots during the update
5. Optional: choose the prod or beta track via the **Use Beta Firmware** setting

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/firmware.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/firmware.png?raw=true" alt="Integration Setup" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

## 🤝 Multi-Inverter Setup

### Automatic Synchronization

Enable setting synchronization across parallel inverters:

```yaml
switch.combined_sync_settings  # Enable/disable sync
sensor.combined_sync_status    # Monitor sync status
```

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/multipledongles.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/multipledongles.png?raw=true" alt="Integration Setup" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

## 🛠️ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| No entities created | Check MQTT connection and logs |
| Firmware timeout | Verify dongle ID is lowercase |
| Time settings not saving | Switch to 24-hour format |
| GridBoss entities missing | Verify the unit is a GridBoss (I-family firmware) |
| Entities grayed out | Check conditional entity configuration |
| Port settings unavailable | Set port mode first, then configure settings |
| Duplicate `_2` entities after upgrade | Cleaned up automatically on first start; see `monitormysolar_migration.log` in your config folder |
| An entity is stuck "unavailable" | Your unit may not report it (varies by family); remove it, or use Options → Restore Deleted Entities |


### Debug Tools

1. **MQTT Explorer** - Monitor MQTT traffic
2. **Home Assistant Logs** - Check for errors
3. **Dongle Web Interface** - Verify connection status

### Getting Help

1. Check existing [GitHub Issues](https://github.com/Monitor-My-Solar/monitormysolar/issues)
2. Include in bug reports:
   - Home Assistant version
   - Integration version
   - Dongle firmware version
   - Debug logs

## 📊 Entity Types

| Type | Count | Description |
|------|-------|-------------|
| Sensors | 100+ | Power, energy, temperature, etc. |
| Switches | 20+ | EPS, charging, discharge control |
| Numbers | 50+ | Limits, rates, thresholds |
| Time | 40+ | Charge/discharge schedules |
| Select | 10+ | Operating modes |
| Binary Sensors | 5+ | Status indicators |
| Update | 1 per dongle | Firmware updates |


## 🔗 Resources

- **Hardware**: [monitormy.solar](https://monitormy.solar)
- **Documentation**: [GitHub Wiki](https://github.com/Monitor-My-Solar/monitormysolar/wiki)
- **Support**: [GitHub Issues](https://github.com/Monitor-My-Solar/monitormysolar/issues)
- **Community**: [Home Assistant Forum](https://community.home-assistant.io/)

### Key Documentation Links

- [Initial Setup Guide](https://github.com/Monitor-My-Solar/monitormysolar/wiki/Initial-Setup)
- [GridBoss Configuration](https://github.com/Monitor-My-Solar/monitormysolar/wiki/GridBoss-Configuration)
- [Supported Entities](https://github.com/Monitor-My-Solar/monitormysolar/wiki/Supported-Entities)
- [Conditional Entity System](https://github.com/Monitor-My-Solar/monitormysolar/wiki/Conditional-Entity-System)
- [Multi-Inverter Setup](https://github.com/Monitor-My-Solar/monitormysolar/wiki/Multi-Inverter-Setup)
- [Common Issues](https://github.com/Monitor-My-Solar/monitormysolar/wiki/Common-Issues)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: This integration requires official Monitor My Solar hardware. Third-party hardware is not supported.