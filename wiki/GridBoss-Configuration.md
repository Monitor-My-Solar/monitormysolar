# GridBoss Configuration

GridBoss is an advanced distribution monitoring and control system for LuxPower inverters. This guide covers setup and configuration.

## Overview

GridBoss provides:
- 🔌 **House Backup** - Easy whole-house backup configuration
- ⚡ **Smart Load Control** - Manage up to 4 configurable SmartLoads
- 🔋 **Generator Integration** - Automatic start/stop control
- ☀️ **AC Coupling** - Monitor up to 4 external solar systems
- 📊 **Split-Phase Monitoring** - Individual L1, L2 tracking (USA standard)
- ⏰ **Advanced Scheduling** - Time-based automation with multiple schedules

### ⚠️ **Important: Port Exclusivity & Configuration Sequence**
Each of the 4 ports can be configured as **either** a SmartLoad **or** AC Coupling, but **not both**. The port mode determines which functionality is available for that specific port.

**🔧 Configuration Sequence:**
1. **First**: Set the port mode (`SmartLoadX_PortMode`) to "Smart Load" or "Ac Coupled"
2. **Then**: Configure the port-specific settings (switches, numbers, time schedules, etc.)

**❌ Common Mistake**: Trying to configure port settings before setting the port mode will result in unavailable/grayed-out entities.

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

### Sensors (80+ entities)

#### GridBoss Status & Monitoring
- `sensor.dongle_XX_midboxStatus` - GridBoss Status
- `sensor.dongle_XX_gridRMSVoltage` - Grid RMS Voltage
- `sensor.dongle_XX_buRMSVoltage` - BU (Backup) RMS Voltage
- `sensor.dongle_XX_genRMSVoltage` - Generator RMS Voltage
- `sensor.dongle_XX_PhaseLockFreq` - Phase Lock Frequency
- `sensor.dongle_XX_GridFreq` - Grid Frequency
- `sensor.dongle_XX_GenFreq` - Generator Frequency
- `sensor.dongle_XX_SmartPortMode` - Smart Port Mode

#### Split-Phase Voltage Monitoring (L1/L2)
- `sensor.dongle_XX_gridL1RMSVoltage` - Grid L1 RMS Voltage
- `sensor.dongle_XX_gridL2RMSVoltage` - Grid L2 RMS Voltage
- `sensor.dongle_XX_buL1RMSVoltage` - BU L1 RMS Voltage
- `sensor.dongle_XX_buL2RMSVoltage` - BU L2 RMS Voltage
- `sensor.dongle_XX_genL1RMSVoltage` - Generator L1 RMS Voltage
- `sensor.dongle_XX_genL2RMSVoltage` - Generator L2 RMS Voltage

#### Split-Phase Current Monitoring (L1/L2)
- `sensor.dongle_XX_gridL1RMSCurrent` - Grid L1 RMS Current
- `sensor.dongle_XX_gridL2RMSCurrent` - Grid L2 RMS Current
- `sensor.dongle_XX_loadL1RMSCurrent` - Load L1 RMS Current
- `sensor.dongle_XX_loadL2RMSCurrent` - Load L2 RMS Current
- `sensor.dongle_XX_genL1RMSCurrent` - Generator L1 RMS Current
- `sensor.dongle_XX_genL2RMSCurrent` - Generator L2 RMS Current
- `sensor.dongle_XX_buL1RMSCurrent` - BU L1 RMS Current
- `sensor.dongle_XX_buL2RMSCurrent` - BU L2 RMS Current

#### SmartLoad Current Monitoring (4 SmartLoads)
- `sensor.dongle_XX_smartLoad1L1RMSCurrent` - SmartLoad1 L1 RMS Current
- `sensor.dongle_XX_smartLoad1L2RMSCurrent` - SmartLoad1 L2 RMS Current
- `sensor.dongle_XX_smartLoad2L1RMSCurrent` - SmartLoad2 L1 RMS Current
- `sensor.dongle_XX_smartLoad2L2RMSCurrent` - SmartLoad2 L2 RMS Current
- `sensor.dongle_XX_smartLoad3L1RMSCurrent` - SmartLoad3 L1 RMS Current
- `sensor.dongle_XX_smartLoad3L2RMSCurrent` - SmartLoad3 L2 RMS Current
- `sensor.dongle_XX_smartLoad4L1RMSCurrent` - SmartLoad4 L1 RMS Current
- `sensor.dongle_XX_smartLoad4L2RMSCurrent` - SmartLoad4 L2 RMS Current

