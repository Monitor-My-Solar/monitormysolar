# Multi-Inverter Setup

This guide covers the advanced features and management of multiple inverter configurations, including parallel inverters and GridBoss systems.

## Overview

Monitor My Solar supports multiple inverter configurations with:
- 🔄 Automatic synchronization of settings
- 📊 Combined virtual sensors
- 🎛️ Unified control interface
- 📈 Aggregated monitoring
- 🏗️ GridBoss distribution systems

## Setup Types

The integration supports several multi-inverter configurations:

| Setup Type | Description | Max Dongles | Use Case |
|------------|-------------|-------------|----------|
| **Parallel Inverters** | Multiple inverters working together | 6 total (1 master + 5 slaves) | Standard parallel setup |
| **Single GridBoss** | One GridBoss with slave inverters | 4 total (1 GridBoss + 3 slaves) | GridBoss distribution |
| **Dual GridBoss** | Two GridBoss units with slaves | 8 total (2 GridBoss + 6 slaves) | Large GridBoss systems |

## Initial Configuration

For initial setup instructions, see [Initial Setup](Initial-Setup.md). This guide covers the advanced features available after setup.

## Adding Inverters to Existing Installation

1. Go to **Settings** → **Devices & Services**
2. Find Monitor My Solar → Click **Configure**
3. Select **"Manage Dongles"**
4. Choose **"Add new dongle"**
5. Enter the new dongle ID and IP
6. System will test connectivity automatically
7. Integration reloads automatically

## Combined Entities

When multiple inverters are configured, the integration automatically creates combined entities that aggregate data and provide unified control.

### Combined Sensors

These sensors aggregate values from all inverters in your setup:

| Entity | Description | Calculation |
|--------|-------------|-------------|
| `sensor.combined_ppv` | Total solar power | Sum of all ppv values |
| `sensor.combined_pbat` | Total battery power | Sum of all pbat values |
| `sensor.combined_pgrid` | Total grid power | Sum of all pgrid values |
| `sensor.combined_pload` | Total load power | Sum of all pload values |
| `sensor.combined_epv_today` | Total solar energy today | Sum of all epv_today values |
| `sensor.combined_ebat_today` | Total battery throughput today | Sum of all ebat_today values |
| `sensor.combined_sync_status` | Synchronization status | Shows sync state and conflicts |

### Combined Controls

Control all inverters simultaneously with these switches:

| Entity | Function | Description |
|--------|----------|-------------|
| `switch.combined_eps_enabled` | EPS Control | Enable/disable EPS on all inverters |
| `switch.combined_ac_charge_enabled` | AC Charging | Control AC charging on all inverters |
| `switch.combined_charge_priority` | Charge Priority | Set charge priority for all inverters |
| `switch.combined_forced_discharge` | Force Discharge | Enable force discharge mode on all |

### Combined Settings

Unified number inputs that update all inverters simultaneously:

| Entity | Range | Description |
|--------|-------|-------------|
| `number.combined_ac_charge_power` | 0-6000W | AC charge rate for all inverters |
| `number.combined_charge_current_limit` | 0-200A | Charge current limit for all |
| `number.combined_discharge_current_limit` | 0-200A | Discharge current limit for all |
| `number.combined_discharge_cutoff_soc` | 10-100% | Minimum SOC for all inverters |

### GridBoss Combined Entities

For GridBoss setups, additional combined entities are available:

| Entity | Description | GridBoss Only |
|--------|-------------|---------------|
| `switch.combined_smartload1_enable` | SmartLoad 1 Control | ✅ |
| `switch.combined_smartload2_enable` | SmartLoad 2 Control | ✅ |
| `switch.combined_smartload3_enable` | SmartLoad 3 Control | ✅ |
| `switch.combined_smartload4_enable` | SmartLoad 4 Control | ✅ |

## Synchronization Features

The integration provides automatic synchronization capabilities to keep all inverters in your setup operating with consistent settings.

### How Synchronization Works

When you have multiple inverters configured:
- **Combined entities** automatically update all inverters when changed
- **Sync status monitoring** tracks which settings are synchronized
- **Automatic detection** identifies out-of-sync conditions
- **Real-time updates** ensure changes propagate quickly

### Sync Status Monitoring

