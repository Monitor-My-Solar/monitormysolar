# Conditional Entity System

## Overview

The Monitor My Solar integration features an advanced conditional entity system that dynamically enables and disables entity settings based on configuration dependencies. This system ensures users can only configure settings that are valid for their current inverter configuration, preventing invalid configurations and providing clear visual feedback.

## How It Works

The conditional entity system automatically detects your inverter type and applies the appropriate logic:

### GridBoss Units
- **SmartLoad Enable/Disable**: Controls which SmartLoads are active
- **SOC/Volt vs Time Mode**: Determines whether SmartLoads use SOC/Voltage or time-based settings

### Standard Units  
- **Charge Control**: Controls whether charge settings use Voltage or SOC mode
- **Discharge Control**: Controls whether discharge settings use Voltage or SOC mode

## Visual Feedback

When entities are unavailable due to configuration dependencies:
- **Always Visible**: Entities remain visible in Home Assistant at all times
- **Helpful Error Messages**: When you try to interact with conditionally unavailable entities, you see clear error messages explaining why the entity is unavailable
- **Dynamic Updates**: Error messages automatically update when you change control settings
- **HomeAssistantError Pattern**: Uses Home Assistant's recommended pattern for conditional entities

## GridBoss SmartLoad Configuration

### SmartLoad Enable/Disable
When a SmartLoad is disabled, all related settings show error messages when used except the enable/disable switch itself.

**Example**: If `SmartLoad3_Enable` is `false`:
- ❌ All SmartLoad3 settings show error messages when used: "Smart Port 3 is set to 'Does Not Operate'"
- ✅ Only the `SmartLoad3_Enable` switch works normally

### SOC/Volt vs Time Mode
Each SmartLoad can operate in two modes:

#### SOC/Volt Mode (`SmartLoadX_SOC_Volt` = `true`)
**Working Settings** (can be used normally):
- `StartSOC`, `EndSOC` - SOC-based start/end points
- `StartVolt`, `EndVolt` - Voltage-based start/end points  
- `SheddingStartSOC`, `SheddingEndSOC` - SOC-based shedding
- `SheddingStartVolt`, `SheddingEndVolt` - Voltage-based shedding

**Error Settings** (show error messages when used):
- All time-based settings (`Start0`, `End0`, `Start1`, `End1`, etc.) - Error: "Smart Port X is in SOC/Volt mode - Time settings not available"

#### Time Mode (`SmartLoadX_SOC_Volt` = `false`)
**Working Settings** (can be used normally):
- `Start0`, `End0` - First time period
- `Start1`, `End1` - Second time period
- `Start2`, `End2` - Third time period

**Error Settings** (show error messages when used):
- All SOC/Voltage-based settings - Error: "Smart Port X is in Time mode - SOC/Volt settings not available"

### Complete SmartLoad Example

```json
{
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
}
```

**Result**:
- **SmartLoad1**: ✅ Enabled + SOC/Volt mode → SOC/Volt entities work normally, Time entities show error messages
- **SmartLoad2**: ✅ Enabled + Time mode → Time entities work normally, SOC/Volt entities show error messages  
- **SmartLoad3**: ❌ Disabled → All entities show error messages (except Enable switch)
- **SmartLoad4**: ❌ Disabled → All entities show error messages (except Enable switch)

## Standard Unit Configuration

### Charge Control Settings

The charge control system has two main settings that determine which entities are available:

#### Charge Control (`ubBatChgcontrol`)
- **"Voltage"**: Enables voltage-based charge settings
- **"SOC"**: Enables SOC-based charge settings

#### Charge Based On (`ACChargeType`)
- **"Time According To"**: Enables time-based charge settings
- **"SOC/Volt According To"**: Enables SOC/Voltage-based charge settings
- **"Time and SOC/Volt According To"**: Enables both time and SOC/Voltage-based settings

### Charge Entity Availability

#### Voltage Mode + SOC/Volt According To
**Working** (can be used normally):
- `ACChgStartVolt` - AC Charge Start (Voltage)
- `ACChgEndVolt` - AC Charge End (Voltage)

**Error** (show error messages when used):
- All SOC-based charge settings - Error: "Charge control is set to 'Voltage' - SOC settings not available"
- All time-based charge settings - Error: "Charge type is set to 'SOC/Volt According To' - Time settings not available"

#### SOC Mode + SOC/Volt According To  
**Working** (can be used normally):
- `ACChgStartSOC` - AC Charge Start (SOC)
- `ACChgEndSOC` - AC Charge End (SOC)