#### Split-Phase Power Monitoring (L1/L2)
- `sensor.dongle_XX_gridL1ActivePower` - Grid L1 Active Power
- `sensor.dongle_XX_gridL2ActivePower` - Grid L2 Active Power
- `sensor.dongle_XX_loadL1ActivePower` - Load L1 Active Power
- `sensor.dongle_XX_loadL2ActivePower` - Load L2 Active Power
- `sensor.dongle_XX_genL1ActivePower` - Generator L1 Active Power
- `sensor.dongle_XX_genL2ActivePower` - Generator L2 Active Power
- `sensor.dongle_XX_buL1ActivePower` - BU L1 Active Power
- `sensor.dongle_XX_buL2ActivePower` - BU L2 Active Power

#### SmartLoad Power Monitoring (4 SmartLoads)
- `sensor.dongle_XX_smartLoad1L1ActivePower` - SmartLoad1 L1 Active Power
- `sensor.dongle_XX_smartLoad1L2ActivePower` - SmartLoad1 L2 Active Power
- `sensor.dongle_XX_smartLoad2L1ActivePower` - SmartLoad2 L1 Active Power
- `sensor.dongle_XX_smartLoad2L2ActivePower` - SmartLoad2 L2 Active Power
- `sensor.dongle_XX_smartLoad3L1ActivePower` - SmartLoad3 L1 Active Power
- `sensor.dongle_XX_smartLoad3L2ActivePower` - SmartLoad3 L2 Active Power
- `sensor.dongle_XX_smartLoad4L1ActivePower` - SmartLoad4 L1 Active Power
- `sensor.dongle_XX_smartLoad4L2ActivePower` - SmartLoad4 L2 Active Power

#### Energy Tracking (Today)
- `sensor.dongle_XX_eLoad_TodayAll` - E Load Today All
- `sensor.dongle_XX_EtoGrid_TodayAll` - E to Grid Today All
- `sensor.dongle_XX_EtoUser_TodayAll` - E to User Today All
- `sensor.dongle_XX_Egen_TodayAll` - E Gen Today All
- `sensor.dongle_XX_ESmartLoad1_TodayAll` - E SmartLoad1 Today All
- `sensor.dongle_XX_ESmartLoad2_TodayAll` - E SmartLoad2 Today All
- `sensor.dongle_XX_ESmartLoad3_TodayAll` - E SmartLoad3 Today All
- `sensor.dongle_XX_ESmartLoad4_TodayAll` - E SmartLoad4 Today All
- `sensor.dongle_XX_EAcouple1_TodayAll` - E ACcouple1 Today All
- `sensor.dongle_XX_EAcouple2_TodayAll` - E ACcouple2 Today All
- `sensor.dongle_XX_EAcouple3_TodayAll` - E ACcouple3 Today All
- `sensor.dongle_XX_EAcouple4_TodayAll` - E ACcouple4 Today All

#### Energy Tracking (Total)
- `sensor.dongle_XX_ELoad_total` - E Load Total
- `sensor.dongle_XX_EBU_Total` - E BU Total
- `sensor.dongle_XX_EtoGrid_total` - E to Grid Total
- `sensor.dongle_XX_EtoUser_total` - E to User Total
- `sensor.dongle_XX_Egen_total` - E Gen Total
- `sensor.dongle_XX_ESmartLoad1_total` - E SmartLoad1 Total
- `sensor.dongle_XX_ESmartLoad2_total` - E SmartLoad2 Total
- `sensor.dongle_XX_ESmartLoad3_total` - E SmartLoad3 Total
- `sensor.dongle_XX_ESmartLoad4_total` - E SmartLoad4 Total
- `sensor.dongle_XX_EAcouple1_total` - E ACcouple1 Total
- `sensor.dongle_XX_EAcouple2_total` - E ACcouple2 Total
- `sensor.dongle_XX_EAcouple3_total` - E ACcouple3 Total
- `sensor.dongle_XX_EAcouple4_total` - E ACcouple4 Total
- `sensor.dongle_XX_MIDBoox_ACType` - MIDBox AC Type

### Switches (17 entities)

#### Generator Control
- `switch.dongle_XX_Generator_enable` - Generator Enable

#### SmartLoad Control (4 SmartLoads)
- `switch.dongle_XX_SmartLoad1_Enable` - SmartLoad1 Enable
- `switch.dongle_XX_SmartLoad2_Enable` - SmartLoad2 Enable
- `switch.dongle_XX_SmartLoad3_Enable` - SmartLoad3 Enable
- `switch.dongle_XX_SmartLoad4_Enable` - SmartLoad4 Enable
- `switch.dongle_XX_SmartLoad1_GridOn` - SmartLoad1 Grid On
- `switch.dongle_XX_SmartLoad2_GridOn` - SmartLoad2 Grid On
- `switch.dongle_XX_SmartLoad3_GridOn` - SmartLoad3 Grid On
- `switch.dongle_XX_SmartLoad4_GridOn` - SmartLoad4 Grid On
- `switch.dongle_XX_SmartLoad1_Shedding` - SmartLoad1 Shedding
- `switch.dongle_XX_SmartLoad2_Shedding` - SmartLoad2 Shedding
- `switch.dongle_XX_SmartLoad3_Shedding` - SmartLoad3 Shedding
- `switch.dongle_XX_SmartLoad4_Shedding` - SmartLoad4 Shedding