The `sensor.combined_sync_status` provides detailed synchronization information:

```yaml
sensor.combined_sync_status:
  state: "2 settings out of sync"
  attributes:
    synced_settings_sample:
      - "ac_charge_enabled: ✅ All synced (on)"
      - "charge_current_limit: ✅ All synced (50.0)"
    out_of_sync_settings:
      - "discharge_cutoff_soc: ❌ dongle-12:34:56:78:90:ab: 20.0, dongle-12:34:56:78:90:ac: 25.0"
      - "ac_charge_power: ❌ dongle-12:34:56:78:90:ab: 3000, dongle-12:34:56:78:90:ac: 2500"
    last_sync_check: "2024-01-15 10:30:00"
    total_inverters: 2
    synced_count: 8
    out_of_sync_count: 2
```

### Using Combined Entities

Combined entities automatically synchronize settings across all inverters:

#### Example: Setting AC Charge Power
```yaml
service: number.set_value
target:
  entity_id: number.combined_ac_charge_power
data:
  value: 3000
```
This will set AC charge power to 3000W on all inverters simultaneously.

#### Example: Enabling EPS Mode
```yaml
service: switch.turn_on
target:
  entity_id: switch.combined_eps_enabled
```
This will enable EPS mode on all inverters at once.

### Sync Status Interpretation

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `"All settings synchronized"` | ✅ Perfect sync | None |
| `"X settings out of sync"` | ⚠️ Some differences | Use combined entities to sync |
| `"Sync check failed"` | ❌ Error occurred | Check connectivity |

### Best Practices for Synchronization

1. **Use Combined Entities**: Always use combined entities for settings that should be the same across all inverters
2. **Monitor Sync Status**: Check sync status regularly to catch drift
3. **Avoid Individual Changes**: Don't change individual inverter settings if you want them synchronized
4. **Test After Changes**: Verify sync status after making changes

## Configuration Examples

### Basic Monitoring Dashboard

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Combined System Status
    entities:
      - entity: sensor.combined_ppv
        name: Total Solar Power
      - entity: sensor.combined_pbat
        name: Total Battery Power
      - entity: sensor.combined_pgrid
        name: Grid Power
      - entity: sensor.combined_pload
        name: Load Power
      - entity: sensor.combined_sync_status
        name: Sync Status
      
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.dongle_12_34_56_78_90_ab_soc
        name: Inverter 1 SOC
      - type: entity
        entity: sensor.dongle_12_34_56_78_90_ac_soc
        name: Inverter 2 SOC
```

### Individual Inverter Cards

```yaml
type: grid
columns: 2
cards:
  - type: entities
    title: Inverter 1 (dongle-12:34:56:78:90:ab)
    entities:
      - sensor.dongle_12_34_56_78_90_ab_ppv
      - sensor.dongle_12_34_56_78_90_ab_pbat
      - sensor.dongle_12_34_56_78_90_ab_soc
      - sensor.dongle_12_34_56_78_90_ab_tbat
      
  - type: entities
    title: Inverter 2 (dongle-12:34:56:78:90:ac)
    entities:
      - sensor.dongle_12_34_56_78_90_ac_ppv
      - sensor.dongle_12_34_56_78_90_ac_pbat
      - sensor.dongle_12_34_56_78_90_ac_soc
      - sensor.dongle_12_34_56_78_90_ac_tbat
```

### Combined Control Panel

```yaml
type: entities
title: Combined System Control
entities:
  - entity: sensor.combined_sync_status
    name: Sync Status
  - type: divider
  - entity: switch.combined_eps_enabled
    name: EPS Mode (All)
  - entity: switch.combined_ac_charge_enabled
    name: AC Charging (All)
  - entity: number.combined_ac_charge_power
    name: AC Charge Rate (All)
  - entity: number.combined_discharge_cutoff_soc
    name: Min SOC (All)
```

### GridBoss Control Panel

For GridBoss setups, you can control SmartLoads across all inverters:

```yaml
type: entities
title: GridBoss SmartLoad Control
entities:
  - entity: switch.combined_smartload1_enable
    name: SmartLoad 1 (All)
  - entity: switch.combined_smartload2_enable
    name: SmartLoad 2 (All)
  - entity: switch.combined_smartload3_enable
    name: SmartLoad 3 (All)
  - entity: switch.combined_smartload4_enable
    name: SmartLoad 4 (All)
