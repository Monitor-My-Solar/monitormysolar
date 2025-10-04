# Conditional Entity System for GridBoss SmartLoad Settings

## Overview

This document describes the implementation of a conditional entity system that dynamically enables/disables entity settings based on configuration dependencies:

### GridBoss Units
1. **SmartSOCVoltBits**: Controls SOC/Volt vs Time mode
2. **SmartLoad Bits**: Controls which SmartLoads are enabled

### Standard Units
1. **Charge Control**: Controls whether charge settings use Voltage or SOC mode
2. **Discharge Control**: Controls whether discharge settings use Voltage or SOC mode

This solves the challenge of having dependent settings where some values can only be set when other settings have specific values.

## Problem Statement

### GridBoss Systems
In GridBoss systems, certain settings have dependencies:

### SmartLoad Enable/Disable
- **Disabled SmartLoads**: When `SmartLoadX_Enable` is `false`, all related settings should be unavailable
- **Enabled SmartLoads**: When `SmartLoadX_Enable` is `true`, related settings become available

### SOC/Volt vs Time Mode
- **SOC/Volt Mode**: When `SmartLoadX_SOC_Volt` is `true`, only SOC and voltage-based settings are available
- **Time Mode**: When `SmartLoadX_SOC_Volt` is `false`, only time-based settings are available

### Always Available Settings
- **Enable/Disable Switches**: Always available regardless of other settings

### Standard Units
In standard inverter units, certain settings have dependencies:

### Charge Control Settings
- **Voltage Mode**: When `ubBatChgcontrol` is set to "Voltage", only voltage-based charge settings are available
- **SOC Mode**: When `ubBatChgcontrol` is set to "SOC", only SOC-based charge settings are available

### Discharge Control Settings
- **Voltage Mode**: When `ubBatDischgControl` is set to "Voltage", only voltage-based discharge settings are available
- **SOC Mode**: When `ubBatDischgControl` is set to "SOC", only SOC-based discharge settings are available

Home Assistant doesn't provide built-in popup alerts or dynamic entity enabling/disabling, so we needed a creative solution.

## Solution Architecture

### 1. Configuration Tracking

The coordinator now tracks configuration types for each dongle:

#### GridBoss Units
```python
self._smart_soc_volt_bits = {}  # Track SmartSOCVoltBits for each dongle
self._smartload_bits = {}  # Track SmartLoad Bits for each dongle
self._port_modes = {}  # Track Port Mode settings for each dongle
```

#### Standard Units
```python
self._charge_control_settings = {}  # Track ubBatChgcontrol for each dongle
self._discharge_control_settings = {}  # Track ubBatDischgControl for each dongle
self._charge_type_settings = {}  # Track ACChargeType for each dongle
```

### 2. Unified Entity Availability System

Entities use the `available` property to dynamically show/hide based on dependency settings. The system automatically detects whether it's a GridBoss or standard unit and applies the appropriate conditional logic:

```python
@property
def available(self) -> bool:
    """Return if entity is available."""
    if not self.coordinator.last_update_success:
        return False
    
    # Check if entity should be available based on conditional settings (GridBoss or standard units)
    return self.coordinator.is_entity_available(self._dongle_id, self._entity_type)
```

The `is_entity_available()` method automatically routes to the appropriate conditional logic:
- **GridBoss units**: Uses SmartLoad Port Mode → SOC/Volt mode → Enable state logic
- **Standard units**: Uses Charge/Discharge control settings logic

### 3. Immediate Updates and User Feedback

The system provides immediate feedback when control settings change:

#### GridBoss Units
When Port Mode or SOC/Volt settings change, the system:
1. Immediately updates the coordinator's internal state
2. Triggers availability updates for related entities
3. Logs what entities should become available/unavailable

#### Standard Units
When Charge/Discharge control settings change, the system:
1. Immediately updates the coordinator's internal state
2. Triggers availability updates for related entities
3. Logs the control mode change

#### User Experience
- **Visual Feedback**: Unavailable entities appear grayed out in Home Assistant
- **No Blocking**: Users can still interact with entities, but availability affects UI display
- **Dynamic Updates**: Entities become available/unavailable automatically when control settings change

## Implementation Details

### Coordinator Methods

#### Unified Availability Method
#### `is_entity_available(dongle_id, entity_unique_id)`
**Main method** that automatically routes to the appropriate conditional logic:
- **GridBoss units**: Routes to `is_entity_available_for_smartload_enable()`
- **Standard units**: Routes to `is_entity_available_for_standard_units()`