#### AC Coupling Control (4 AC Coupling Ports)
- `switch.dongle_XX_ACcouple1_Enable` - ACcouple1 Enable
- `switch.dongle_XX_ACcouple2_Enable` - ACcouple2 Enable
- `switch.dongle_XX_ACcouple3_Enable` - ACcouple3 Enable
- `switch.dongle_XX_ACcouple4_Enable` - ACcouple4 Enable

### Number Entities (56 entities)

#### Generator Settings
- `number.dongle_XX_Generator_Warmup` - Generator Warmup Time (0-600s)
- `number.dongle_XX_Generator_CoolDown` - Generator Cool Down Time (0-600s)
- `number.dongle_XX_Generator_Exercise_Period` - Generator Exercise Period (0-365d)

#### SmartLoad SOC Settings (4 SmartLoads)
- `number.dongle_XX_SmartLoad1_StartSOC` - SmartLoad1 Start SOC (0-100%)
- `number.dongle_XX_SmartLoad1_EndSOC` - SmartLoad1 End SOC (0-100%)
- `number.dongle_XX_SmartLoad2_StartSOC` - SmartLoad2 Start SOC (0-100%)
- `number.dongle_XX_SmartLoad2_EndSOC` - SmartLoad2 End SOC (0-100%)
- `number.dongle_XX_SmartLoad3_StartSOC` - SmartLoad3 Start SOC (0-100%)
- `number.dongle_XX_SmartLoad3_EndSOC` - SmartLoad3 End SOC (0-100%)
- `number.dongle_XX_SmartLoad4_StartSOC` - SmartLoad4 Start SOC (0-100%)
- `number.dongle_XX_SmartLoad4_EndSOC` - SmartLoad4 End SOC (0-100%)

#### SmartLoad Voltage Settings (4 SmartLoads)
- `number.dongle_XX_SmartLoad1_StartVolt` - SmartLoad1 Start Voltage (40-60V)
- `number.dongle_XX_SmartLoad1_EndVolt` - SmartLoad1 End Voltage (40-60V)
- `number.dongle_XX_SmartLoad2_StartVolt` - SmartLoad2 Start Voltage (40-60V)
- `number.dongle_XX_SmartLoad2_EndVolt` - SmartLoad2 End Voltage (40-60V)
- `number.dongle_XX_SmartLoad3_StartVolt` - SmartLoad3 Start Voltage (40-60V)
- `number.dongle_XX_SmartLoad3_EndVolt` - SmartLoad3 End Voltage (40-60V)
- `number.dongle_XX_SmartLoad4_StartVolt` - SmartLoad4 Start Voltage (40-60V)
- `number.dongle_XX_SmartLoad4_EndVolt` - SmartLoad4 End Voltage (40-60V)

#### AC Coupling SOC Settings (4 AC Coupling Ports)
- `number.dongle_XX_ACcouple1_StartSOC` - ACcouple1 Start SOC (0-100%)
- `number.dongle_XX_ACcouple1_EndSOC` - ACcouple1 End SOC (0-100%)
- `number.dongle_XX_ACcouple2_StartSOC` - ACcouple2 Start SOC (0-100%)
- `number.dongle_XX_ACcouple2_EndSOC` - ACcouple2 End SOC (0-100%)
- `number.dongle_XX_ACcouple3_StartSOC` - ACcouple3 Start SOC (0-100%)
- `number.dongle_XX_ACcouple3_EndSOC` - ACcouple3 End SOC (0-100%)
- `number.dongle_XX_ACcouple4_StartSOC` - ACcouple4 Start SOC (0-100%)
- `number.dongle_XX_ACcouple4_EndSOC` - ACcouple4 End SOC (0-100%)

#### AC Coupling Voltage Settings (4 AC Coupling Ports)
- `number.dongle_XX_ACcouple1_StartVolt` - ACcouple1 Start Voltage (40-60V)
- `number.dongle_XX_ACcouple1_EndVolt` - ACcouple1 End Voltage (40-60V)
- `number.dongle_XX_ACcouple2_StartVolt` - ACcouple2 Start Voltage (40-60V)
- `number.dongle_XX_ACcouple2_EndVolt` - ACcouple2 End Voltage (40-60V)
- `number.dongle_XX_ACcouple3_StartVolt` - ACcouple3 Start Voltage (40-60V)
- `number.dongle_XX_ACcouple3_EndVolt` - ACcouple3 End Voltage (40-60V)
- `number.dongle_XX_ACcouple4_StartVolt` - ACcouple4 Start Voltage (40-60V)
- `number.dongle_XX_ACcouple4_EndVolt` - ACcouple4 End Voltage (40-60V)

