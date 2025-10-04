# Supported Entities

This page details all available entities for LuxPower inverters supported by the Monitor My Solar integration.

## Entity Overview

| Type | Count | Description |
|------|-------|-------------|
| **Sensors** | 200+ | Power, energy, voltage, current, temperature, status, GridBoss monitoring |
| **Binary Sensors** | 2 | Battery charge/discharge indicators |
| **Switches** | 25+ | EPS, charging, discharge, operation modes, GridBoss controls |
| **Numbers** | 80+ | Limits, thresholds, power settings, GridBoss configuration |
| **Time** | 50+ | Charge/discharge schedules, GridBoss load scheduling |
| **Select** | 60+ | Time-based operation modes, GridBoss port modes |
| **Buttons** | 2 | Restart inverter, firmware updates |
| **Update** | 1 | Firmware updates with progress |

## Entity Naming Convention

All entities use the format: `{type}.dongle_{mac_address}_{unique_id}`

Where `{mac_address}` is the dongle's MAC address with colons replaced by underscores (e.g., `12_34_56_78_90_ab`)

Example: `sensor.dongle_12_34_56_78_90_ab_soc`

## LuxPower Entities

### Core Sensors

#### Power Sensors
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_ppv1` | PV1 Power | W | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |
| `sensor.dongle_XX_ppv2` | PV2 Power | W | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |
| `sensor.dongle_XX_ppv3` | PV3 Power | W | FAAB, FAAA, EAAA, EAAB, HAAA |
| `sensor.dongle_XX_ppv1` | PV Power (AC Coupled) | W | BAAA, BAAB |
| `sensor.dongle_XX_Pall` | Power PV All | W | All |
| `sensor.dongle_XX_pcharge` | Power Charge | W | All |
| `sensor.dongle_XX_pdischarge` | Power Discharge | W | All |
| `sensor.dongle_XX_pinv` | Power Inverter | W | All |
| `sensor.dongle_XX_prec` | Power Rectifier | W | All |
| `sensor.dongle_XX_peps` | Power EPS | W | All |
| `sensor.dongle_XX_ptogrid` | Power to Grid (live) | W | All |
| `sensor.dongle_XX_ptouser` | Power to User (live) | W | All |
| `sensor.dongle_XX_pload` | House Consumption (Live) | W | All |

#### Energy Sensors
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_epv1_day` | Energy PV1 Day | kWh | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |
| `sensor.dongle_XX_epv1_day` | PV Energy Day (AC Coupled) | kWh | BAAA, BAAB |
| `sensor.dongle_XX_epv2_day` | Energy PV2 Day | kWh | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |
| `sensor.dongle_XX_epv3_day` | Energy PV3 Day | kWh | FAAB, FAAA, EAAA, EAAB, HAAA |
| `sensor.dongle_XX_epv_all` | Total PV Day | kWh | All |
| `sensor.dongle_XX_einv_day` | Energy Inverter Day | kWh | All |
| `sensor.dongle_XX_erec_day` | Energy Rectifier Day | kWh | All |
| `sensor.dongle_XX_echg_day` | Energy Charge Day | kWh | All |
| `sensor.dongle_XX_edischg_day` | Energy Discharge Day | kWh | All |
| `sensor.dongle_XX_eeps_day` | Energy EPS Day | kWh | All |
| `sensor.dongle_XX_etogrid_day` | Energy to Grid Day | kWh | All |
| `sensor.dongle_XX_etouser_day` | Energy to User Day | kWh | All |
| `sensor.dongle_XX_epv1_all` | Energy PV1 All | kWh | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |
| `sensor.dongle_XX_epv1_all` | PV Energy All (AC Coupled) | kWh | BAAA, BAAB |
| `sensor.dongle_XX_epv2_all` | Energy PV2 All | kWh | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |
| `sensor.dongle_XX_epv3_all` | Energy PV3 All | kWh | FAAB, FAAA, EAAA, EAAB, HAAA |
| `sensor.dongle_XX_einv_all` | Energy Inverter All | kWh | All |
| `sensor.dongle_XX_erec_all` | Energy Rectifier All | kWh | All |
| `sensor.dongle_XX_echg_all` | Energy Charge All | kWh | All |
| `sensor.dongle_XX_edischg_all` | Energy Discharge All | kWh | All |
| `sensor.dongle_XX_eeps_all` | Energy EPS All | kWh | All |
| `sensor.dongle_XX_etogrid_all` | Energy to Grid All | kWh | All |
| `sensor.dongle_XX_etouser_all` | Energy to User All | kWh | All |
| `sensor.dongle_XX_HourlyConsumption` | Hourly Consumption | kWh | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |
| `sensor.dongle_XX_DailyConsumption` | Daily Consumption | kWh | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |

#### Voltage & Current
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_vpv1` | Voltage PV1 | V | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |
| `sensor.dongle_XX_vpv2` | Voltage PV2 | V | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa, HAAA, ceaa |
| `sensor.dongle_XX_vpv3` | Voltage PV3 | V | FAAB, FAAA, EAAA, EAAB |
| `sensor.dongle_XX_vbat` | Voltage Battery | V | All |
| `sensor.dongle_XX_vacr` | Voltage AC R | V | All |
| `sensor.dongle_XX_vacs` | Voltage AC S | V | GAAB, GAAA |
| `sensor.dongle_XX_vact` | Voltage AC T | V | GAAB, GAAA |
| `sensor.dongle_XX_vepsr` | Voltage EPS R | V | All |
| `sensor.dongle_XX_vepss` | Voltage EPS S | V | GAAA, GAAB, FAAA, FAAB, EAAA, EAAB, ccaa, ceaa |
| `sensor.dongle_XX_vepst` | Voltage EPS T | V | GAAA, GAAB, FAAA, FAAB, EAAA, EAAB, ccaa, ceaa |
| `sensor.dongle_XX_vbus1` | Voltage Bus 1 | V | All |
| `sensor.dongle_XX_vbus2` | Voltage Bus 2 | V | All |
| `sensor.dongle_XX_ipv1` | PV1 Current (calculated) | A | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa |
| `sensor.dongle_XX_ipv2` | PV2 Current (calculated) | A | AAAA, AAAB, FAAA, FAAB, EAAA, EAAB, ccaa |
| `sensor.dongle_XX_ipv3` | PV3 Current (calculated) | A | FAAB, FAAA, EAAA, EAAB |
| `sensor.dongle_XX_iinvrms` | Current Inverter RMS | A | All |
| `sensor.dongle_XX_fac` | Frequency AC | Hz | All |
| `sensor.dongle_XX_feps` | Frequency EPS | Hz | All |
| `sensor.dongle_XX_pf` | Power Factor | % | All |
| `sensor.dongle_XX_seps` | Apparent Power EPS | VA | All |

#### Battery Information
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_soc` | State of Charge | % | All |
| `sensor.dongle_XX_soh` | State of Health | % | All |
| `sensor.dongle_XX_BatCapacity` | Battery Capacity (Ah) | Ah | All |
| `sensor.dongle_XX_BatCurrent_BMS` | Battery Current | A | All |
| `sensor.dongle_XX_MaxChgCurr` | Battery Max Charge Current | A | All |
| `sensor.dongle_XX_MaxDischgCurr` | Battery Max Discharge Current | A | All |
| `sensor.dongle_XX_ChargeVoltRef` | Battery Charge Voltage Ref | V | All |
| `sensor.dongle_XX_DischgCutVolt` | Battery Discharge Voltage Ref | V | All |
| `sensor.dongle_XX_BatStatus0_BMS` | Battery BMS Status 0 | - | All |
| `sensor.dongle_XX_BatStatus5_BMS` | Battery BMS Status 5 | - | All |
| `sensor.dongle_XX_BatStatus_INV` | Battery Status Aggregrate Value | - | All |
| `sensor.dongle_XX_BatParallelNum` | Number Of Batteries (Parallel) | - | All |
| `sensor.dongle_XX_FaultCode_BMS` | Battery Fault Code | - | All |
| `sensor.dongle_XX_WarningCode_BMS` | Battery Warning Code | - | All |
| `sensor.dongle_XX_MaxCellVolt_BMS` | Max Cell Voltage | V | All |
| `sensor.dongle_XX_MinCellVolt_BMS` | Min Cell Voltage | V | All |
| `sensor.dongle_XX_MaxCellTemp_BMS` | Max Cell Temperature | °C | All |
| `sensor.dongle_XX_MinCellTemp_BMS` | Min Cell Temperature | °C | All |
| `sensor.dongle_XX_CycleCnt_BMS` | Battery Cycle Count | - | All |
| `sensor.dongle_XX_BatVoltSample_INV` | Inverter Battery Voltage Sample | V | All |

