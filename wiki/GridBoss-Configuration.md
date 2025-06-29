# GridBoss Configuration

GridBoss is an advanced distribution monitoring and control system for LuxPower inverters. This guide covers setup and configuration.

## Overview

GridBoss provides:
- 🔌 **House Backup** - Easy whole-house backup configuration
- ⚡ **Smart Load Control** - Manage up to 8 configurable loads
- 🔋 **Generator Integration** - Automatic start/stop control
- ☀️ **AC Coupling** - Monitor external solar systems
- 📊 **3-Phase Monitoring** - Individual L1, L2, L3 tracking
- ⏰ **Advanced Scheduling** - Time-based automation

## Requirements

- ✅ LuxPower inverter
- ✅ Firmware code **IAAB**
- ✅ GridBoss hardware unit
- ✅ Integration v3.0.0+

## Enabling GridBoss

### New Installation

During initial setup:
1. Check **"GridBoss Connected"** option
2. Complete setup normally

### Existing Installation

1. Go to **Settings** → **Devices & Services**
2. Find Monitor My Solar → Click **Configure**
3. Select **Update Settings**
4. Check **"GridBoss Connected"**
5. Click **Submit**
6. Integration will reload with GridBoss entities

## GridBoss Entities

When enabled, GridBoss adds 190+ new entities:

### Sensors (68 entities)

#### Power Monitoring
- `sensor.dongle_XX_gridboss_grid_voltage_l1` - L1 voltage
- `sensor.dongle_XX_gridboss_grid_voltage_l2` - L2 voltage
- `sensor.dongle_XX_gridboss_grid_voltage_l3` - L3 voltage
- `sensor.dongle_XX_gridboss_grid_current_l1` - L1 current
- `sensor.dongle_XX_gridboss_grid_power_l1` - L1 power
- `sensor.dongle_XX_gridboss_total_grid_power` - Total grid power

#### Load Monitoring
- `sensor.dongle_XX_gridboss_load1_power` through `load6_power`
- `sensor.dongle_XX_gridboss_load1_current` through `load6_current`
- `sensor.dongle_XX_gridboss_total_load_power`

#### Energy Tracking
- `sensor.dongle_XX_gridboss_total_energy_from_grid`
- `sensor.dongle_XX_gridboss_total_energy_to_grid`
- `sensor.dongle_XX_gridboss_generator_total_energy`

### Switches (17 entities)

#### Load Control
- `switch.dongle_XX_gridboss_load1_enabled` through `load6_enabled`
- `switch.dongle_XX_gridboss_generator_enabled`
- `switch.dongle_XX_gridboss_dry_contact_enabled`

#### System Control
- `switch.dongle_XX_gridboss_ac_couple_enabled`
- `switch.dongle_XX_gridboss_parallel_mode`
- `switch.dongle_XX_gridboss_three_phase_mode`

### Number Entities (56 entities)

#### Power Limits
- `number.dongle_XX_gridboss_generator_charge_power_limit`
- `number.dongle_XX_gridboss_load1_power_limit` through `load6_power_limit`
- `number.dongle_XX_gridboss_total_power_limit`

#### Voltage Settings
- `number.dongle_XX_gridboss_generator_startup_voltage`
- `number.dongle_XX_gridboss_generator_shutdown_voltage`

### Time Entities (48 entities)

#### Load Schedules
Each load (1-6) has:
- `time.dongle_XX_gridboss_load1_schedule_start`
- `time.dongle_XX_gridboss_load1_schedule_end`

#### Generator Schedule
- `time.dongle_XX_gridboss_generator_schedule_start`
- `time.dongle_XX_gridboss_generator_schedule_end`

## Configuration Examples

### Basic Load Control

Control loads based on battery SOC:

```yaml
automation:
  - alias: "Disable non-essential loads on low battery"
    trigger:
      - platform: numeric_state
        entity_id: sensor.dongle_XX_soc
        below: 20
    action:
      - service: switch.turn_off
        entity_id:
          - switch.dongle_XX_gridboss_load3_enabled
          - switch.dongle_XX_gridboss_load4_enabled
```

### Generator Auto-Start

Start generator on low battery:

```yaml
automation:
  - alias: "Auto-start generator"
    trigger:
      - platform: numeric_state
        entity_id: sensor.dongle_XX_vbat
        below: 47.5
    condition:
      - condition: state
        entity_id: switch.dongle_XX_gridboss_generator_enabled
        state: "off"
    action:
      - service: switch.turn_on
        entity_id: switch.dongle_XX_gridboss_generator_enabled
      - service: notify.mobile_app
        data:
          message: "Generator started - Low battery voltage"
```

### Time-Based Load Management

Schedule loads for off-peak usage:

```yaml
automation:
  - alias: "Enable water heater off-peak"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: switch.turn_on
        entity_id: switch.dongle_XX_gridboss_load1_enabled
      
  - alias: "Disable water heater peak"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: switch.turn_off
        entity_id: switch.dongle_XX_gridboss_load1_enabled
```

### Three-Phase Monitoring

Create a card showing phase balance:

```yaml
type: entities
title: Phase Balance
entities:
  - entity: sensor.dongle_XX_gridboss_grid_power_l1
    name: L1 Power
  - entity: sensor.dongle_XX_gridboss_grid_power_l2
    name: L2 Power
  - entity: sensor.dongle_XX_gridboss_grid_power_l3
    name: L3 Power
  - type: divider
  - entity: sensor.dongle_XX_gridboss_total_grid_power
    name: Total Power
```

## Advanced Features

### AC Coupling

Monitor external solar systems:

1. Enable AC coupling:
```yaml
switch.dongle_XX_gridboss_ac_couple_enabled: on
```

2. Monitor AC-coupled power:
```yaml
sensor.dongle_XX_gridboss_ac_couple_power
sensor.dongle_XX_gridboss_ac_couple_energy_today
```

### Dry Contact Integration

Use for external control signals:

```yaml
binary_sensor:
  - platform: template
    sensors:
      grid_failure:
        value_template: "{{ is_state('switch.dongle_XX_gridboss_dry_contact_enabled', 'on') }}"
        device_class: problem
```

### Load Priority Management

Set power limits for loads:

```yaml
script:
  set_load_priorities:
    sequence:
      - service: number.set_value
        target:
          entity_id: number.dongle_XX_gridboss_load1_power_limit
        data:
          value: 3000  # Essential loads - 3kW
      - service: number.set_value
        target:
          entity_id: number.dongle_XX_gridboss_load2_power_limit
        data:
          value: 2000  # Semi-essential - 2kW
      - service: number.set_value
        target:
          entity_id: number.dongle_XX_gridboss_load3_power_limit
        data:
          value: 1000  # Non-essential - 1kW
```

## Dashboard Examples

### GridBoss Overview Card

```yaml
type: vertical-stack
cards:
  - type: entities
    title: GridBoss Status
    entities:
      - entity: sensor.dongle_XX_gridboss_total_grid_power
        name: Grid Power
      - entity: sensor.dongle_XX_gridboss_total_load_power
        name: Total Load
      - entity: sensor.dongle_XX_gridboss_generator_power
        name: Generator
      
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.dongle_XX_gridboss_grid_voltage_l1
        name: L1
        min: 200
        max: 260
      - type: gauge
        entity: sensor.dongle_XX_gridboss_grid_voltage_l2
        name: L2
        min: 200
        max: 260
      - type: gauge
        entity: sensor.dongle_XX_gridboss_grid_voltage_l3
        name: L3
        min: 200
        max: 260
```

### Load Control Panel

```yaml
type: entities
title: Load Control
entities:
  - entity: switch.dongle_XX_gridboss_load1_enabled
    name: Water Heater
    secondary_info: last-changed
  - entity: switch.dongle_XX_gridboss_load2_enabled
    name: Pool Pump
  - entity: switch.dongle_XX_gridboss_load3_enabled
    name: Air Conditioner
  - entity: switch.dongle_XX_gridboss_load4_enabled
    name: EV Charger
```

## Troubleshooting

### GridBoss Entities Not Appearing

1. Verify firmware code is **IAAB**:
   - Check in integration configuration status
   - Look in Home Assistant logs

2. Ensure GridBoss is enabled:
   - Integration → Configure → Update Settings
   - Check "GridBoss Connected"

3. Restart Home Assistant after enabling

### Generator Not Starting

1. Check voltage thresholds:
   - `number.dongle_XX_gridboss_generator_startup_voltage`
   - Ensure set below current battery voltage for testing

2. Verify generator is enabled:
   - `switch.dongle_XX_gridboss_generator_enabled`

3. Check physical connections

### Load Control Not Working

1. Verify load is enabled in GridBoss
2. Check power limit settings
3. Ensure physical wiring is correct
4. Monitor load current/power sensors

## Best Practices

1. **Test Thoroughly**: Test load switching and generator control during installation
2. **Set Appropriate Limits**: Configure power limits to prevent overload
3. **Monitor Phase Balance**: Keep phases balanced for optimal performance
4. **Document Connections**: Label all GridBoss connections clearly
5. **Regular Testing**: Test generator auto-start monthly

## Support

For GridBoss-specific issues:
1. Include firmware code (IAAB) in reports
2. List which GridBoss features are enabled
3. Provide debug logs with GridBoss MQTT topics
4. Include photos of physical connections if relevant