#### GridBoss Methods
#### `update_smart_soc_volt_bits(dongle_id, smart_soc_volt_bits)`
Updates the SmartSOCVoltBits settings and triggers entity availability updates.

#### `update_smartload_bits(dongle_id, smartload_bits)`
Updates the SmartLoad Bits settings and triggers entity availability updates.

#### `update_port_modes(dongle_id, port_modes)`
Updates the Port Mode settings and triggers entity availability updates.

#### `is_entity_available_for_smartload_enable(dongle_id, entity_unique_id)`
Determines GridBoss entity availability based on hierarchical logic:
- Port Mode → SOC/Volt mode → Enable state

#### Standard Unit Methods
#### `update_charge_control_setting(dongle_id, charge_control)`
Updates the charge control setting ("Voltage" or "SOC") and triggers entity availability updates.

#### `update_discharge_control_setting(dongle_id, discharge_control)`
Updates the discharge control setting ("Voltage" or "SOC") and triggers entity availability updates.

#### `update_charge_type_setting(dongle_id, charge_type)`
Updates the charge type setting ("Time According To", "SOC/Volt According To", or "Time and SOC/Volt According To") and triggers entity availability updates.

#### `is_entity_available_for_standard_units(dongle_id, entity_unique_id)`
Determines standard unit entity availability based on:
- Charge control setting (Voltage vs SOC)
- Charge type setting (Time vs SOC/Volt vs Time and SOC/Volt)
- Discharge control setting (Voltage vs SOC)
- Entity type (charge voltage, charge SOC, charge time, discharge voltage, discharge SOC)

#### Common Methods
#### `_trigger_entity_availability_update(dongle_id)`
Triggers async updates to entity availability when any control settings change.

### Entity Classification

The system classifies entities into categories:

**SOC/Volt Entities** (available when `SmartLoadX_SOC_Volt` is `true`):
- `StartSOC`, `EndSOC`
- `StartVolt`, `EndVolt`
- `SheddingStartSOC`, `SheddingEndSOC`
- `SheddingStartVolt`, `SheddingEndVolt`

**Time Entities** (available when `SmartLoadX_SOC_Volt` is `false`):
- `Start0`, `End0`
- `Start1`, `End1`
- `Start2`, `End2`

### Standard Unit Entity Classification

**Charge Voltage Entities** (available when `ubBatChgcontrol` is "Voltage" AND `ACChargeType` is "SOC/Volt According To" or "Time and SOC/Volt According To"):
- `ACChgStartVolt`, `ACChgEndVolt`

**Charge SOC Entities** (available when `ubBatChgcontrol` is "SOC" AND `ACChargeType` is "SOC/Volt According To" or "Time and SOC/Volt According To"):
- `ACChgStartSOC`, `ACChgEndSOC`

**Charge Time Entities** (available when `ACChargeType` is "Time According To"):
- `Time0` through `Time47`, `ACChgStart`, `ACChgEnd`, `ACChgStart1`, `ACChgEnd1`, `ACChgStart2`, `ACChgEnd2`

**Discharge Voltage Entities** (available when `ubBatDischgControl` is "Voltage"):
- `ForceDichgEndVolt`

**Discharge SOC Entities** (available when `ubBatDischgControl` is "SOC"):
- `ForcedDischgSOCLimit`

### User Experience

1. **Always Visible**: Entities remain visible in Home Assistant at all times
2. **Helpful Error Messages**: When users try to interact with conditionally unavailable entities, they see clear error messages explaining why the entity is unavailable
3. **Dynamic Updates**: Error messages update automatically when control settings change
4. **Immediate Response**: Changes to control settings trigger instant availability updates
5. **Unified System**: Same conditional logic works for both GridBoss and standard units
6. **HomeAssistantError Pattern**: Uses Home Assistant's recommended pattern for conditional entities

## Example Usage

### Complete SmartLoad Configuration

```json
"SmartLoad": {
  "Bits": {
    "SmartLoad1_Enable": true,
    "SmartLoad2_Enable": true,
    "SmartLoad3_Enable": false,
    "SmartLoad4_Enable": false
  }
},
"SmartSOCVoltBits": {
  "SmartLoad1_SOC_Volt": true,
  "SmartLoad2_SOC_Volt": false,
  "SmartLoad3_SOC_Volt": true,
  "SmartLoad4_SOC_Volt": false
}
```