#### Temperature Sensors
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_tinner` | Internal Temperature | °C | All |
| `sensor.dongle_XX_tradiator1` | Radiator Temperature 1 | °C | All |
| `sensor.dongle_XX_tradiator2` | Radiator Temperature 2 | °C | E, F, G |
| `sensor.dongle_XX_tbat` | Battery Temperature | °C | All |
| `sensor.dongle_XX_MaxCellTemp_BMS` | Max Cell Temperature | °C | All |
| `sensor.dongle_XX_MinCellTemp_BMS` | Min Cell Temperature | °C | All |
| `sensor.dongle_XX_T1` | Radiator T1 | °C | FAAB, FAAA |
| `sensor.dongle_XX_T2` | Radiator T2 | °C | FAAB, FAAA |
| `sensor.dongle_XX_T3` | Radiator T3 | °C | FAAB, FAAA |
| `sensor.dongle_XX_T4` | Radiator T4 | °C | FAAB, FAAA |

#### Status Sensors
| Entity ID | Description | Values | Firmware Codes |
|-----------|-------------|--------|----------------|
| `sensor.dongle_XX_state` | State | Various states | All |
| `sensor.dongle_XX_statedescription` | Working Mode | Various modes | All |
| `sensor.dongle_XX_fault_status` | Fault Status | Text | All |
| `sensor.dongle_XX_warning_status` | Warning Status | Text | All |
| `sensor.dongle_XX_FaultCode` | Fault Code | Text | All |
| `sensor.dongle_XX_WarningCode` | Warning Code | Text | All |
| `sensor.dongle_XX_internalfault` | Internal Fault | - | All |
| `sensor.dongle_XX_uptime` | Uptime Sensor | seconds | All |
| `sensor.dongle_XX_RunningTime` | Running Time | seconds | All |
| `sensor.dongle_XX_MasterOrSlave` | Master or Slave Device | Text | All |
| `sensor.dongle_XX_FWCode` | FWCode | - | All |
| `sensor.dongle_XX_SlaveVer` | Slave Version | Text | All |
| `sensor.dongle_XX_ComVer` | Com Version | Text | All |
| `sensor.dongle_XX_CntlVer` | Control Version | Text | All |
| `sensor.dongle_XX_FWVer` | FW Version | Text | All |
| `sensor.dongle_XX_last_bank_update` | Last Bank Update | timestamp | All |

### Binary Sensors

| Entity ID | Description | States | Firmware Codes |
|-----------|-------------|--------|----------------|
| `binary_sensor.dongle_XX_battery_charge_status` | Battery Charge | on/off | All |
| `binary_sensor.dongle_XX_battery_discharge_status` | Battery Discharge | on/off | All |

### Switches

#### Basic Controls
| Entity ID | Description | Function | Firmware Codes |
|-----------|-------------|----------|----------------|
| `switch.dongle_XX_ResetSetting` | Restart Inverter | Restart inverter | All |
| `switch.dongle_XX_EPS` | EPS | Enable emergency power | All |
| `switch.dongle_XX_NeutralDetect` | Ground neutral detection enable | Enable neutral detection | All |
| `switch.dongle_XX_ACCharge` | AC Charge | Allow grid charging | All |
| `switch.dongle_XX_SWSeamlessly` | Seamless off-grid mode switching | Enable seamless switching | All |
| `switch.dongle_XX_SetToStandby` | Standby Switch | Set to standby mode | All |
| `switch.dongle_XX_ForcedDischg` | Force Discharge | Force battery discharge | All |
| `switch.dongle_XX_ForcedChg` | Charge Priority | Battery/Load priority | All |
| `switch.dongle_XX_FeedInGrid` | Export Allowed | Allow export to grid | All |

#### Advanced Controls
| Entity ID | Description | Function | Firmware Codes |
|-----------|-------------|----------|----------------|
| `switch.dongle_XX_ubPVGridOffEn` | PV Grid Off | Disable PV when grid off | All |
| `switch.dongle_XX_ubFastZeroExport` | Fast Zero Export | Enable fast zero export | All |
| `switch.dongle_XX_ubMicroGridEn` | Micro Grid On | Enable micro grid mode | All |
| `switch.dongle_XX_ubBatShared` | Battery Shared | Enable battery sharing | All |
| `switch.dongle_XX_ubChgLastEn` | Charge Last | Enable charge last mode | All |
| `switch.dongle_XX_TakeLoadTogether` | Take Load Together | Enable load sharing | All |
| `switch.dongle_XX_HalfHourACChrStartEn` | Half hour charge Switch | Enable half-hour charging | All |

### Number Entities

#### Power Settings
| Entity ID | Range | Description | Firmware Codes |
|-----------|-------|-------------|----------------|
| `number.dongle_XX_ActivePowerPercentCMD` | 0-100% | Active Power | All |
| `number.dongle_XX_ChargePowerPercentCMD` | 0-100% | Charge Power Rate | All |
| `number.dongle_XX_DischgPowerPercentCMD` | 0-100% | Discharge Power Rate | All |
| `number.dongle_XX_ACChgPowerCMD` | 0-100% | AC Charge Rate | All |
| `number.dongle_XX_ChgFirstPowerCMD` | 0-100% | Charge First Rate | All |
| `number.dongle_XX_ForcedDischgPowerCMD` | 0-100% | Force Discharge Power Rate | All |
| `number.dongle_XX_ForcedDischgSOCLimit` | 0-100% | Force Discharge SOC Limit | All |
| `number.dongle_XX_DischgCurr` | 0-140A | Discharge Current DC(A) | All |
| `number.dongle_XX_ChargeCurr` | 0-140A | Charge Current DC(A) | All |
| `number.dongle_XX_ChargeRate` | 0-140A | Lead acid Charge Rate (A) | All |
| `number.dongle_XX_DischgRate` | 0-140A | Lead Acid Discharge Rate (A) | All |
| `number.dongle_XX_PtoUserStartdischg` | 1-50W | Battery Discharge Start Point (W) | All |
| `number.dongle_XX_PtoUserStartchg` | -50-1W | Battery Charge Start Point (W) | All |
| `number.dongle_XX_wCT_PowerOffset` | 0-1000W | CT Offset (W) | All |
| `number.dongle_XX_MaxBackFlow` | 0-200W | Export Power (%) | All |

#### Battery Settings
| Entity ID | Range | Description | Firmware Codes |
|-----------|-------|-------------|----------------|
| `number.dongle_XX_ACChgSOCLimit` | 0-100% | AC Charge SOC Limit | All |
| `number.dongle_XX_ChgFirstSOCLimit` | 0-100% | Charge First SOC Limit | All |
| `number.dongle_XX_EOD` | 0-90% | On-grid Discharge Cut-off SOC Limit | All |
| `number.dongle_XX_SOCLowLimitForESPSDischg` | 0-90% | Off-grid Discharge Cut-off SOC Limit | All |
| `number.dongle_XX_ACChgStartSOC` | 0-100% | AC Charge Start (SOC) | All |
| `number.dongle_XX_ACChgEndSOC` | 0-100% | AC Charge End (SOC) | All |
| `number.dongle_XX_ACChgStartVolt` | 38.5-52V | AC Charge Start (Voltage) | All |
| `number.dongle_XX_ACChgEndVolt` | 48-59V | AC Charge End (Voltage) | All |
| `number.dongle_XX_BatStopChgSOC` | 0-101% | System Charge SOC Limit % | HAAA, FAAA, FAAB, ccaa, ceaa |
| `number.dongle_XX_BatStopChgVolt` | 40-56V | System Charge Volt limit (v) | HAAA, FAAA, FAAB, ccaa, ceaa |
| `number.dongle_XX_ForceDichgEndVolt` | 40-56V | Stop Discharge (Voltage) | All |

#### Grid Settings
| Entity ID | Range | Description | Firmware Codes |
|-----------|-------|-------------|----------------|
| `number.dongle_XX_MaxGridInputPower` | 0-24kW | Max Grid Input Power | All |
| `number.dongle_XX_GenRatePower` | 0-24kW | Generator Rated Input Power | HAAA, FAAA, FAAB, ccaa, ceaa |
| `number.dongle_XX_GenChgStartVolt` | 40-56V | Generator Charge Start Voltage | HAAA, FAAA, FAAB, ccaa, ceaa |
| `number.dongle_XX_GenChgEndVolt` | 50-60V | Generator Charge End Voltage | HAAA, FAAA, FAAB, ccaa, ceaa |
| `number.dongle_XX_GenChgStartSOC` | 0-100% | Generator Charge Start SOC | HAAA, FAAA, FAAB, ccaa, ceaa |
| `number.dongle_XX_GenChgEndSOC` | 0-100% | Generator Charge End SOC | HAAA, FAAA, FAAB, ccaa, ceaa |
| `number.dongle_XX_MaxGenChgBatCurr` | 0-140A | Max Generator Charge Battery Current | HAAA, FAAA, FAAB, ccaa, ceaa |
| `number.dongle_XX_GenChgStartCurr` | 0-140A | Generator Charge Start Current | HAAA, FAAA, FAAB, ccaa, ceaa |

### Time Entities

#### Charge Schedule
| Entity ID | Format | Description | Firmware Codes |
|-----------|--------|-------------|----------------|
| `time.dongle_XX_ACChgStart` | HH:MM | AC Charge Start | All |
| `time.dongle_XX_ACChgEnd` | HH:MM | AC Charge End | All |
| `time.dongle_XX_ACChgStart1` | HH:MM | AC Charge Start1 | All |
| `time.dongle_XX_ACChgEnd1` | HH:MM | AC Charge End1 | All |
| `time.dongle_XX_ACChgStart2` | HH:MM | AC Charge Start2 | All |
| `time.dongle_XX_ACChgEnd2` | HH:MM | AC Charge End2 | All |
| `time.dongle_XX_ChgFirstStart` | HH:MM | Charge Priority Start | All |
| `time.dongle_XX_ChgFirstEnd` | HH:MM | Charge Priority End | All |
| `time.dongle_XX_ChgFirstStart1` | HH:MM | Charge Priority Start1 | All |
| `time.dongle_XX_ChgFirstEnd1` | HH:MM | Charge Priority End1 | All |
| `time.dongle_XX_ChgFirstStart2` | HH:MM | Charge Priority Start2 | All |
| `time.dongle_XX_ChgFirstEnd2` | HH:MM | Charge Priority End2 | All |

#### Discharge Schedule
| Entity ID | Format | Description | Firmware Codes |
|-----------|--------|-------------|----------------|
| `time.dongle_XX_ForcedDischgStart` | HH:MM | Force Discharge Start | All |
| `time.dongle_XX_ForcedDischgEnd` | HH:MM | Force Discharge End | All |
| `time.dongle_XX_ForcedDischgStart1` | HH:MM | Force Discharge Start1 | All |
| `time.dongle_XX_ForcedDischgEnd1` | HH:MM | Force Discharge End1 | All |
| `time.dongle_XX_ForcedDischgStart2` | HH:MM | Force Discharge Start2 | All |
| `time.dongle_XX_ForcedDischgEnd2` | HH:MM | Force Discharge End2 | All |

### Select Entities

#### Time Period Selectors (48 30-minute slots)
| Entity ID | Description | Options | Firmware Codes |
|-----------|-------------|---------|----------------|
| `select.dongle_XX_Time0` | 00:00-00:30 | Does Not Operate, AC Charge, PV Charge, Discharge | All |
| `select.dongle_XX_Time1` | 00:30-01:00 | Does Not Operate, AC Charge, PV Charge, Discharge | All |
| ... | ... | ... | ... |
| `select.dongle_XX_Time47` | 23:30-00:00 | Does Not Operate, AC Charge, PV Charge, Discharge | All |

#### Control Selectors
| Entity ID | Description | Options | Firmware Codes |
|-----------|-------------|---------|----------------|
| `select.dongle_XX_CTSampleRatio` | CT Sample Ratio | 1:1000, 1:3000 | All |
| `select.dongle_XX_ClearParallelAlarm` | Clear Parallel Alarm | N/A, Clear | All |
| `select.dongle_XX_ACChargeType` | Charge Based on | Time According To, SOC/Volt According To | AAAA, AAAB, BAAA, BAAB |
| `select.dongle_XX_ACChargeType` | Charge Based on | Time According To, SOC/Volt According To, Time and SOC/Volt According To | ccaa, FAAB, FAAA, EAAA, EAAB, HAAA, ceaa |
| `select.dongle_XX_ubBatChgcontrol` | Charge Control | Voltage, SOC | All |
| `select.dongle_XX_ubBatDischgControl` | Discharge Control | Voltage, SOC | All |
| `select.dongle_XX_quickchgtime` | Quick Charge Duration | 0, 15, 30, 45, 60, 90, 120 | All |

### Button Entities

| Entity ID | Description | Action | Firmware Codes |
|-----------|-------------|--------|----------------|
| `button.dongle_XX_firmware_update_button` | Dongle Firmware Update | Updates dongle firmware | All |
| `button.dongle_XX_INVReboot` | Restart Inverter | Reboots the inverter | All |

### Update Entity

| Entity ID | Description | Features | Firmware Codes |
|-----------|-------------|----------|----------------|
| `update.dongle_XX_firmware_update` | Firmware Update | Progress tracking, release notes | IAAB, AAAA, AAAB, BAAA, BAAB, ccaa, FAAB, FAAA, EAAA, EAAB, HAAA, ceaa |

## GridBoss Entities (IAAB Firmware)

GridBoss adds 190+ entities for advanced distribution control. All GridBoss entities are only available with IAAB firmware.

### GridBoss Sensors

#### GridBoss Status & Monitoring
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_midboxStatus` | GridBoss Status | Text | IAAB |
| `sensor.dongle_XX_gridRMSVoltage` | Grid RMS Voltage | V | IAAB |
| `sensor.dongle_XX_buRMSVoltage` | BU RMS Voltage | V | IAAB |
| `sensor.dongle_XX_genRMSVoltage` | Gen RMS Voltage | V | IAAB |
| `sensor.dongle_XX_PhaseLockFreq` | Phase Lock Frequency | Hz | IAAB |
| `sensor.dongle_XX_GridFreq` | Grid Frequency | Hz | IAAB |
| `sensor.dongle_XX_GenFreq` | Gen Frequency | Hz | IAAB |
| `sensor.dongle_XX_SmartPortMode` | Smart Port Mode | Text | IAAB |

