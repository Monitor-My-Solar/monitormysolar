# Multi-Inverter Setup

This guide covers configuration and management of multiple parallel inverters.

## Overview

Monitor My Solar supports up to 4 parallel inverters per integration instance with:
- 🔄 Automatic synchronization of settings
- 📊 Combined virtual sensors
- 🎛️ Unified control interface
- 📈 Aggregated monitoring

## Initial Setup

### During First Installation

1. In the configuration wizard, check **"Parallel Inverters"**
2. Click **Submit**
3. Enter additional dongle IDs:
   - Dongle ID 2: `dongle-XX:XX:XX:XX:XX:XX`
   - Dongle ID 3: (optional)
   - Dongle ID 4: (optional)
4. Enter corresponding IP addresses (optional, for firmware updates)
5. Click **Submit**

### Adding Inverters to Existing Installation

1. Go to **Settings** → **Devices & Services**
2. Find Monitor My Solar → Click **Configure**
3. Select **"Manage Dongles"**
4. Choose **"Add new dongle"**
5. Enter the new dongle ID and IP
6. System will test connectivity
7. Integration reloads automatically

## Combined Entities

When multiple inverters are configured, the integration creates combined entities that aggregate data:

### Combined Sensors

These sensors sum values from all inverters:

| Entity | Description | Calculation |
|--------|-------------|-------------|
| `sensor.combined_ppv` | Total solar power | Sum of all ppv |
| `sensor.combined_pbat` | Total battery power | Sum of all pbat |
| `sensor.combined_pgrid` | Total grid power | Sum of all pgrid |
| `sensor.combined_pload` | Total load power | Sum of all pload |
| `sensor.combined_epv_today` | Total solar today | Sum of all epv_today |
| `sensor.combined_ebat_today` | Battery throughput today | Sum of all ebat_today |

### Combined Controls

Control all inverters simultaneously:

| Entity | Function |
|--------|----------|
| `switch.combined_eps_enabled` | Enable/disable EPS on all |
| `switch.combined_ac_charge_enabled` | Control AC charging |
| `switch.combined_charge_priority` | Set charge priority |
| `switch.combined_forced_discharge` | Force discharge mode |

### Combined Settings

Unified number inputs that update all inverters:

| Entity | Range | Description |
|--------|-------|-------------|
| `number.combined_ac_charge_power` | 0-6000W | AC charge rate |
| `number.combined_charge_current_limit` | 0-200A | Charge current |
| `number.combined_discharge_current_limit` | 0-200A | Discharge current |
| `number.combined_discharge_cutoff_soc` | 10-100% | Min SOC |

## Synchronization Features

### Automatic Sync

Enable automatic synchronization:

```yaml
switch.combined_sync_settings: on
```

When enabled:
- Settings changes on any inverter propagate to others
- Out-of-sync conditions are detected and corrected
- Sync status shows in `sensor.combined_sync_status`

### Sync Status Monitoring

The sync status sensor provides detailed information:

```yaml
sensor.combined_sync_status:
  state: "3 settings out of sync"
  attributes:
    synced_settings_sample:
      - "ac_charge_enabled: ✅ All synced (on)"
      - "charge_current_limit: ✅ All synced (50.0)"
    out_of_sync_settings:
      - "discharge_cutoff_soc: ❌ dongle-1: 20.0, dongle-2: 25.0"
      - "ac_charge_power: ❌ dongle-1: 3000, dongle-2: 2500"
    last_sync_check: "2024-01-15 10:30:00"
```

### Manual Sync

To manually sync a specific setting:

1. Use the combined entity to set the desired value
2. All inverters will update within seconds

Example:
```yaml
service: number.set_value
target:
  entity_id: number.combined_discharge_cutoff_soc
data:
  value: 20
```

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
      
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.dongle_1_soc
        name: Inverter 1
      - type: entity
        entity: sensor.dongle_2_soc
        name: Inverter 2
```

### Individual Inverter Cards

```yaml
type: grid
columns: 2
cards:
  - type: entities
    title: Inverter 1
    entities:
      - sensor.dongle_1_ppv
      - sensor.dongle_1_pbat
      - sensor.dongle_1_soc
      - sensor.dongle_1_tbat
      
  - type: entities
    title: Inverter 2
    entities:
      - sensor.dongle_2_ppv
      - sensor.dongle_2_pbat
      - sensor.dongle_2_soc
      - sensor.dongle_2_tbat
