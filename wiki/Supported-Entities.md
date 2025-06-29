# Supported Entities

This page details all available entities for each supported inverter brand.

## Entity Overview

| Type | Count | Description |
|------|-------|-------------|
| **Sensors** | 100+ | Power, energy, voltage, current, temperature, status |
| **Binary Sensors** | 5+ | Charge/discharge indicators, fault states |
| **Switches** | 20+ | EPS, charging, discharge, operation modes |
| **Numbers** | 50+ | Limits, thresholds, power settings |
| **Time** | 40+ | Charge/discharge schedules |
| **Select** | 10+ | Time-based operation modes |
| **Buttons** | 2 | Restart inverter, manual updates |
| **Update** | 1 | Firmware updates with progress |

## LuxPower Entities

### Core Sensors

#### Power Sensors
| Entity ID | Description | Unit |
|-----------|-------------|------|
| `sensor.dongle_XX_ppv` | Solar power | W |
| `sensor.dongle_XX_ppv1` | String 1 power | W |
| `sensor.dongle_XX_ppv2` | String 2 power | W |
| `sensor.dongle_XX_ppv3` | String 3 power | W |
| `sensor.dongle_XX_pbat` | Battery power | W |
| `sensor.dongle_XX_pgrid` | Grid power (+ import, - export) | W |
| `sensor.dongle_XX_pload` | Load power | W |
| `sensor.dongle_XX_peps` | EPS/backup power | W |
| `sensor.dongle_XX_pinv` | Inverter output power | W |

#### Energy Sensors
| Entity ID | Description | Unit |
|-----------|-------------|------|
| `sensor.dongle_XX_epv_today` | Solar energy today | kWh |
| `sensor.dongle_XX_epv_total` | Total solar energy | kWh |
| `sensor.dongle_XX_ebat_today` | Battery energy today | kWh |
| `sensor.dongle_XX_eload_today` | Load energy today | kWh |
| `sensor.dongle_XX_egrid_today` | Grid energy today | kWh |
| `sensor.dongle_XX_egrid_feed` | Energy fed to grid | kWh |
| `sensor.dongle_XX_egrid_consume` | Energy from grid | kWh |

#### Voltage & Current
| Entity ID | Description | Unit |
|-----------|-------------|------|
| `sensor.dongle_XX_vpv1` | PV1 voltage | V |
| `sensor.dongle_XX_vpv2` | PV2 voltage | V |
| `sensor.dongle_XX_vpv3` | PV3 voltage | V |
| `sensor.dongle_XX_vbat` | Battery voltage | V |
| `sensor.dongle_XX_vgrid` | Grid voltage | V |
| `sensor.dongle_XX_veps` | EPS voltage | V |
| `sensor.dongle_XX_ipv1` | PV1 current | A |
| `sensor.dongle_XX_ipv2` | PV2 current | A |
| `sensor.dongle_XX_ibat` | Battery current | A |

#### Battery Information
| Entity ID | Description | Unit |
|-----------|-------------|------|
| `sensor.dongle_XX_soc` | State of charge | % |
| `sensor.dongle_XX_bms_soc` | BMS reported SOC | % |
| `sensor.dongle_XX_batcapacity` | Battery capacity | Ah |
| `sensor.dongle_XX_bms_battery_voltage` | BMS voltage | V |
| `sensor.dongle_XX_bms_battery_current` | BMS current | A |
| `sensor.dongle_XX_bms_max_charge_current` | Max charge current | A |
| `sensor.dongle_XX_bms_max_discharge_current` | Max discharge current | A |

#### Temperature Sensors
| Entity ID | Description | Unit |
|-----------|-------------|------|
| `sensor.dongle_XX_tinv` | Inverter temperature | °C |
| `sensor.dongle_XX_tbat` | Battery temperature | °C |
| `sensor.dongle_XX_tradiator1` | Radiator 1 temp | °C |
| `sensor.dongle_XX_tradiator2` | Radiator 2 temp | °C |
| `sensor.dongle_XX_maxcelltemp_bms` | Max cell temperature | °C |
| `sensor.dongle_XX_mincelltemp_bms` | Min cell temperature | °C |