#### GridBoss Voltage Monitoring (Per Phase)
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_gridL1RMSVoltage` | Grid L1 RMS Voltage | V | IAAB |
| `sensor.dongle_XX_gridL2RMSVoltage` | Grid L2 RMS Voltage | V | IAAB |
| `sensor.dongle_XX_buL1RMSVoltage` | BU L1 RMS Voltage | V | IAAB |
| `sensor.dongle_XX_buL2RMSVoltage` | BU L2 RMS Voltage | V | IAAB |
| `sensor.dongle_XX_genL1RMSVoltage` | Gen L1 RMS Voltage | V | IAAB |
| `sensor.dongle_XX_genL2RMSVoltage` | Gen L2 RMS Voltage | V | IAAB |

#### GridBoss Current Monitoring (Per Phase)
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_gridL1RMSCurrent` | Grid L1 RMS Current | A | IAAB |
| `sensor.dongle_XX_gridL2RMSCurrent` | Grid L2 RMS Current | A | IAAB |
| `sensor.dongle_XX_loadL1RMSCurrent` | Load L1 RMS Current | A | IAAB |
| `sensor.dongle_XX_loadL2RMSCurrent` | Load L2 RMS Current | A | IAAB |
| `sensor.dongle_XX_genL1RMSCurrent` | Gen L1 RMS Current | A | IAAB |
| `sensor.dongle_XX_genL2RMSCurrent` | Gen L2 RMS Current | A | IAAB |
| `sensor.dongle_XX_buL1RMSCurrent` | BU L1 RMS Current | A | IAAB |
| `sensor.dongle_XX_buL2RMSCurrent` | BU L2 RMS Current | A | IAAB |