**Result**:
- **SmartLoad1**: ✅ Enabled + SOC/Volt mode → SOC/Volt entities available, Time entities unavailable
- **SmartLoad2**: ✅ Enabled + Time mode → Time entities available, SOC/Volt entities unavailable  
- **SmartLoad3**: ❌ Disabled → All entities unavailable (except Enable switch)
- **SmartLoad4**: ❌ Disabled → All entities unavailable (except Enable switch)

### User Interaction Examples

#### Example 1: Disabled SmartLoad
1. User tries to set `SmartLoad3StartSOC` when `SmartLoad3_Enable` is `false`
2. System shows HomeAssistantError: "Smart Port 3 is set to 'Does Not Operate'"
3. Entity remains visible and functional, but shows clear error message when used

#### Example 2: Wrong Mode
1. User tries to set `SmartLoad1Start0` (time entity) when `SmartLoad1_SOC_Volt` is `true`
2. System shows HomeAssistantError: "Smart Port 1 is in SOC/Volt mode - Time settings not available"
3. Entity remains visible and functional, but shows clear error message when used

#### Example 3: Always Available
1. User can always access `SmartLoad1_Enable` switch regardless of other settings
2. This allows users to enable/disable SmartLoads as needed

### Standard Unit Configuration Examples

#### Example 1: Charge Control - Voltage Mode with SOC/Volt According To
1. User sets `ubBatChgcontrol` to "Voltage" AND `ACChargeType` to "SOC/Volt According To"
2. **Working entities**: `ACChgStartVolt`, `ACChgEndVolt` (can be used normally)
3. **Error entities**: `ACChgStartSOC`, `ACChgEndSOC`, all Time entities (show error messages when used)

#### Example 2: Charge Control - SOC Mode with SOC/Volt According To
1. User sets `ubBatChgcontrol` to "SOC" AND `ACChargeType` to "SOC/Volt According To"
2. **Working entities**: `ACChgStartSOC`, `ACChgEndSOC` (can be used normally)
3. **Error entities**: `ACChgStartVolt`, `ACChgEndVolt`, all Time entities (show error messages when used)

#### Example 3: Charge Control - Time According To
1. User sets `ACChargeType` to "Time According To"
2. **Working entities**: All Time entities (`Time0` through `Time47`, `ACChgStart`, `ACChgEnd`, etc.) (can be used normally)
3. **Error entities**: `ACChgStartVolt`, `ACChgEndVolt`, `ACChgStartSOC`, `ACChgEndSOC` (show error messages when used)

#### Example 4: Charge Control - Time and SOC/Volt According To
1. User sets `ACChargeType` to "Time and SOC/Volt According To"
2. **Working entities**: All Time entities + SOC/Volt entities (based on `ubBatChgcontrol` setting) (can be used normally)
3. **Error entities**: None (all charge entities work normally)

#### Example 5: Discharge Control - Voltage Mode
1. User sets `ubBatDischgControl` to "Voltage"
2. **Working entities**: `ForceDichgEndVolt` (can be used normally)
3. **Error entities**: `ForcedDischgSOCLimit` (shows error message when used)

#### Example 6: Discharge Control - SOC Mode
1. User sets `ubBatDischgControl` to "SOC"
2. **Working entities**: `ForcedDischgSOCLimit` (can be used normally)
3. **Error entities**: `ForceDichgEndVolt` (shows error message when used)

## Benefits

1. **Prevents Invalid Configurations**: Users cannot set conflicting settings
2. **Clear Error Messages**: Users see helpful error messages explaining why entities are unavailable
3. **Always Visible**: Entities remain visible at all times, making the interface more predictable
4. **Dynamic Behavior**: Error messages automatically update when dependencies change
5. **Immediate Response**: Changes to control settings trigger instant availability updates
6. **Unified System**: Same conditional logic works for both GridBoss and standard units
7. **No Breaking Changes**: Existing functionality remains intact
8. **Extensible**: System can be extended for other conditional settings
9. **Automatic Detection**: System automatically detects unit type and applies appropriate logic
10. **Home Assistant Best Practice**: Uses the recommended HomeAssistantError pattern

## Technical Notes