```

## Automation Examples

### Balance Battery SOC

Keep batteries balanced within 5%:

```yaml
automation:
  - alias: "Balance battery SOC"
    trigger:
      - platform: time_pattern
        minutes: "/10"
    condition:
      - condition: template
        value_template: >
          {% set soc1 = states('sensor.dongle_12_34_56_78_90_ab_soc')|float %}
          {% set soc2 = states('sensor.dongle_12_34_56_78_90_ac_soc')|float %}
          {{ (soc1 - soc2)|abs > 5 }}
    action:
      - service: notify.mobile_app
        data:
          message: "Battery imbalance detected: SOC difference > 5%"
```

### Coordinated Charging

Enable AC charging when all batteries are low:

```yaml
automation:
  - alias: "Enable AC charging on low SOC"
    trigger:
      - platform: numeric_state
        entity_id: 
          - sensor.dongle_12_34_56_78_90_ab_soc
          - sensor.dongle_12_34_56_78_90_ac_soc
        below: 20
    condition:
      - condition: numeric_state
        entity_id: sensor.dongle_12_34_56_78_90_ab_soc
        below: 20
      - condition: numeric_state
        entity_id: sensor.dongle_12_34_56_78_90_ac_soc
        below: 20
    action:
      - service: switch.turn_on
        entity_id: switch.combined_ac_charge_enabled
```

### Sync Status Monitoring

Alert when inverters go out of sync:

```yaml
automation:
  - alias: "Alert on sync issues"
    trigger:
      - platform: state
        entity_id: sensor.combined_sync_status
    condition:
      - condition: template
        value_template: >
          {{ not trigger.to_state.state.startswith('All settings') }}
    action:
      - service: notify.mobile_app
        data:
          message: "Inverter sync issue: {{ trigger.to_state.state }}"
```

### GridBoss SmartLoad Automation

Control SmartLoads based on battery SOC:

```yaml
automation:
  - alias: "Disable SmartLoads on low SOC"
    trigger:
      - platform: numeric_state
        entity_id: sensor.combined_soc
        below: 20
    action:
      - service: switch.turn_off
        entity_id: switch.combined_smartload1_enable
      - service: switch.turn_off
        entity_id: switch.combined_smartload2_enable
      - service: switch.turn_off
        entity_id: switch.combined_smartload3_enable
      - service: switch.turn_off
        entity_id: switch.combined_smartload4_enable