#### SmartLoad Current Monitoring
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_smartLoad1L1RMSCurrent` | SmartLoad1 L1 RMS Current | A | IAAB |
| `sensor.dongle_XX_smartLoad1L2RMSCurrent` | SmartLoad1 L2 RMS Current | A | IAAB |
| `sensor.dongle_XX_smartLoad2L1RMSCurrent` | SmartLoad2 L1 RMS Current | A | IAAB |
| `sensor.dongle_XX_smartLoad2L2RMSCurrent` | SmartLoad2 L2 RMS Current | A | IAAB |
| `sensor.dongle_XX_smartLoad3L1RMSCurrent` | SmartLoad3 L1 RMS Current | A | IAAB |
| `sensor.dongle_XX_smartLoad3L2RMSCurrent` | SmartLoad3 L2 RMS Current | A | IAAB |
| `sensor.dongle_XX_smartLoad4L1RMSCurrent` | SmartLoad4 L1 RMS Current | A | IAAB |
| `sensor.dongle_XX_smartLoad4L2RMSCurrent` | SmartLoad4 L2 RMS Current | A | IAAB |

#### GridBoss Power Monitoring (Per Phase)
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_gridL1ActivePower` | Grid L1 Active Power | W | IAAB |
| `sensor.dongle_XX_gridL2ActivePower` | Grid L2 Active Power | W | IAAB |
| `sensor.dongle_XX_loadL1ActivePower` | Load L1 Active Power | W | IAAB |
| `sensor.dongle_XX_loadL2ActivePower` | Load L2 Active Power | W | IAAB |
| `sensor.dongle_XX_genL1ActivePower` | Gen L1 Active Power | W | IAAB |
| `sensor.dongle_XX_genL2ActivePower` | Gen L2 Active Power | W | IAAB |
| `sensor.dongle_XX_buL1ActivePower` | BU L1 Active Power | W | IAAB |
| `sensor.dongle_XX_buL2ActivePower` | BU L2 Active Power | W | IAAB |