- The system uses Home Assistant's recommended `HomeAssistantError` pattern
- Entities remain available at all times but show error messages when used inappropriately
- Entity availability updates are triggered asynchronously
- The system gracefully handles missing or incomplete configuration data
- All changes are backward compatible
- **Unified Architecture**: Single `is_entity_available()` method handles both GridBoss and standard units
- **Automatic Routing**: System automatically detects unit type and applies appropriate conditional logic
- **Immediate Updates**: Control setting changes trigger instant availability updates via MQTT processing
- **Extensible Design**: Easy to add new conditional logic for additional settings
- **Error Message System**: Detailed error messages explain exactly why entities are unavailable

## Future Enhancements

1. **Additional Dependencies**: Extend to other conditional settings (more charge/discharge settings, time-based controls, etc.)
2. **Bulk Operations**: Handle multiple entity updates more efficiently
3. **Configuration UI**: Add visual indicators in the configuration flow
4. **Automation Support**: Allow automations to be aware of entity availability
5. **Advanced Charge Settings**: Add conditional logic for additional charge-related settings
6. **Time-based Conditionals**: Add conditional logic for time-based settings
7. **Cross-Unit Dependencies**: Add conditional logic that spans multiple units






## Charging conditionals:
- Charge Settings when entity ```{"name": "Charge Control", "type": "select", "unique_id": "ubBatChgcontrol", "options": ["Voltage", "SOC"]},``` is set to VOLT && ```{"name": "Charge Based on:", "type": "select", "unique_id": "ACChargeType", "options": ["Time According To", "SOC/Volt According To"] "allowed_firmware_codes": ["AAAA", "AAAB", "BAAA", "BAAB"]},{"name": "Charge Based on:", "type": "select", "unique_id": "ACChargeType", "options": ["Time According To", "SOC/Volt According To", "Time and SOC/Volt According To"] "allowed_firmware_codes": ["ccaa","FAAB","FAAA","EAAA", "EAAB","HAAA","ceaa"]},``` is set to SOC/VOLT or Time and SOC/Volt According to
  - ```{"name": "AC Charge Start (Voltage)", "type": "number", "unique_id": "ACChgStartVolt", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"},{"name": "AC Charge End (Voltage)", "type": "number", "unique_id": "ACChgEndVolt", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"},```
- Charge Settings When Entity ```{"name": "Charge Control", "type": "select", "unique_id": "ubBatChgcontrol", "options": ["Voltage", "SOC"]},``` is set to SOC
 - ```{"name": "AC Charge Start (SOC)", "type": "number", "unique_id": "ACChgStartSOC", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"}, {"name": "AC Charge End (SOC)", "type": "number", "unique_id": "ACChgEndSOC", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"},```&& ```{"name": "Charge Based on:", "type": "select", "unique_id": "ACChargeType", "options": ["Time According To", "SOC/Volt According To"] "allowed_firmware_codes": ["AAAA", "AAAB", "BAAA", "BAAB"]},{"name": "Charge Based on:", "type": "select", "unique_id": "ACChargeType", "options": ["Time According To", "SOC/Volt According To", "Time and SOC/Volt According To"] "allowed_firmware_codes": ["ccaa","FAAB","FAAA","EAAA", "EAAB","HAAA","ceaa"]},``` is set to SOC/VOLT or Time and SOC/Volt According to