#### Shedding Settings (4 SmartLoads)
- `number.dongle_XX_SmartLoad1_SheddingStartPv_Power` - SmartLoad1 Shedding Start PV Power (0-10000W)
- `number.dongle_XX_SmartLoad2_SheddingStartPv_Power` - SmartLoad2 Shedding Start PV Power (0-10000W)
- `number.dongle_XX_SmartLoad3_SheddingStartPv_Power` - SmartLoad3 Shedding Start PV Power (0-10000W)
- `number.dongle_XX_SmartLoad4_SheddingStartPv_Power` - SmartLoad4 Shedding Start PV Power (0-10000W)
- `number.dongle_XX_SmartLoad1_SheddingStartSOC` - SmartLoad1 Shedding Start SOC (0-100%)
- `number.dongle_XX_SmartLoad1_SheddingEndSOC` - SmartLoad1 Shedding End SOC (0-100%)
- `number.dongle_XX_SmartLoad2_SheddingStartSOC` - SmartLoad2 Shedding Start SOC (0-100%)
- `number.dongle_XX_SmartLoad2_SheddingEndSOC` - SmartLoad2 Shedding End SOC (0-100%)
- `number.dongle_XX_SmartLoad3_SheddingStartSOC` - SmartLoad3 Shedding Start SOC (0-100%)
- `number.dongle_XX_SmartLoad3_SheddingEndSOC` - SmartLoad3 Shedding End SOC (0-100%)
- `number.dongle_XX_SmartLoad4_SheddingStartSOC` - SmartLoad4 Shedding Start SOC (0-100%)
- `number.dongle_XX_SmartLoad4_SheddingEndSOC` - SmartLoad4 Shedding End SOC (0-100%)
- `number.dongle_XX_SmartLoad1_SheddingStartVolt` - SmartLoad1 Shedding Start Voltage (40-60V)
- `number.dongle_XX_SmartLoad1_SheddingEndVolt` - SmartLoad1 Shedding End Voltage (40-60V)
- `number.dongle_XX_SmartLoad2_SheddingStartVolt` - SmartLoad2 Shedding Start Voltage (40-60V)
- `number.dongle_XX_SmartLoad2_SheddingEndVolt` - SmartLoad2 Shedding End Voltage (40-60V)
- `number.dongle_XX_SmartLoad3_SheddingStartVolt` - SmartLoad3 Shedding Start Voltage (40-60V)
- `number.dongle_XX_SmartLoad3_SheddingEndVolt` - SmartLoad3 Shedding End Voltage (40-60V)
- `number.dongle_XX_SmartLoad4_SheddingStartVolt` - SmartLoad4 Shedding Start Voltage (40-60V)
- `number.dongle_XX_SmartLoad4_SheddingEndVolt` - SmartLoad4 Shedding End Voltage (40-60V)
- `number.dongle_XX_Flash_5060hz` - Flash 50/60Hz (0-1)
- `number.dongle_XX_NEC_120CurrLimit` - NEC 120 Current Limit (0-200A)

### Select Entities (8 entities)

#### Port Mode Configuration (4 Ports - Exclusive Configuration)
**⚠️ Each port can only be configured as ONE mode at a time:**
- `select.dongle_XX_SmartLoad1_PortMode` - Smart Port 1 (Does Not Operate, Smart Load, Ac Coupled)
- `select.dongle_XX_SmartLoad2_PortMode` - Smart Port 2 (Does Not Operate, Smart Load, Ac Coupled)
- `select.dongle_XX_SmartLoad3_PortMode` - Smart Port 3 (Does Not Operate, Smart Load, Ac Coupled)
- `select.dongle_XX_SmartLoad4_PortMode` - Smart Port 4 (Does Not Operate, Smart Load, Ac Coupled)

**Port Mode Options:**
- **"Does Not Operate"** - Port is disabled
- **"Smart Load"** - Port functions as a SmartLoad (load control)
- **"Ac Coupled"** - Port functions as AC Coupling (external solar monitoring)

#### SmartLoad Mode Configuration (Only Available When Port Mode = "Smart Load")
- `select.dongle_XX_SmartLoad1_SOC_Volt` - Smart Load 1 Mode (Time, SOC/Volt)
- `select.dongle_XX_SmartLoad2_SOC_Volt` - Smart Load 2 Mode (Time, SOC/Volt)
- `select.dongle_XX_SmartLoad3_SOC_Volt` - Smart Load 3 Mode (Time, SOC/Volt)
- `select.dongle_XX_SmartLoad4_SOC_Volt` - Smart Load 4 Mode (Time, SOC/Volt)