#### SmartLoad Power Monitoring
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_smartLoad1L1ActivePower` | SmartLoad1 L1 Active Power | W | IAAB |
| `sensor.dongle_XX_smartLoad1L2ActivePower` | SmartLoad1 L2 Active Power | W | IAAB |
| `sensor.dongle_XX_smartLoad2L1ActivePower` | SmartLoad2 L1 Active Power | W | IAAB |
| `sensor.dongle_XX_smartLoad2L2ActivePower` | SmartLoad2 L2 Active Power | W | IAAB |
| `sensor.dongle_XX_smartLoad3L1ActivePower` | SmartLoad3 L1 Active Power | W | IAAB |
| `sensor.dongle_XX_smartLoad3L2ActivePower` | SmartLoad3 L2 Active Power | W | IAAB |
| `sensor.dongle_XX_smartLoad4L1ActivePower` | SmartLoad4 L1 Active Power | W | IAAB |
| `sensor.dongle_XX_smartLoad4L2ActivePower` | SmartLoad4 L2 Active Power | W | IAAB |

#### GridBoss Energy Monitoring (Today)
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_eLoad_TodayAll` | E Load Today All | kWh | IAAB |
| `sensor.dongle_XX_EtoGrid_TodayAll` | E to Grid Today All | kWh | IAAB |
| `sensor.dongle_XX_EtoUser_TodayAll` | E to User Today All | kWh | IAAB |
| `sensor.dongle_XX_Egen_TodayAll` | E Gen Today All | kWh | IAAB |
| `sensor.dongle_XX_ESmartLoad1_TodayAll` | E SmartLoad1 Today All | kWh | IAAB |
| `sensor.dongle_XX_ESmartLoad2_TodayAll` | E SmartLoad2 Today All | kWh | IAAB |
| `sensor.dongle_XX_ESmartLoad3_TodayAll` | E SmartLoad3 Today All | kWh | IAAB |
| `sensor.dongle_XX_ESmartLoad4_TodayAll` | E SmartLoad4 Today All | kWh | IAAB |
| `sensor.dongle_XX_EAcouple1_TodayAll` | E ACcouple1 Today All | kWh | IAAB |
| `sensor.dongle_XX_EAcouple2_TodayAll` | E ACcouple2 Today All | kWh | IAAB |
| `sensor.dongle_XX_EAcouple3_TodayAll` | E ACcouple3 Today All | kWh | IAAB |
| `sensor.dongle_XX_EAcouple4_TodayAll` | E ACcouple4 Today All | kWh | IAAB |

#### GridBoss Energy Monitoring (Total)
| Entity ID | Description | Unit | Firmware Codes |
|-----------|-------------|------|----------------|
| `sensor.dongle_XX_ELoad_total` | E Load Total | kWh | IAAB |
| `sensor.dongle_XX_EBU_Total` | E BU Total | kWh | IAAB |
| `sensor.dongle_XX_EtoGrid_total` | E to Grid Total | kWh | IAAB |
| `sensor.dongle_XX_EtoUser_total` | E to User Total | kWh | IAAB |
| `sensor.dongle_XX_Egen_total` | E Gen Total | kWh | IAAB |
| `sensor.dongle_XX_ESmartLoad1_total` | E SmartLoad1 Total | kWh | IAAB |
| `sensor.dongle_XX_ESmartLoad2_total` | E SmartLoad2 Total | kWh | IAAB |
| `sensor.dongle_XX_ESmartLoad3_total` | E SmartLoad3 Total | kWh | IAAB |
| `sensor.dongle_XX_ESmartLoad4_total` | E SmartLoad4 Total | kWh | IAAB |
| `sensor.dongle_XX_EAcouple1_total` | E ACcouple1 Total | kWh | IAAB |
| `sensor.dongle_XX_EAcouple2_total` | E ACcouple2 Total | kWh | IAAB |
| `sensor.dongle_XX_EAcouple3_total` | E ACcouple3 Total | kWh | IAAB |
| `sensor.dongle_XX_EAcouple4_total` | E ACcouple4 Total | kWh | IAAB |
| `sensor.dongle_XX_MIDBoox_ACType` | MIDBox AC Type | - | IAAB |

### GridBoss Switches

#### Generator Control
| Entity ID | Description | Function | Firmware Codes |
|-----------|-------------|----------|----------------|
| `switch.dongle_XX_Generator_enable` | Generator Enable | Enable generator | IAAB |

#### SmartLoad Control
| Entity ID | Description | Function | Firmware Codes |
|-----------|-------------|----------|----------------|
| `switch.dongle_XX_SmartLoad1_Enable` | SmartLoad1 Enable | Enable SmartLoad1 | IAAB |
| `switch.dongle_XX_SmartLoad2_Enable` | SmartLoad2 Enable | Enable SmartLoad2 | IAAB |
| `switch.dongle_XX_SmartLoad3_Enable` | SmartLoad3 Enable | Enable SmartLoad3 | IAAB |
| `switch.dongle_XX_SmartLoad4_Enable` | SmartLoad4 Enable | Enable SmartLoad4 | IAAB |
| `switch.dongle_XX_SmartLoad1_GridOn` | SmartLoad1 Grid On | SmartLoad1 grid connection | IAAB |
| `switch.dongle_XX_SmartLoad2_GridOn` | SmartLoad2 Grid On | SmartLoad2 grid connection | IAAB |
| `switch.dongle_XX_SmartLoad3_GridOn` | SmartLoad3 Grid On | SmartLoad3 grid connection | IAAB |
| `switch.dongle_XX_SmartLoad4_GridOn` | SmartLoad4 Grid On | SmartLoad4 grid connection | IAAB |
| `switch.dongle_XX_SmartLoad1_Shedding` | SmartLoad1 Shedding | Enable SmartLoad1 shedding | IAAB |
| `switch.dongle_XX_SmartLoad2_Shedding` | SmartLoad2 Shedding | Enable SmartLoad2 shedding | IAAB |
| `switch.dongle_XX_SmartLoad3_Shedding` | SmartLoad3 Shedding | Enable SmartLoad3 shedding | IAAB |
| `switch.dongle_XX_SmartLoad4_Shedding` | SmartLoad4 Shedding | Enable SmartLoad4 shedding | IAAB |

#### AC Coupling Control
| Entity ID | Description | Function | Firmware Codes |
|-----------|-------------|----------|----------------|
| `switch.dongle_XX_ACcouple1_Enable` | ACcouple1 Enable | Enable AC coupling 1 | IAAB |
| `switch.dongle_XX_ACcouple2_Enable` | ACcouple2 Enable | Enable AC coupling 2 | IAAB |
| `switch.dongle_XX_ACcouple3_Enable` | ACcouple3 Enable | Enable AC coupling 3 | IAAB |
| `switch.dongle_XX_ACcouple4_Enable` | ACcouple4 Enable | Enable AC coupling 4 | IAAB |

### GridBoss Number Entities

#### Generator Settings
| Entity ID | Range | Description | Firmware Codes |
|-----------|-------|-------------|----------------|
| `number.dongle_XX_Generator_Warmup` | 0-600s | Generator Warmup Time | IAAB |
| `number.dongle_XX_Generator_CoolDown` | 0-600s | Generator Cool Down Time | IAAB |
| `number.dongle_XX_Generator_Exercise_Period` | 0-365d | Generator Exercise Period | IAAB |

#### SmartLoad SOC Settings
| Entity ID | Range | Description | Firmware Codes |
|-----------|-------|-------------|----------------|
| `number.dongle_XX_SmartLoad1_StartSOC` | 0-100% | SmartLoad1 Start SOC | IAAB |
| `number.dongle_XX_SmartLoad1_EndSOC` | 0-100% | SmartLoad1 End SOC | IAAB |
| `number.dongle_XX_SmartLoad2_StartSOC` | 0-100% | SmartLoad2 Start SOC | IAAB |
| `number.dongle_XX_SmartLoad2_EndSOC` | 0-100% | SmartLoad2 End SOC | IAAB |
| `number.dongle_XX_SmartLoad3_StartSOC` | 0-100% | SmartLoad3 Start SOC | IAAB |
| `number.dongle_XX_SmartLoad3_EndSOC` | 0-100% | SmartLoad3 End SOC | IAAB |
| `number.dongle_XX_SmartLoad4_StartSOC` | 0-100% | SmartLoad4 Start SOC | IAAB |
| `number.dongle_XX_SmartLoad4_EndSOC` | 0-100% | SmartLoad4 End SOC | IAAB |

