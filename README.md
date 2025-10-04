# Monitor My Solar - Home Assistant Integration

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/Monitor-My-Solar/monitormysolar)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A powerful Home Assistant integration for solar inverter monitoring and control through Monitor My Solar hardware dongles.

## Dongles are required to be on Version 3.0.0 for all the features below to work.
- Dongles that do not update to Version 3.0.0 before 02/07/2025 will no longer receive OTA updates and you will need to contact Monitor My Solar to get a upgrade path


## 🌟 Features

- **Real-time monitoring** of all inverter parameters
- **Full control** over inverter settings
- **Multi-inverter support** with automatic synchronization
- **GridBoss support** (NEW in v3.0.0) for advanced distribution monitoring
- **Conditional Entity System** - Smart entity availability based on configuration
- **Firmware updates** with progress tracking
- **No cloud dependency** - fully local control

## 📋 Supported Inverters

| Brand | Status | GridBoss Support |
|-------|--------|------------------|
| LuxPower | ✅ Fully Supported | ✅ IAAB Firmware |
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
| Dongle IP | For firmware updates (optional) | 192.168.1.150 |

**Parallel Inverters:**
- Master dongle ID (required)
- Up to 5 slave dongle IDs (optional)
- IP addresses for each dongle (optional)

**GridBoss Setup:**
- GridBoss dongle ID (required)
- Up to 3 slave dongle IDs (optional)
- IP addresses for each dongle (optional)

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

## 🆕 GridBoss Configuration (v3.0.0)

GridBoss support is available for LuxPower inverters with firmware code **IAAB**.

### GridBoss Setup Types

**Single GridBoss Setup:**
- One GridBoss unit with up to 3 slave inverters
- Perfect for residential installations
- Provides 4 SmartLoads and 4 AC Coupling ports

**Dual GridBoss Setup:**
- Two GridBoss units with up to 3 slaves each
- Ideal for larger commercial installations
- Provides 8 SmartLoads and 8 AC Coupling ports total

### Enabling GridBoss for Existing Installations

1. Go to integration → **Configure**
2. Select **Update Settings**
3. Check **"GridBoss Connected"**
4. Click **Submit**



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
- Update IP addresses

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/images/configflow.png" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/images/configflow.png" alt="Integration Setup" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
  </a>
</p>

### 2. Update Settings
- Database write intervals
- GridBoss enable/disable

<p align="center">
  <a href="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/update-settings.png?raw=true" target="_blank">
    <img src="https://github.com/Monitor-My-Solar/monitormysolar/blob/main/images/update-settings.png?raw=true" alt="Update Settings" width="600" style="cursor:pointer; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" title="Click to view full size" />
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

1. Ensure dongle IP is configured
2. Click on the update entity
3. View available updates and release notes
4. Click **Install** to update
5. Monitor real-time progress

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
| GridBoss entities missing | Verify firmware code IAAB |
| Entities grayed out | Check conditional entity configuration |
| Port settings unavailable | Set port mode first, then configure settings |


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