**SmartLoad Mode Options:**
- **"Time"** - SmartLoad operates based on time schedules
- **"SOC/Volt"** - SmartLoad operates based on battery SOC/voltage thresholds

### Time Entities (48 entities)

#### SmartLoad Time Scheduling (4 SmartLoads, 3 schedules each)
Each SmartLoad has 3 time schedules (Start0/End0, Start1/End1, Start2/End2):
- `time.dongle_XX_SmartLoad1Start0` - SmartLoad1 Start0
- `time.dongle_XX_SmartLoad1End0` - SmartLoad1 End0
- `time.dongle_XX_SmartLoad1Start1` - SmartLoad1 Start1
- `time.dongle_XX_SmartLoad1End1` - SmartLoad1 End1
- `time.dongle_XX_SmartLoad1Start2` - SmartLoad1 Start2
- `time.dongle_XX_SmartLoad1End2` - SmartLoad1 End2
- `time.dongle_XX_SmartLoad2Start0` - SmartLoad2 Start0
- `time.dongle_XX_SmartLoad2End0` - SmartLoad2 End0
- `time.dongle_XX_SmartLoad2Start1` - SmartLoad2 Start1
- `time.dongle_XX_SmartLoad2End1` - SmartLoad2 End1
- `time.dongle_XX_SmartLoad2Start2` - SmartLoad2 Start2
- `time.dongle_XX_SmartLoad2End2` - SmartLoad2 End2
- `time.dongle_XX_SmartLoad3Start0` - SmartLoad3 Start0
- `time.dongle_XX_SmartLoad3End0` - SmartLoad3 End0
- `time.dongle_XX_SmartLoad3Start1` - SmartLoad3 Start1
- `time.dongle_XX_SmartLoad3End1` - SmartLoad3 End1
- `time.dongle_XX_SmartLoad3Start2` - SmartLoad3 Start2
- `time.dongle_XX_SmartLoad3End2` - SmartLoad3 End2
- `time.dongle_XX_SmartLoad4Start0` - SmartLoad4 Start0
- `time.dongle_XX_SmartLoad4End0` - SmartLoad4 End0
- `time.dongle_XX_SmartLoad4Start1` - SmartLoad4 Start1
- `time.dongle_XX_SmartLoad4End1` - SmartLoad4 End1
- `time.dongle_XX_SmartLoad4Start2` - SmartLoad4 Start2
- `time.dongle_XX_SmartLoad4End2` - SmartLoad4 End2

#### AC Coupling Time Scheduling (4 AC Coupling Ports, 3 schedules each)
Each AC Coupling port has 3 time schedules (Start0/End0, Start1/End1, Start2/End2):
- `time.dongle_XX_ACcouple1Start0` - ACcouple1 Start0
- `time.dongle_XX_ACcouple1End0` - ACcouple1 End0
- `time.dongle_XX_ACcouple1Start1` - ACcouple1 Start1
- `time.dongle_XX_ACcouple1End1` - ACcouple1 End1
- `time.dongle_XX_ACcouple1Start2` - ACcouple1 Start2
- `time.dongle_XX_ACcouple1End2` - ACcouple1 End2
- `time.dongle_XX_ACcouple2Start0` - ACcouple2 Start0
- `time.dongle_XX_ACcouple2End0` - ACcouple2 End0
- `time.dongle_XX_ACcouple2Start1` - ACcouple2 Start1
- `time.dongle_XX_ACcouple2End1` - ACcouple2 End1
- `time.dongle_XX_ACcouple2Start2` - ACcouple2 Start2
- `time.dongle_XX_ACcouple2End2` - ACcouple2 End2
- `time.dongle_XX_ACcouple3Start0` - ACcouple3 Start0
- `time.dongle_XX_ACcouple3End0` - ACcouple3 End0
- `time.dongle_XX_ACcouple3Start1` - ACcouple3 Start1
- `time.dongle_XX_ACcouple3End1` - ACcouple3 End1
- `time.dongle_XX_ACcouple3Start2` - ACcouple3 Start2
- `time.dongle_XX_ACcouple3End2` - ACcouple3 End2
- `time.dongle_XX_ACcouple4Start0` - ACcouple4 Start0
- `time.dongle_XX_ACcouple4End0` - ACcouple4 End0
- `time.dongle_XX_ACcouple4Start1` - ACcouple4 Start1
- `time.dongle_XX_ACcouple4End1` - ACcouple4 End1
- `time.dongle_XX_ACcouple4Start2` - ACcouple4 Start2
- `time.dongle_XX_ACcouple4End2` - ACcouple4 End2

## Configuration Examples

### Basic SmartLoad Control

Control SmartLoads based on battery SOC:

```yaml
automation:
  - alias: "Disable non-essential SmartLoads on low battery"
    trigger:
      - platform: numeric_state
        entity_id: sensor.dongle_12_34_56_78_90_ab_soc
        below: 20
    action:
      - service: switch.turn_off
        entity_id:
          - switch.dongle_12_34_56_78_90_ab_SmartLoad3_Enable
          - switch.dongle_12_34_56_78_90_ab_SmartLoad4_Enable
```

### Generator Auto-Start

Start generator on low battery:

```yaml
automation:
  - alias: "Auto-start generator"
    trigger:
      - platform: numeric_state
        entity_id: sensor.dongle_12_34_56_78_90_ab_vbat
        below: 47.5
    condition:
      - condition: state
        entity_id: switch.dongle_12_34_56_78_90_ab_Generator_enable
        state: "off"
    action:
      - service: switch.turn_on
        entity_id: switch.dongle_12_34_56_78_90_ab_Generator_enable
      - service: notify.mobile_app
        data:
          message: "Generator started - Low battery voltage"
```

### Time-Based SmartLoad Management

Schedule SmartLoads for off-peak usage:

```yaml
# First, configure the port as a SmartLoad with Time mode
script:
  setup_smartload_time_mode:
    sequence:
      # Step 1: Set port mode to Smart Load (REQUIRED FIRST)
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad1_PortMode
        data:
          option: "Smart Load"
      # Step 2: Set SmartLoad mode to Time
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad1_SOC_Volt
        data:
          option: "Time"

# Then use automations to control the SmartLoad
automation:
  - alias: "Enable water heater off-peak"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: switch.turn_on
        entity_id: switch.dongle_12_34_56_78_90_ab_SmartLoad1_Enable
      
  - alias: "Disable water heater peak"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: switch.turn_off
        entity_id: switch.dongle_12_34_56_78_90_ab_SmartLoad1_Enable
```

### SmartLoad SOC-Based Control

Configure SmartLoad to operate based on battery SOC:

```yaml
script:
  configure_smartload_soc:
    sequence:
      # Step 1: Set port mode to Smart Load (REQUIRED FIRST)
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad1_PortMode
        data:
          option: "Smart Load"
      # Step 2: Set SmartLoad mode to SOC/Volt
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad1_SOC_Volt
        data:
          option: "SOC/Volt"
      # Step 3: Configure SOC thresholds
      - service: number.set_value
        target:
          entity_id: number.dongle_12_34_56_78_90_ab_SmartLoad1_StartSOC
        data:
          value: 80  # Start when SOC > 80%
      - service: number.set_value
        target:
          entity_id: number.dongle_12_34_56_78_90_ab_SmartLoad1_EndSOC
        data:
          value: 20  # Stop when SOC < 20%
```

### AC Coupling Configuration

Configure AC coupling for external solar:

```yaml
script:
  configure_ac_coupling:
    sequence:
      # First, set port mode to AC Coupled (this disables SmartLoad functionality)
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad1_PortMode
        data:
          option: "Ac Coupled"
      # Then enable AC coupling
      - service: switch.turn_on
        entity_id: switch.dongle_12_34_56_78_90_ab_ACcouple1_Enable
      # Configure AC coupling SOC thresholds
      - service: number.set_value
        target:
          entity_id: number.dongle_12_34_56_78_90_ab_ACcouple1_StartSOC
        data:
          value: 90  # Start AC coupling when SOC > 90%
```

### Port Configuration Examples

#### Example 1: Mixed Port Configuration
```yaml
script:
  configure_mixed_ports:
    sequence:
      # Port 1: SmartLoad
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad1_PortMode
        data:
          option: "Smart Load"
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad1_SOC_Volt
        data:
          option: "SOC/Volt"
      
      # Port 2: AC Coupling
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad2_PortMode
        data:
          option: "Ac Coupled"
      - service: switch.turn_on
        entity_id: switch.dongle_12_34_56_78_90_ab_ACcouple2_Enable
      
      # Port 3: Disabled
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad3_PortMode
        data:
          option: "Does Not Operate"
      
      # Port 4: SmartLoad with Time mode
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad4_PortMode
        data:
          option: "Smart Load"
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad4_SOC_Volt
        data:
          option: "Time"
```

#### Example 2: Converting Port from SmartLoad to AC Coupling
```yaml
script:
  convert_port_to_ac_coupling:
    sequence:
      # Step 1: Disable SmartLoad first
      - service: switch.turn_off
        entity_id: switch.dongle_12_34_56_78_90_ab_SmartLoad1_Enable
      
      # Step 2: Change port mode to AC Coupled
      - service: select.select_option
        target:
          entity_id: select.dongle_12_34_56_78_90_ab_SmartLoad1_PortMode
        data:
          option: "Ac Coupled"
      
      # Step 3: Enable AC coupling
      - service: switch.turn_on
        entity_id: switch.dongle_12_34_56_78_90_ab_ACcouple1_Enable
```