```

## Best Practices

### 1. Battery Management
- **Monitor SOC Balance**: Keep batteries at similar SOC levels across all inverters
- **Use Combined Controls**: Use combined charging/discharging controls for consistency
- **Temperature Monitoring**: Monitor individual battery temperatures
- **Load Distribution**: Distribute loads evenly across inverters

### 2. Synchronization
- **Use Combined Entities**: Always use combined entities for settings that should be synchronized
- **Monitor Sync Status**: Check `sensor.combined_sync_status` regularly
- **Address Drift**: Use combined entities to correct out-of-sync conditions
- **Avoid Individual Changes**: Don't change individual inverter settings if you want them synchronized

### 3. GridBoss Management
- **SmartLoad Coordination**: Use combined SmartLoad controls for consistent behavior
- **Conditional Entities**: Understand how [Conditional Entity System](Conditional-Entity-System) affects availability
- **Load Prioritization**: Set up proper SmartLoad priorities based on your needs

### 4. Firmware Updates
- **Consistent Versions**: Keep all inverters on the same firmware version
- **Staggered Updates**: Update one inverter at a time to maintain system stability
- **Test After Updates**: Verify all functionality after firmware updates

## Troubleshooting

### Inverter Not Responding

**Symptoms**: One or more inverters show as unavailable

**Solutions**:
1. Use **Check Status** in integration options to test connectivity
2. Verify MQTT broker can reach the dongle
3. Check dongle web interface shows "Connected"
4. Restart the specific dongle if needed
5. Use **Manage Dongles** to remove and re-add problematic dongles

### Settings Not Syncing

**Symptoms**: Inverters have different settings despite using combined entities

**Solutions**:
1. Check `sensor.combined_sync_status` for detailed sync information
2. Use combined entities to set the desired values
3. Verify all inverters have compatible firmware versions
4. Check for connectivity issues with individual dongles

### Combined Sensors Show Wrong Values

**Symptoms**: Combined sensors show incorrect or missing data

**Solutions**:
1. Check individual sensors for "unavailable" states
2. Verify all dongles are reporting data via MQTT
3. Ensure firmware codes are compatible
4. Restart the integration if needed

### GridBoss Issues

**Symptoms**: GridBoss features not working or missing entities

**Solutions**:
1. Verify GridBoss setup type was selected correctly
2. Check GridBoss dongle connectivity using **Check Status**
3. Ensure slave dongles are properly configured
4. Review [Conditional Entity System](Conditional-Entity-System) documentation

### Different Firmware Versions

**Symptoms**: Some features missing or inconsistent behavior

**Solutions**:
- Combined entities only show features available on all inverters
- Individual entities show all features for each inverter
- Update all inverters to the same firmware version for consistency
- Check firmware compatibility in the [Supported Entities](Supported-Entities) documentation

## Advanced Configuration

### Custom Combined Sensors

Create your own combined sensors using Home Assistant templates:

```yaml
template:
  - sensor:
      - name: "Average Battery SOC"
        unit_of_measurement: "%"
        state: >
          {% set soc1 = states('sensor.dongle_12_34_56_78_90_ab_soc')|float(0) %}
          {% set soc2 = states('sensor.dongle_12_34_56_78_90_ac_soc')|float(0) %}
          {{ ((soc1 + soc2) / 2)|round(1) }}
          
      - name: "Total Battery Capacity"
        unit_of_measurement: "kWh"
        state: >
          {% set v1 = states('sensor.dongle_12_34_56_78_90_ab_vbat')|float(0) %}
          {% set v2 = states('sensor.dongle_12_34_56_78_90_ac_vbat')|float(0) %}
          {% set ah = 200 %}  # Battery Ah per inverter
          {{ ((v1 + v2) * ah / 1000)|round(2) }}
          
      - name: "System Efficiency"
        unit_of_measurement: "%"
        state: >
          {% set solar = states('sensor.combined_ppv')|float(0) %}
          {% set load = states('sensor.combined_pload')|float(0) %}
          {% if solar > 0 %}
            {{ ((load / solar) * 100)|round(1) }}
          {% else %}
            0
          {% endif %}
```

### Per-Inverter Automations

Control inverters individually based on conditions:

```yaml
automation:
  - alias: "Disable inverter 2 on low load"
    trigger:
      - platform: numeric_state
        entity_id: sensor.combined_pload
        below: 2000
        for: "00:10:00"
    action:
      - service: switch.turn_off
        entity_id: switch.dongle_12_34_56_78_90_ac_eps_enabled
```

### Energy Dashboard Integration

Configure the Energy Dashboard for multi-inverter setups:

```yaml
# In Configuration → Energy → Individual Devices
Grid Consumption:
  - sensor.dongle_12_34_56_78_90_ab_pgrid
  - sensor.dongle_12_34_56_78_90_ac_pgrid

Solar Production:
  - sensor.combined_ppv

Battery:
  - sensor.combined_pbat
```

## Dongle Management

For adding, removing, or updating dongles, use the integration options:

1. Go to **Settings** → **Devices & Services**
2. Click on your Monitor My Solar integration
3. Click **Configure** (gear icon)
4. Choose **"Manage Dongles"**

### Available Options:
- **Add new dongle**: Add additional dongles to your setup
- **Remove existing dongle**: Remove dongles (minimum 1 required)
- **Update dongle IPs**: Change IP addresses for firmware updates

## Related Documentation

- [Initial Setup](Initial-Setup.md) - Basic configuration guide
- [Conditional Entity System](Conditional-Entity-System) - Dynamic entity availability
- [Supported Entities](Supported-Entities) - Complete entity reference
- [GridBoss Configuration](GridBoss-Configuration) - GridBoss-specific setup

## Support

For multi-inverter issues, include:
1. All dongle IDs in your setup
2. Which specific dongles are affected
3. Sync status information from `sensor.combined_sync_status`
4. Current states of combined entities
5. Setup type (parallel, single GridBoss, dual GridBoss)