#### Status Sensors
| Entity ID | Description | Values |
|-----------|-------------|--------|
| `sensor.dongle_XX_status` | Inverter status | Various states |
| `sensor.dongle_XX_fault_status` | Fault code | 0 = No fault |
| `sensor.dongle_XX_warning_status` | Warning code | 0 = No warning |
| `sensor.dongle_XX_uptime` | System uptime | seconds |

### Binary Sensors

| Entity ID | Description | States |
|-----------|-------------|--------|
| `binary_sensor.dongle_XX_battery_charging` | Battery charging | on/off |
| `binary_sensor.dongle_XX_battery_discharging` | Battery discharging | on/off |

### Switches

#### Basic Controls
| Entity ID | Description | Function |
|-----------|-------------|----------|
| `switch.dongle_XX_eps_enabled` | EPS/Backup power | Enable emergency power |
| `switch.dongle_XX_ac_charge_enabled` | AC charging | Allow grid charging |
| `switch.dongle_XX_charge_priority` | Charge priority | Battery/Load priority |
| `switch.dongle_XX_forced_discharge` | Force discharge | Force battery discharge |
| `switch.dongle_XX_normal_discharge` | Normal discharge | Standard discharge mode |

#### Advanced Controls
| Entity ID | Description | Function |
|-----------|-------------|----------|
| `switch.dongle_XX_feed_priority` | Feed priority | Solar/Battery to grid |
| `switch.dongle_XX_acfirstrealpower` | AC first power | Grid priority mode |
| `switch.dongle_XX_winter_mode` | Winter mode | Optimized for winter |
| `switch.dongle_XX_summer_mode` | Summer mode | Optimized for summer |

### Number Entities

#### Power Settings
| Entity ID | Range | Description |
|-----------|-------|-------------|
| `number.dongle_XX_ac_charge_power` | 0-6000W | AC charge rate |
| `number.dongle_XX_discharge_power` | 0-6000W | Discharge rate |
| `number.dongle_XX_discharge_power_percent` | 0-100% | Discharge percentage |
| `number.dongle_XX_grid_export_limit` | 0-10000W | Max export power |
| `number.dongle_XX_eps_power` | 0-6000W | EPS output power |

#### Battery Settings
| Entity ID | Range | Description |
|-----------|-------|-------------|
| `number.dongle_XX_charge_current_limit` | 0-200A | Max charge current |
| `number.dongle_XX_discharge_current_limit` | 0-200A | Max discharge current |
| `number.dongle_XX_discharge_cutoff_soc` | 10-100% | Min SOC before stop |
| `number.dongle_XX_charge_cutoff_soc` | 80-100% | Max SOC to charge |
| `number.dongle_XX_force_charge_soc` | 0-100% | Force charge below SOC |

#### Grid Settings
| Entity ID | Range | Description |
|-----------|-------|-------------|
| `number.dongle_XX_ac_charge_soc_limit` | 0-100% | Grid charge to SOC |
| `number.dongle_XX_start_ac_charge_soc` | 0-100% | Start grid charge SOC |
| `number.dongle_XX_ub_limitchgcurr` | 0-100A | Unbalanced charge limit |
| `number.dongle_XX_ub_limitdischgcurr` | 0-100A | Unbalanced discharge limit |

### Time Entities

#### Charge Schedule
| Entity ID | Format | Description |
|-----------|--------|-------------|
| `time.dongle_XX_ac_charge_start` | HH:MM | AC charge start time |
| `time.dongle_XX_ac_charge_end` | HH:MM | AC charge end time |
| `time.dongle_XX_ac_charge_start1` | HH:MM | Schedule 1 start |
| `time.dongle_XX_ac_charge_end1` | HH:MM | Schedule 1 end |
| `time.dongle_XX_ac_charge_start2` | HH:MM | Schedule 2 start |
| `time.dongle_XX_ac_charge_end2` | HH:MM | Schedule 2 end |

#### Discharge Schedule
| Entity ID | Format | Description |
|-----------|--------|-------------|
| `time.dongle_XX_discharge_start` | HH:MM | Discharge start time |
| `time.dongle_XX_discharge_end` | HH:MM | Discharge end time |
| `time.dongle_XX_discharge_start1` | HH:MM | Schedule 1 start |
| `time.dongle_XX_discharge_end1` | HH:MM | Schedule 1 end |
| `time.dongle_XX_discharge_start2` | HH:MM | Schedule 2 start |
| `time.dongle_XX_discharge_end2` | HH:MM | Schedule 2 end |