#### SmartLoad Voltage Settings
| Entity ID | Range | Description | Firmware Codes |
|-----------|-------|-------------|----------------|
| `number.dongle_XX_SmartLoad1_StartVolt` | 40-60V | SmartLoad1 Start Voltage | IAAB |
| `number.dongle_XX_SmartLoad1_EndVolt` | 40-60V | SmartLoad1 End Voltage | IAAB |
| `number.dongle_XX_SmartLoad2_StartVolt` | 40-60V | SmartLoad2 Start Voltage | IAAB |
| `number.dongle_XX_SmartLoad2_EndVolt` | 40-60V | SmartLoad2 End Voltage | IAAB |
| `number.dongle_XX_SmartLoad3_StartVolt` | 40-60V | SmartLoad3 Start Voltage | IAAB |
| `number.dongle_XX_SmartLoad3_EndVolt` | 40-60V | SmartLoad3 End Voltage | IAAB |
| `number.dongle_XX_SmartLoad4_StartVolt` | 40-60V | SmartLoad4 Start Voltage | IAAB |
| `number.dongle_XX_SmartLoad4_EndVolt` | 40-60V | SmartLoad4 End Voltage | IAAB |

#### AC Coupling SOC Settings
| Entity ID | Range | Description | Firmware Codes |
|-----------|-------|-------------|----------------|
| `number.dongle_XX_ACcouple1_StartSOC` | 0-100% | ACcouple1 Start SOC | IAAB |
| `number.dongle_XX_ACcouple1_EndSOC` | 0-100% | ACcouple1 End SOC | IAAB |
| `number.dongle_XX_ACcouple2_StartSOC` | 0-100% | ACcouple2 Start SOC | IAAB |
| `number.dongle_XX_ACcouple2_EndSOC` | 0-100% | ACcouple2 End SOC | IAAB |
| `number.dongle_XX_ACcouple3_StartSOC` | 0-100% | ACcouple3 Start SOC | IAAB |
| `number.dongle_XX_ACcouple3_EndSOC` | 0-100% | ACcouple3 End SOC | IAAB |
| `number.dongle_XX_ACcouple4_StartSOC` | 0-100% | ACcouple4 Start SOC | IAAB |
| `number.dongle_XX_ACcouple4_EndSOC` | 0-100% | ACcouple4 End SOC | IAAB |

#### AC Coupling Voltage Settings
| Entity ID | Range | Description | Firmware Codes |
|-----------|-------|-------------|----------------|
| `number.dongle_XX_ACcouple1_StartVolt` | 40-60V | ACcouple1 Start Voltage | IAAB |
| `number.dongle_XX_ACcouple1_EndVolt` | 40-60V | ACcouple1 End Voltage | IAAB |
| `number.dongle_XX_ACcouple2_StartVolt` | 40-60V | ACcouple2 Start Voltage | IAAB |
| `number.dongle_XX_ACcouple2_EndVolt` | 40-60V | ACcouple2 End Voltage | IAAB |
| `number.dongle_XX_ACcouple3_StartVolt` | 40-60V | ACcouple3 Start Voltage | IAAB |
| `number.dongle_XX_ACcouple3_EndVolt` | 40-60V | ACcouple3 End Voltage | IAAB |
| `number.dongle_XX_ACcouple4_StartVolt` | 40-60V | ACcouple4 Start Voltage | IAAB |
| `number.dongle_XX_ACcouple4_EndVolt` | 40-60V | ACcouple4 End Voltage | IAAB |

#### Shedding Settings
| Entity ID | Range | Description | Firmware Codes |
|-----------|-------|-------------|----------------|
| `number.dongle_XX_SmartLoad1_SheddingStartPv_Power` | 0-10000W | SmartLoad1 Shedding Start PV Power | IAAB |
| `number.dongle_XX_SmartLoad2_SheddingStartPv_Power` | 0-10000W | SmartLoad2 Shedding Start PV Power | IAAB |
| `number.dongle_XX_SmartLoad3_SheddingStartPv_Power` | 0-10000W | SmartLoad3 Shedding Start PV Power | IAAB |
| `number.dongle_XX_SmartLoad4_SheddingStartPv_Power` | 0-10000W | SmartLoad4 Shedding Start PV Power | IAAB |
| `number.dongle_XX_SmartLoad1_SheddingStartSOC` | 0-100% | SmartLoad1 Shedding Start SOC | IAAB |
| `number.dongle_XX_SmartLoad1_SheddingEndSOC` | 0-100% | SmartLoad1 Shedding End SOC | IAAB |
| `number.dongle_XX_SmartLoad2_SheddingStartSOC` | 0-100% | SmartLoad2 Shedding Start SOC | IAAB |
| `number.dongle_XX_SmartLoad2_SheddingEndSOC` | 0-100% | SmartLoad2 Shedding End SOC | IAAB |
| `number.dongle_XX_SmartLoad3_SheddingStartSOC` | 0-100% | SmartLoad3 Shedding Start SOC | IAAB |
| `number.dongle_XX_SmartLoad3_SheddingEndSOC` | 0-100% | SmartLoad3 Shedding End SOC | IAAB |
| `number.dongle_XX_SmartLoad4_SheddingStartSOC` | 0-100% | SmartLoad4 Shedding Start SOC | IAAB |
| `number.dongle_XX_SmartLoad4_SheddingEndSOC` | 0-100% | SmartLoad4 Shedding End SOC | IAAB |
| `number.dongle_XX_SmartLoad1_SheddingStartVolt` | 40-60V | SmartLoad1 Shedding Start Voltage | IAAB |
| `number.dongle_XX_SmartLoad1_SheddingEndVolt` | 40-60V | SmartLoad1 Shedding End Voltage | IAAB |
| `number.dongle_XX_SmartLoad2_SheddingStartVolt` | 40-60V | SmartLoad2 Shedding Start Voltage | IAAB |
| `number.dongle_XX_SmartLoad2_SheddingEndVolt` | 40-60V | SmartLoad2 Shedding End Voltage | IAAB |
| `number.dongle_XX_SmartLoad3_SheddingStartVolt` | 40-60V | SmartLoad3 Shedding Start Voltage | IAAB |
| `number.dongle_XX_SmartLoad3_SheddingEndVolt` | 40-60V | SmartLoad3 Shedding End Voltage | IAAB |
| `number.dongle_XX_SmartLoad4_SheddingStartVolt` | 40-60V | SmartLoad4 Shedding Start Voltage | IAAB |
| `number.dongle_XX_SmartLoad4_SheddingEndVolt` | 40-60V | SmartLoad4 Shedding End Voltage | IAAB |
| `number.dongle_XX_Flash_5060hz` | 0-1 | Flash 50/60Hz | IAAB |
| `number.dongle_XX_NEC_120CurrLimit` | 0-200A | NEC 120 Current Limit | IAAB |