### Charge Based on Entities
- Charge Based on  ```{"name": "Charge Based on:", "type": "select", "unique_id": "ACChargeType", "options": ["Time According To", "SOC/Volt According To"] "allowed_firmware_codes": ["AAAA", "AAAB", "BAAA", "BAAB"]},{"name": "Charge Based on:", "type": "select", "unique_id": "ACChargeType", "options": ["Time According To", "SOC/Volt According To", "Time and SOC/Volt According To"] "allowed_firmware_codes": ["ccaa","FAAB","FAAA","EAAA", "EAAB","HAAA","ceaa"]},``` is set to Time according too The above SOC and Voltage based entities should be greyed out and unavailable
  - ```
    {"name": "00:00 -- 00:30", "type": "select", "unique_id": "Time0", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "00:30 -- 01:00", "type": "select", "unique_id": "Time1", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "01:00 -- 01:30", "type": "select", "unique_id": "Time2", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "01:30 -- 02:00", "type": "select", "unique_id": "Time3", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "02:00 -- 02:30", "type": "select", "unique_id": "Time4", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "02:30 -- 03:00", "type": "select", "unique_id": "Time5", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "03:00 -- 03:30", "type": "select", "unique_id": "Time6", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "03:30 -- 04:00", "type": "select", "unique_id": "Time7", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "04:00 -- 04:30", "type": "select", "unique_id": "Time8", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "04:30 -- 05:00", "type": "select", "unique_id": "Time9", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "05:00 -- 05:30", "type": "select", "unique_id": "Time10", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "05:30 -- 06:00", "type": "select", "unique_id": "Time11", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "06:00 -- 06:30", "type": "select", "unique_id": "Time12", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "06:30 -- 07:00", "type": "select", "unique_id": "Time13", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "07:00 -- 07:30", "type": "select", "unique_id": "Time14", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "07:30 -- 08:00", "type": "select", "unique_id": "Time15", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "08:00 -- 08:30", "type": "select", "unique_id": "Time16", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "08:30 -- 09:00", "type": "select", "unique_id": "Time17", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "09:00 -- 09:30", "type": "select", "unique_id": "Time18", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "09:30 -- 10:00", "type": "select", "unique_id": "Time19", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "10:00 -- 10:30", "type": "select", "unique_id": "Time20", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "10:30 -- 11:00", "type": "select", "unique_id": "Time21", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "11:00 -- 11:30", "type": "select", "unique_id": "Time22", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "11:30 -- 12:00", "type": "select", "unique_id": "Time23", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "12:00 -- 12:30", "type": "select", "unique_id": "Time24", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "12:30 -- 13:00", "type": "select", "unique_id": "Time25", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "13:00 -- 13:30", "type": "select", "unique_id": "Time26", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "13:30 -- 14:00", "type": "select", "unique_id": "Time27", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "14:00 -- 14:30", "type": "select", "unique_id": "Time28", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "14:30 -- 15:00", "type": "select", "unique_id": "Time29", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "15:00 -- 15:30", "type": "select", "unique_id": "Time30", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "15:30 -- 16:00", "type": "select", "unique_id": "Time31", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "16:00 -- 16:30", "type": "select", "unique_id": "Time32", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "16:30 -- 17:00", "type": "select", "unique_id": "Time33", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "17:00 -- 17:30", "type": "select", "unique_id": "Time34", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "17:30 -- 18:00", "type": "select", "unique_id": "Time35", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "18:00 -- 18:30", "type": "select", "unique_id": "Time36", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "18:30 -- 19:00", "type": "select", "unique_id": "Time37", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "19:00 -- 19:30", "type": "select", "unique_id": "Time38", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "19:30 -- 20:00", "type": "select", "unique_id": "Time39", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "20:00 -- 20:30", "type": "select", "unique_id": "Time40", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "20:30 -- 21:00", "type": "select", "unique_id": "Time41", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "21:00 -- 21:30", "type": "select", "unique_id": "Time42", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "21:30 -- 22:00", "type": "select", "unique_id": "Time43", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "22:00 -- 22:30", "type": "select", "unique_id": "Time44", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "22:30 -- 23:00", "type": "select", "unique_id": "Time45", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "23:00 -- 23:30", "type": "select", "unique_id": "Time46", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    {"name": "23:30 -- 24:00", "type": "select", "unique_id": "Time47", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
    
    {"name": "AC Charge Start", "type": "time", "unique_id": "ACChgStart"},
    {"name": "AC Charge End", "type": "time", "unique_id": "ACChgEnd"},
    {"name": "AC Charge Start1", "type": "time", "unique_id": "ACChgStart1"},
    {"name": "AC Charge End1", "type": "time", "unique_id": "ACChgEnd1"},
    {"name": "AC Charge Start2", "type": "time", "unique_id": "ACChgStart2"},
    {"name": "AC Charge End2", "type": "time", "unique_id": "ACChgEnd2"}, 
    ```
    

## Discharging Conditionals
 - Discharge Settings when Entity ``` {"name": "Discharge Control", "type": "select", "unique_id": "ubBatDischgControl", "options": ["Voltage", "SOC"]},``` is set to VOLT
  - ```{"name": "Stop Dischage (Voltage)", "type": "number", "unique_id": "ForceDichgEndVolt", "unit": "V", "min": 40, "max": 56, "mode": "slider"},```
- Discharge Settings when Entity ``` {"name": "Discharge Control", "type": "select", "unique_id": "ubBatDischgControl", "options": ["Voltage", "SOC"]},``` is set to SOC
  - ```{"name": "Force Discharge SOC Limit", "type": "number", "unique_id": "ForcedDischgSOCLimit", "unit": "PERCENT", "min": 0, "max": 100 , "mode": "slider"},```