### Select Entities

Time period selectors with 48 30-minute slots:

| Entity ID | Description | Options |
|-----------|-------------|---------|
| `select.dongle_XX_time00` | 00:00-00:30 mode | Multiple modes |
| `select.dongle_XX_time01` | 00:30-01:00 mode | Multiple modes |
| ... | ... | ... |
| `select.dongle_XX_time47` | 23:30-00:00 mode | Multiple modes |

Mode options vary by firmware but typically include:
- Self Use
- Feed Priority
- Backup
- Peak Shaving

### Button Entities

| Entity ID | Description | Action |
|-----------|-------------|--------|
| `button.dongle_XX_invreboot` | Restart inverter | Reboots the inverter |

### Update Entity

| Entity ID | Description | Features |
|-----------|-------------|----------|
| `update.dongle_XX_firmware_update` | Firmware updates | Progress tracking, release notes |

## GridBoss Entities (IAAB Firmware)

GridBoss adds 190+ entities for advanced distribution control. See [GridBoss Configuration](GridBoss-Configuration) for detailed list.

### Key GridBoss Categories:
- **Grid monitoring**: Voltage, current, power per phase
- **Load control**: 6 controllable loads with scheduling
- **Generator**: Auto start/stop with thresholds
- **AC coupling**: External solar monitoring
- **3-phase**: Individual phase monitoring

## Combined Entities (Multi-Inverter)

When multiple inverters are configured, combined entities are created:

### Combined Sensors
All power and energy sensors have combined versions that sum values:
- `sensor.combined_ppv` - Total solar power
- `sensor.combined_pbat` - Total battery power
- `sensor.combined_pgrid` - Total grid power
- `sensor.combined_pload` - Total load power

### Combined Controls
All switches and numbers have combined versions that control all inverters:
- `switch.combined_eps_enabled`
- `switch.combined_ac_charge_enabled`
- `number.combined_discharge_cutoff_soc`

## Entity Attributes

Many entities include additional attributes:

### Power Sensors
```yaml
sensor.dongle_XX_ppv:
  state: 3500
  attributes:
    unit_of_measurement: W
    device_class: power
    state_class: measurement
    last_updated: 2024-01-15 10:30:00
```

### Status Sensors
```yaml
sensor.dongle_XX_fault_status:
  state: "No Fault"
  attributes:
    value: 0
    description: null
    start_time: null
    end_time: null
```

### BMS Sensors
```yaml
sensor.dongle_XX_bms_battery_voltage:
  state: 52.4
  attributes:
    cell_voltages: [3.35, 3.34, 3.35, ...]
    min_cell_voltage: 3.34
    max_cell_voltage: 3.35
```

## Firmware-Specific Entities

Different firmware codes enable different entities:

### Standard (Most Firmware)
- Basic power monitoring
- Battery management
- Grid interaction
- Time scheduling

### IAAB (GridBoss)
All standard entities plus:
- GridBoss monitoring
- Load control
- Generator management
- 3-phase monitoring

### US Models (Feature Code C)
- Different voltage ranges
- Grid code compliance
- Modified power limits

## Using Entities

### In Automations
```yaml
automation:
  - trigger:
      - platform: numeric_state
        entity_id: sensor.dongle_XX_soc
        below: 20
    action:
      - service: switch.turn_on
        entity_id: switch.dongle_XX_ac_charge_enabled
```

### In Scripts
```yaml
script:
  charge_to_80:
    sequence:
      - service: number.set_value
        target:
          entity_id: number.dongle_XX_charge_cutoff_soc
        data:
          value: 80
```

### In Templates
```yaml
template:
  - sensor:
      - name: "Battery Power kW"
        unit_of_measurement: "kW"
        state: >
          {{ (states('sensor.dongle_XX_pbat')|float / 1000)|round(2) }}
```

## Entity Best Practices

1. **Use state_class**: For energy tracking in statistics
2. **Monitor availability**: Check for unavailable states
3. **Handle units**: Convert W to kW for display
4. **Group related**: Create entity groups for organization
5. **Template carefully**: Add error handling to templates