### Split-Phase Monitoring

Create a card showing split-phase balance (USA standard):

```yaml
type: entities
title: Split-Phase Balance
entities:
  - entity: sensor.dongle_12_34_56_78_90_ab_gridL1ActivePower
    name: L1 Power
  - entity: sensor.dongle_12_34_56_78_90_ab_gridL2ActivePower
    name: L2 Power
  - type: divider
  - entity: sensor.dongle_12_34_56_78_90_ab_gridL1RMSVoltage
    name: L1 Voltage
  - entity: sensor.dongle_12_34_56_78_90_ab_gridL2RMSVoltage
    name: L2 Voltage
```

## Advanced Features

### AC Coupling

Monitor external solar systems:

1. Enable AC coupling:
```yaml
switch.dongle_12_34_56_78_90_ab_ACcouple1_Enable: on
```

2. Monitor AC-coupled power:
```yaml
sensor.dongle_12_34_56_78_90_ab_EAcouple1_TodayAll  # Today's energy
sensor.dongle_12_34_56_78_90_ab_EAcouple1_total     # Total energy
```

### SmartLoad Shedding

Configure SmartLoad shedding based on PV power and SOC:

```yaml
script:
  configure_smartload_shedding:
    sequence:
      - service: switch.turn_on
        entity_id: switch.dongle_12_34_56_78_90_ab_SmartLoad1_Shedding
      - service: number.set_value
        target:
          entity_id: number.dongle_12_34_56_78_90_ab_SmartLoad1_SheddingStartPv_Power
        data:
          value: 5000  # Start shedding when PV > 5kW
      - service: number.set_value
        target:
          entity_id: number.dongle_12_34_56_78_90_ab_SmartLoad1_SheddingStartSOC
        data:
          value: 30  # Start shedding when SOC < 30%
```

### Generator Management

Configure generator with warmup and cooldown periods:

```yaml
script:
  configure_generator:
    sequence:
      - service: number.set_value
        target:
          entity_id: number.dongle_12_34_56_78_90_ab_Generator_Warmup
        data:
          value: 60  # 60 second warmup
      - service: number.set_value
        target:
          entity_id: number.dongle_12_34_56_78_90_ab_Generator_CoolDown
        data:
          value: 120  # 2 minute cooldown
      - service: number.set_value
        target:
          entity_id: number.dongle_12_34_56_78_90_ab_Generator_Exercise_Period
        data:
          value: 7  # Exercise weekly
```

## Dashboard Examples

### GridBoss Overview Card

```yaml
type: vertical-stack
cards:
  - type: entities
    title: GridBoss Status
    entities:
      - entity: sensor.dongle_12_34_56_78_90_ab_gridL1ActivePower
        name: Grid L1 Power
      - entity: sensor.dongle_12_34_56_78_90_ab_gridL2ActivePower
        name: Grid L2 Power
      - entity: sensor.dongle_12_34_56_78_90_ab_loadL1ActivePower
        name: Load L1 Power
      - entity: sensor.dongle_12_34_56_78_90_ab_loadL2ActivePower
        name: Load L2 Power
      - entity: sensor.dongle_12_34_56_78_90_ab_genL1ActivePower
        name: Generator L1 Power
      - entity: sensor.dongle_12_34_56_78_90_ab_genL2ActivePower
        name: Generator L2 Power
      
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.dongle_12_34_56_78_90_ab_gridL1RMSVoltage
        name: L1 Voltage
        min: 200
        max: 260
      - type: gauge
        entity: sensor.dongle_12_34_56_78_90_ab_gridL2RMSVoltage
        name: L2 Voltage
        min: 200
        max: 260
```

### SmartLoad Control Panel

```yaml
type: entities
title: SmartLoad Control
entities:
  - entity: switch.dongle_12_34_56_78_90_ab_SmartLoad1_Enable
    name: Water Heater
    secondary_info: last-changed
  - entity: switch.dongle_12_34_56_78_90_ab_SmartLoad2_Enable
    name: Pool Pump
  - entity: switch.dongle_12_34_56_78_90_ab_SmartLoad3_Enable
    name: Air Conditioner
  - entity: switch.dongle_12_34_56_78_90_ab_SmartLoad4_Enable
    name: EV Charger
```

### AC Coupling Monitoring