### GridBoss Select Entities

#### Port Mode Configuration
| Entity ID | Description | Options | Firmware Codes |
|-----------|-------------|---------|----------------|
| `select.dongle_XX_SmartLoad1_PortMode` | Smart Port 1 | Does Not Operate, Smart Load, Ac Coupled | IAAB |
| `select.dongle_XX_SmartLoad2_PortMode` | Smart Port 2 | Does Not Operate, Smart Load, Ac Coupled | IAAB |
| `select.dongle_XX_SmartLoad3_PortMode` | Smart Port 3 | Does Not Operate, Smart Load, Ac Coupled | IAAB |
| `select.dongle_XX_SmartLoad4_PortMode` | Smart Port 4 | Does Not Operate, Smart Load, Ac Coupled | IAAB |

#### SmartLoad Mode Configuration
| Entity ID | Description | Options | Firmware Codes |
|-----------|-------------|---------|----------------|
| `select.dongle_XX_SmartLoad1_SOC_Volt` | Smart Load 1 Mode | Time, SOC/Volt | IAAB |
| `select.dongle_XX_SmartLoad2_SOC_Volt` | Smart Load 2 Mode | Time, SOC/Volt | IAAB |
| `select.dongle_XX_SmartLoad3_SOC_Volt` | Smart Load 3 Mode | Time, SOC/Volt | IAAB |
| `select.dongle_XX_SmartLoad4_SOC_Volt` | Smart Load 4 Mode | Time, SOC/Volt | IAAB |

### GridBoss Time Entities

#### SmartLoad Time Scheduling
| Entity ID | Format | Description | Firmware Codes |
|-----------|--------|-------------|----------------|
| `time.dongle_XX_SmartLoad1Start0` | HH:MM | SmartLoad1 Start0 | IAAB |
| `time.dongle_XX_SmartLoad1End0` | HH:MM | SmartLoad1 End0 | IAAB |
| `time.dongle_XX_SmartLoad1Start1` | HH:MM | SmartLoad1 Start1 | IAAB |
| `time.dongle_XX_SmartLoad1End1` | HH:MM | SmartLoad1 End1 | IAAB |
| `time.dongle_XX_SmartLoad1Start2` | HH:MM | SmartLoad1 Start2 | IAAB |
| `time.dongle_XX_SmartLoad1End2` | HH:MM | SmartLoad1 End2 | IAAB |
| `time.dongle_XX_SmartLoad2Start0` | HH:MM | SmartLoad2 Start0 | IAAB |
| `time.dongle_XX_SmartLoad2End0` | HH:MM | SmartLoad2 End0 | IAAB |
| `time.dongle_XX_SmartLoad2Start1` | HH:MM | SmartLoad2 Start1 | IAAB |
| `time.dongle_XX_SmartLoad2End1` | HH:MM | SmartLoad2 End1 | IAAB |
| `time.dongle_XX_SmartLoad2Start2` | HH:MM | SmartLoad2 Start2 | IAAB |
| `time.dongle_XX_SmartLoad2End2` | HH:MM | SmartLoad2 End2 | IAAB |
| `time.dongle_XX_SmartLoad3Start0` | HH:MM | SmartLoad3 Start0 | IAAB |
| `time.dongle_XX_SmartLoad3End0` | HH:MM | SmartLoad3 End0 | IAAB |
| `time.dongle_XX_SmartLoad3Start1` | HH:MM | SmartLoad3 Start1 | IAAB |
| `time.dongle_XX_SmartLoad3End1` | HH:MM | SmartLoad3 End1 | IAAB |
| `time.dongle_XX_SmartLoad3Start2` | HH:MM | SmartLoad3 Start2 | IAAB |
| `time.dongle_XX_SmartLoad3End2` | HH:MM | SmartLoad3 End2 | IAAB |
| `time.dongle_XX_SmartLoad4Start0` | HH:MM | SmartLoad4 Start0 | IAAB |
| `time.dongle_XX_SmartLoad4End0` | HH:MM | SmartLoad4 End0 | IAAB |
| `time.dongle_XX_SmartLoad4Start1` | HH:MM | SmartLoad4 Start1 | IAAB |
| `time.dongle_XX_SmartLoad4End1` | HH:MM | SmartLoad4 End1 | IAAB |
| `time.dongle_XX_SmartLoad4Start2` | HH:MM | SmartLoad4 Start2 | IAAB |
| `time.dongle_XX_SmartLoad4End2` | HH:MM | SmartLoad4 End2 | IAAB |

#### AC Coupling Time Scheduling
| Entity ID | Format | Description | Firmware Codes |
|-----------|--------|-------------|----------------|
| `time.dongle_XX_ACcouple1Start0` | HH:MM | ACcouple1 Start0 | IAAB |
| `time.dongle_XX_ACcouple1End0` | HH:MM | ACcouple1 End0 | IAAB |
| `time.dongle_XX_ACcouple1Start1` | HH:MM | ACcouple1 Start1 | IAAB |
| `time.dongle_XX_ACcouple1End1` | HH:MM | ACcouple1 End1 | IAAB |
| `time.dongle_XX_ACcouple1Start2` | HH:MM | ACcouple1 Start2 | IAAB |
| `time.dongle_XX_ACcouple1End2` | HH:MM | ACcouple1 End2 | IAAB |
| `time.dongle_XX_ACcouple2Start0` | HH:MM | ACcouple2 Start0 | IAAB |
| `time.dongle_XX_ACcouple2End0` | HH:MM | ACcouple2 End0 | IAAB |
| `time.dongle_XX_ACcouple2Start1` | HH:MM | ACcouple2 Start1 | IAAB |
| `time.dongle_XX_ACcouple2End1` | HH:MM | ACcouple2 End1 | IAAB |
| `time.dongle_XX_ACcouple2Start2` | HH:MM | ACcouple2 Start2 | IAAB |
| `time.dongle_XX_ACcouple2End2` | HH:MM | ACcouple2 End2 | IAAB |
| `time.dongle_XX_ACcouple3Start0` | HH:MM | ACcouple3 Start0 | IAAB |
| `time.dongle_XX_ACcouple3End0` | HH:MM | ACcouple3 End0 | IAAB |
| `time.dongle_XX_ACcouple3Start1` | HH:MM | ACcouple3 Start1 | IAAB |
| `time.dongle_XX_ACcouple3End1` | HH:MM | ACcouple3 End1 | IAAB |
| `time.dongle_XX_ACcouple3Start2` | HH:MM | ACcouple3 Start2 | IAAB |
| `time.dongle_XX_ACcouple3End2` | HH:MM | ACcouple3 End2 | IAAB |
| `time.dongle_XX_ACcouple4Start0` | HH:MM | ACcouple4 Start0 | IAAB |
| `time.dongle_XX_ACcouple4End0` | HH:MM | ACcouple4 End0 | IAAB |
| `time.dongle_XX_ACcouple4Start1` | HH:MM | ACcouple4 Start1 | IAAB |
| `time.dongle_XX_ACcouple4End1` | HH:MM | ACcouple4 End1 | IAAB |
| `time.dongle_XX_ACcouple4Start2` | HH:MM | ACcouple4 Start2 | IAAB |
| `time.dongle_XX_ACcouple4End2` | HH:MM | ACcouple4 End2 | IAAB |