```

### Sync Control Panel

```yaml
type: entities
title: Synchronization Control
entities:
  - entity: switch.combined_sync_settings
    name: Auto Sync
  - entity: sensor.combined_sync_status
    name: Sync Status
  - type: divider
  - entity: number.combined_ac_charge_power
    name: AC Charge Rate (All)
  - entity: number.combined_discharge_cutoff_soc
    name: Min SOC (All)
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
          {% set soc1 = states('sensor.dongle_1_soc')|float %}
          {% set soc2 = states('sensor.dongle_2_soc')|float %}
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
          - sensor.dongle_1_soc
          - sensor.dongle_2_soc
        below: 20
    condition:
      - condition: numeric_state
        entity_id: sensor.dongle_1_soc
        below: 20
      - condition: numeric_state
        entity_id: sensor.dongle_2_soc
        below: 20
    action:
      - service: switch.turn_on
        entity_id: switch.combined_ac_charge_enabled
```

### Load Distribution

Distribute load based on battery SOC:

```yaml
automation:
  - alias: "Adjust discharge based on SOC"
    trigger:
      - platform: time_pattern
        minutes: "/5"
    action:
      - service: number.set_value
        target:
          entity_id: number.dongle_1_discharge_power_percent
        data:
          value: >
            {% set soc1 = states('sensor.dongle_1_soc')|float %}
            {% set soc2 = states('sensor.dongle_2_soc')|float %}
            {% set total = soc1 + soc2 %}
            {{ ((soc1 / total) * 100)|round }}
```

## Best Practices

### 1. Battery Management
- Keep batteries at similar SOC levels
- Use combined charging controls
- Monitor individual battery temperatures

### 2. Load Balancing
- Distribute loads evenly across inverters
- Monitor individual inverter loads
- Avoid overloading single units

### 3. Synchronization
- Enable auto-sync for consistent operation
- Monitor sync status regularly
- Address sync issues promptly

### 4. Firmware Updates
- Update all inverters to same firmware version
- Use staggered updates (one at a time)
- Test thoroughly after updates

## Troubleshooting

### Inverter Not Responding

1. Check individual dongle connectivity
2. Verify MQTT topics for missing dongle
3. Test using Check Status option
4. Restart specific dongle if needed

### Settings Not Syncing

1. Check sync switch is enabled
2. Verify all inverters have same firmware
3. Look at sync status attributes
4. Manually set via combined entity

### Combined Sensors Show Wrong Values

1. Ensure all dongles reporting data
2. Check for "unavailable" in individual sensors
3. Verify firmware codes match
4. Restart integration if needed

### Different Firmware Versions

If inverters have different features:
- Combined entities only show common features
- Individual entities show all features
- Update firmware for consistency

## Advanced Configuration

### Custom Combined Sensors

Create your own combined sensors:

```yaml
template:
  - sensor:
      - name: "Average Battery SOC"
        unit_of_measurement: "%"
        state: >
          {% set soc1 = states('sensor.dongle_1_soc')|float(0) %}
          {% set soc2 = states('sensor.dongle_2_soc')|float(0) %}
          {{ ((soc1 + soc2) / 2)|round(1) }}
          
      - name: "Total Battery Capacity"
        unit_of_measurement: "kWh"
        state: >
          {% set v1 = states('sensor.dongle_1_vbat')|float(0) %}
          {% set v2 = states('sensor.dongle_2_vbat')|float(0) %}
          {% set ah = 200 %}  # Battery Ah per inverter
          {{ ((v1 + v2) * ah / 1000)|round(2) }}
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
        entity_id: switch.dongle_2_eps_enabled
```

## Managing Dongles

### Add a Dongle
1. Configure → Manage Dongles → Add new dongle
2. Enter dongle ID and IP
3. Wait for connectivity test
4. Integration reloads automatically

### Remove a Dongle
1. Configure → Manage Dongles → Remove existing dongle
2. Select dongle to remove
3. Cannot remove last dongle
4. Integration reloads automatically

### Update IPs
1. Configure → Manage Dongles → Update dongle IPs
2. Enter new IP addresses
3. Used for firmware updates only
4. MQTT uses dongle ID for communication

## Support

For multi-inverter issues:
1. Include all dongle IDs
2. Specify which dongles affected
3. Include sync status information
4. Provide combined entity states