```yaml
type: entities
title: AC Coupling Status
entities:
  - entity: switch.dongle_12_34_56_78_90_ab_ACcouple1_Enable
    name: AC Couple 1
  - entity: switch.dongle_12_34_56_78_90_ab_ACcouple2_Enable
    name: AC Couple 2
  - entity: switch.dongle_12_34_56_78_90_ab_ACcouple3_Enable
    name: AC Couple 3
  - entity: switch.dongle_12_34_56_78_90_ab_ACcouple4_Enable
    name: AC Couple 4
  - type: divider
  - entity: sensor.dongle_12_34_56_78_90_ab_EAcouple1_TodayAll
    name: AC Couple 1 Today
  - entity: sensor.dongle_12_34_56_78_90_ab_EAcouple2_TodayAll
    name: AC Couple 2 Today
  - entity: sensor.dongle_12_34_56_78_90_ab_EAcouple3_TodayAll
    name: AC Couple 3 Today
  - entity: sensor.dongle_12_34_56_78_90_ab_EAcouple4_TodayAll
    name: AC Couple 4 Today
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

1. Check generator is enabled:
   - `switch.dongle_12_34_56_78_90_ab_Generator_enable`

2. Verify generator settings:
   - `number.dongle_12_34_56_78_90_ab_Generator_Warmup`
   - `number.dongle_12_34_56_78_90_ab_Generator_CoolDown`

3. Check physical connections

### SmartLoad Control Not Working

1. **First, verify port mode is set to Smart Load**:
   - `select.dongle_12_34_56_78_90_ab_SmartLoad1_PortMode` = "Smart Load"
   - **Critical**: Port must be in "Smart Load" mode before any SmartLoad settings are available

2. Verify SmartLoad is enabled:
   - `switch.dongle_12_34_56_78_90_ab_SmartLoad1_Enable` (etc.)

3. Check SmartLoad mode configuration:
   - `select.dongle_12_34_56_78_90_ab_SmartLoad1_SOC_Volt` (Time or SOC/Volt)

4. Verify SOC/voltage settings (only available if mode is SOC/Volt):
   - `number.dongle_12_34_56_78_90_ab_SmartLoad1_StartSOC`
   - `number.dongle_12_34_56_78_90_ab_SmartLoad1_EndSOC`

5. Monitor SmartLoad current/power sensors:
   - `sensor.dongle_12_34_56_78_90_ab_smartLoad1L1RMSCurrent`
   - `sensor.dongle_12_34_56_78_90_ab_smartLoad1L1ActivePower`

### AC Coupling Not Working

1. **First, verify port mode is set to AC Coupled**:
   - `select.dongle_12_34_56_78_90_ab_SmartLoad1_PortMode` = "Ac Coupled"
   - **Critical**: Port must be in "Ac Coupled" mode before any AC Coupling settings are available

2. Verify AC coupling is enabled:
   - `switch.dongle_12_34_56_78_90_ab_ACcouple1_Enable`

3. Monitor AC coupling energy:
   - `sensor.dongle_12_34_56_78_90_ab_EAcouple1_TodayAll`

### Port Mode Conflicts

1. **Cannot use both SmartLoad and AC Coupling on same port**:
   - If port is set to "Smart Load", AC Coupling entities will be unavailable
   - If port is set to "Ac Coupled", SmartLoad entities will be unavailable
   - Change port mode first, then configure the desired functionality

2. **Configuration sequence is critical**:
   - **Step 1**: Set port mode (`SmartLoadX_PortMode`) to "Smart Load" or "Ac Coupled"
   - **Step 2**: Configure port-specific settings (switches, numbers, time schedules)
   - **❌ Wrong**: Trying to configure settings before setting port mode results in unavailable entities

3. **Entity availability based on port mode**:
   - **"Smart Load" mode**: SmartLoad switches, SOC/Volt settings, time schedules available
   - **"Ac Coupled" mode**: AC Coupling switches, AC Coupling SOC/Volt settings, AC Coupling time schedules available
   - **"Does Not Operate" mode**: All port-specific entities unavailable

## Best Practices

1. **Test Thoroughly**: Test SmartLoad switching and generator control during installation
2. **Set Appropriate SOC/Voltage Limits**: Configure SOC and voltage thresholds for SmartLoads
3. **Monitor Split-Phase Balance**: Keep L1/L2 phases balanced for optimal performance
4. **Document Connections**: Label all GridBoss connections clearly
5. **Regular Testing**: Test generator auto-start monthly
6. **Configure Shedding**: Set up SmartLoad shedding for grid stability
7. **Use Time Schedules**: Configure multiple time schedules for flexible load management
8. **Monitor AC Coupling**: Track external solar system performance
9. **Plan Port Configuration**: Decide which ports will be SmartLoads vs AC Coupling before configuration
10. **Port Mode First**: Always set port mode before configuring port-specific settings
11. **Understand Exclusivity**: Remember that each port can only be one type at a time

## Support

For GridBoss-specific issues:
1. Include firmware code (IAAB) in reports
2. List which GridBoss features are enabled
3. Provide debug logs with GridBoss MQTT topics
4. Include photos of physical connections if relevant