## Combined Entities (Multi-Inverter)

When multiple inverters are configured, combined entities are created automatically. These entities aggregate data from all configured dongles and provide unified control.

### Combined Sensors
All power and energy sensors have combined versions that sum values from all dongles:
- `sensor.combined_ppv1` - Total PV1 power
- `sensor.combined_ppv2` - Total PV2 power  
- `sensor.combined_ppv3` - Total PV3 power
- `sensor.combined_Pall` - Total PV power
- `sensor.combined_pcharge` - Total charge power
- `sensor.combined_pdischarge` - Total discharge power
- `sensor.combined_pload` - Total load power
- `sensor.combined_ptogrid` - Total grid power
- `sensor.combined_ptouser` - Total user power
- `sensor.combined_peps` - Total EPS power

### Combined Energy Sensors
- `sensor.combined_epv1_day` - Total PV1 energy today
- `sensor.combined_epv2_day` - Total PV2 energy today
- `sensor.combined_epv3_day` - Total PV3 energy today
- `sensor.combined_epv_all` - Total PV energy today
- `sensor.combined_echg_day` - Total charge energy today
- `sensor.combined_edischg_day` - Total discharge energy today
- `sensor.combined_etogrid_day` - Total grid energy today
- `sensor.combined_etouser_day` - Total user energy today

### Combined Controls
All switches and numbers have combined versions that control all inverters simultaneously:
- `switch.combined_EPS` - Control EPS on all inverters
- `switch.combined_ACCharge` - Control AC charging on all inverters
- `switch.combined_ForcedDischg` - Control forced discharge on all inverters
- `switch.combined_ForcedChg` - Control charge priority on all inverters
- `number.combined_ActivePowerPercentCMD` - Set active power on all inverters
- `number.combined_ChargePowerPercentCMD` - Set charge power on all inverters
- `number.combined_DischgPowerPercentCMD` - Set discharge power on all inverters
- `number.combined_ACChgPowerCMD` - Set AC charge power on all inverters

### GridBoss Combined Entities
For GridBoss systems, additional combined entities are created:
- `switch.combined_Generator_enable` - Control generator on all GridBoss units
- `switch.combined_SmartLoad1_Enable` - Control SmartLoad1 on all units
- `switch.combined_SmartLoad2_Enable` - Control SmartLoad2 on all units
- `switch.combined_SmartLoad3_Enable` - Control SmartLoad3 on all units
- `switch.combined_SmartLoad4_Enable` - Control SmartLoad4 on all units

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

Different firmware codes enable different entities. The integration uses a conditional entity system that automatically shows/hides entities based on your inverter's firmware code.

### Supported Firmware Codes

| Firmware Code | Model Type | Key Features |
|---------------|------------|--------------|
| **AAAA** | 3-6k Hybrid Standard | Basic hybrid functionality, 2 PV strings |
| **AAAB** | 3-6k Hybrid Parallel | Parallel inverter support, 2 PV strings |
| **BAAA** | AC Coupled Standard | AC coupling support, 1 PV string |
| **BAAB** | AC Coupled Parallel | AC coupling with parallel support |
| **ccaa** | 6-12k Standard | Higher power capacity, 2 PV strings |
| **ceaa** | Off Grid | Off-grid operation, 2 PV strings |
| **EAAA** | 8-10k Hybrid Standard | High power hybrid, 2 PV strings |
| **EAAB** | 8-10k Hybrid Parallel | High power parallel, 2 PV strings |
| **FAAA** | 12k Hybrid Standard | 12kW capacity, 3 PV strings |
| **FAAB** | 12k Hybrid Parallel | 12kW parallel, 3 PV strings |
| **HAAA** | Gen Models | Generator support, 2 PV strings |
| **IAAB** | GridBoss | Advanced distribution control, 190+ entities |

### Entity Availability by Firmware

#### PV String Support
- **1 String**: BAAA, BAAB
- **2 Strings**: AAAA, AAAB, ccaa, ceaa, EAAA, EAAB, HAAA
- **3 Strings**: FAAA, FAAB

#### Advanced Features
- **Generator Support**: HAAA, FAAA, FAAB, ccaa, ceaa
- **GridBoss Features**: IAAB only
- **3-Phase Support**: GAAB, GAAA (not in current const.py)
- **AC Coupling**: BAAA, BAAB, IAAB

### Conditional Entity System

The integration automatically manages entity availability based on your firmware code:

- **Available Entities**: Shown normally and fully functional
- **Unavailable Entities**: Grayed out and disabled in the UI
- **Dynamic Updates**: Entities appear/disappear when firmware is updated

This prevents configuration errors and provides clear visual feedback about which features are available for your specific inverter model.

## Calculated Sensors

The integration provides several calculated sensors for enhanced monitoring:

### Battery Time to Empty
| Entity ID | Description | Attributes |
|-----------|-------------|------------|
| `sensor.dongle_XX_battery_time_empty` | Battery Time to Empty | calculated_kwh_storage_total, calculated_kwh_left, time_battery_empty, human_readable_time_left |

### Power Flow Sensors
| Entity ID | Description | Attributes |
|-----------|-------------|------------|
| `sensor.dongle_XX_gridflow_live` | Grid Flow Live | ptouser, ptogrid |
| `sensor.dongle_XX_batteryflow_live` | Battery Flow Live | pdischarge, pcharge |

## Using Entities

### In Automations
```yaml
automation:
  - trigger:
      - platform: numeric_state
        entity_id: sensor.dongle_12_34_56_78_90_ab_soc
        below: 20
    action:
      - service: switch.turn_on
        entity_id: switch.dongle_12_34_56_78_90_ab_ACCharge
```

### In Scripts
```yaml
script:
  charge_to_80:
    sequence:
      - service: number.set_value
        target:
          entity_id: number.dongle_12_34_56_78_90_ab_ACChgSOCLimit
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
          {{ (states('sensor.dongle_12_34_56_78_90_ab_pcharge')|float / 1000)|round(2) }}
```

### GridBoss Automation Example
```yaml
automation:
  - trigger:
      - platform: numeric_state
        entity_id: sensor.dongle_12_34_56_78_90_ab_soc
        below: 30
    action:
      - service: switch.turn_on
        entity_id: switch.dongle_12_34_56_78_90_ab_Generator_enable
```

## Entity Best Practices

1. **Use state_class**: For energy tracking in statistics
2. **Monitor availability**: Check for unavailable states
3. **Handle units**: Convert W to kW for display
4. **Group related**: Create entity groups for organization
5. **Template carefully**: Add error handling to templates
6. **Firmware awareness**: Check firmware code before using advanced features
7. **GridBoss features**: Use conditional logic for GridBoss-specific entities
8. **Combined entities**: Use combined entities for multi-inverter setups