**Error** (show error messages when used):
- All voltage-based charge settings - Error: "Charge control is set to 'SOC' - Voltage settings not available"
- All time-based charge settings - Error: "Charge type is set to 'SOC/Volt According To' - Time settings not available"

#### Time According To
**Working** (can be used normally):
- All time-based settings (`Time0` through `Time47`)
- Time period settings (`ACChgStart`, `ACChgEnd`, etc.)

**Error** (show error messages when used):
- All SOC/Voltage-based charge settings - Error: "Charge type is set to 'Time According To' - SOC/Volt settings not available"

#### Time and SOC/Volt According To
**Working** (can be used normally):
- All time-based settings
- SOC/Voltage-based settings (based on `ubBatChgcontrol` setting)

**Error** (show error messages when used):
- None (all charge entities work normally)

### Discharge Control Settings

#### Discharge Control (`ubBatDischgControl`)
- **"Voltage"**: Enables voltage-based discharge settings
- **"SOC"**: Enables SOC-based discharge settings

### Discharge Entity Availability

#### Voltage Mode
**Working** (can be used normally):
- `ForceDichgEndVolt` - Stop Discharge (Voltage)

**Error** (shows error message when used):
- `ForcedDischgSOCLimit` - Force Discharge SOC Limit - Error: "Discharge control is set to 'Voltage' - SOC settings not available"

#### SOC Mode
**Working** (can be used normally):
- `ForcedDischgSOCLimit` - Force Discharge SOC Limit

**Error** (shows error message when used):
- `ForceDichgEndVolt` - Stop Discharge (Voltage) - Error: "Discharge control is set to 'SOC' - Voltage settings not available"

## User Experience Examples

### Example 1: Changing SmartLoad Mode
1. You have `SmartLoad1` enabled in SOC/Volt mode
2. You change `SmartLoad1_SOC_Volt` to `false` (Time mode)
3. **Immediately**: SOC/Volt entities show error messages when used: "Smart Port 1 is in Time mode - SOC/Volt settings not available"
4. **Immediately**: Time entities work normally
5. No restart or refresh needed

### Example 2: Disabling a SmartLoad
1. You have `SmartLoad2` configured with various settings
2. You set `SmartLoad2_Enable` to `false`
3. **Immediately**: All SmartLoad2 settings show error messages when used: "Smart Port 2 is set to 'Does Not Operate'"
4. **Immediately**: Only the `SmartLoad2_Enable` switch works normally

### Example 3: Standard Unit Charge Control
1. You set `ubBatChgcontrol` to "Voltage"
2. You set `ACChargeType` to "SOC/Volt According To"
3. **Working**: `ACChgStartVolt`, `ACChgEndVolt` (can be used normally)
4. **Error**: All SOC and time-based charge settings show error messages when used

## Benefits

1. **Prevents Invalid Configurations**: You cannot set conflicting settings
2. **Clear Error Messages**: You see helpful error messages explaining why entities are unavailable
3. **Always Visible**: Entities remain visible at all times, making the interface more predictable
4. **Dynamic Behavior**: Error messages automatically update when dependencies change
5. **Immediate Response**: Changes to control settings trigger instant availability updates
6. **Unified System**: Same conditional logic works for both GridBoss and standard units
7. **No Breaking Changes**: Existing functionality remains intact
8. **Automatic Detection**: System automatically detects unit type and applies appropriate logic
9. **Home Assistant Best Practice**: Uses the recommended HomeAssistantError pattern

## Technical Details

- The system uses Home Assistant's recommended `HomeAssistantError` pattern
- Entities remain available at all times but show error messages when used inappropriately
- Entity availability updates are triggered asynchronously
- The system gracefully handles missing or incomplete configuration data
- All changes are backward compatible
- Control setting changes trigger instant availability updates via MQTT processing
- Detailed error messages explain exactly why entities are unavailable

## Troubleshooting

### Entities Not Updating
If entities don't update when you change control settings:
1. Check that your dongle is connected and communicating
2. Verify the control setting change was successful
3. Wait a few seconds for the update to propagate
4. Check the Home Assistant logs for any error messages

### All Entities Showing Error Messages
If all entities show error messages when used:
1. Check your dongle connection status
2. Verify the inverter is responding to MQTT messages
3. Check that the coordinator is receiving updates successfully

### Wrong Error Messages
If entities show the wrong error messages for your configuration:
1. Verify your control settings are set correctly
2. Check that your inverter type is detected properly
3. Review the entity classification in the logs

## Future Enhancements

The conditional entity system is designed to be extensible. Future enhancements may include:
- Additional conditional settings for more complex configurations
- Visual indicators in the configuration flow
- Automation support for entity availability
- Cross-unit dependencies for multi-inverter setups
