# Conditional Entity System for GridBoss SmartLoad Settings

## Overview

This document describes the implementation of a conditional entity system that dynamically enables/disables GridBoss SmartLoad settings based on two key configurations:
1. **SmartSOCVoltBits**: Controls SOC/Volt vs Time mode
2. **SmartLoad Bits**: Controls which SmartLoads are enabled

This solves the challenge of having dependent settings where some values can only be set when other settings have specific values.

## Problem Statement

In GridBoss systems, certain settings have dependencies:

### SmartLoad Enable/Disable
- **Disabled SmartLoads**: When `SmartLoadX_Enable` is `false`, all related settings should be unavailable
- **Enabled SmartLoads**: When `SmartLoadX_Enable` is `true`, related settings become available

### SOC/Volt vs Time Mode
- **SOC/Volt Mode**: When `SmartLoadX_SOC_Volt` is `true`, only SOC and voltage-based settings are available
- **Time Mode**: When `SmartLoadX_SOC_Volt` is `false`, only time-based settings are available

### Always Available Settings
- **Enable/Disable Switches**: Always available regardless of other settings

Home Assistant doesn't provide built-in popup alerts or dynamic entity enabling/disabling, so we needed a creative solution.

## Solution Architecture

### 1. SmartSOCVoltBits and SmartLoad Bits Tracking

The coordinator now tracks both configuration types for each dongle:

```python
self._smart_soc_volt_bits = {}  # Track SmartSOCVoltBits for each dongle
self._smartload_bits = {}  # Track SmartLoad Bits for each dongle
```

### 2. Entity Availability System

Entities use the `available` property to dynamically show/hide based on dependency settings:

```python
@property
def available(self) -> bool:
    """Return if entity is available."""
    if not self.coordinator.last_update_success:
        return False
    
    # Check if entity should be available based on SmartLoad SOC/Volt settings
    return self.coordinator.is_entity_available_for_smartload(self._dongle_id, self._entity_type)
```

### 3. Validation and User Feedback

When users try to set invalid values, the system:
1. Prevents the setting from being applied
2. Shows a persistent notification explaining why the setting is unavailable
3. Logs a warning message

## Implementation Details

### Coordinator Methods

#### `update_smart_soc_volt_bits(dongle_id, smart_soc_volt_bits)`
Updates the SmartSOCVoltBits settings and triggers entity availability updates.

#### `update_smartload_bits(dongle_id, smartload_bits)`
Updates the SmartLoad Bits settings and triggers entity availability updates.

#### `is_entity_available_for_smartload(dongle_id, entity_unique_id)`
Determines if an entity should be available based on:
- Whether it's a GridBoss dongle
- The SmartLoad number (1-4)
- Whether the SmartLoad is enabled
- Whether it's a SOC/Volt or Time entity
- The current SmartSOCVoltBits setting

#### `is_smartload_enabled(dongle_id, smartload_number)`
Checks if a specific SmartLoad is enabled.

#### `is_entity_available_for_smartload_enable(dongle_id, entity_unique_id)`
Checks availability based only on SmartLoad enable state (used for Enable/Disable switches).

#### `_trigger_entity_availability_update(dongle_id)`
Triggers async updates to entity availability when SmartSOCVoltBits change.

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

### User Experience

1. **Visual Feedback**: Unavailable entities appear grayed out in Home Assistant
2. **Prevention**: Users cannot set values on unavailable entities
3. **Notifications**: Clear explanations when users try to access unavailable settings
4. **Dynamic Updates**: Entities become available/unavailable automatically when SmartSOCVoltBits change

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
2. System shows notification: "The setting 'SmartLoad3 Start SOC' is not available because SmartLoad3 is disabled. Please enable SmartLoad3 first."
3. Entity remains grayed out until SmartLoad3 is enabled

#### Example 2: Wrong Mode
1. User tries to set `SmartLoad1Start0` (time entity) when `SmartLoad1_SOC_Volt` is `true`
2. System shows notification: "The setting 'SmartLoad1 Start0' is not available because SmartLoad1 is configured for Time mode. Please change to SOC/Volt mode first."
3. Entity remains grayed out until SmartLoad mode changes

#### Example 3: Always Available
1. User can always access `SmartLoad1_Enable` switch regardless of other settings
2. This allows users to enable/disable SmartLoads as needed

## Benefits

1. **Prevents Invalid Configurations**: Users cannot set conflicting settings
2. **Clear User Feedback**: Persistent notifications explain why settings are unavailable
3. **Dynamic Behavior**: Entities automatically update when dependencies change
4. **No Breaking Changes**: Existing functionality remains intact
5. **Extensible**: System can be extended for other conditional settings

## Technical Notes

- The system uses Home Assistant's built-in `available` property
- Persistent notifications provide user feedback without popups
- Entity availability updates are triggered asynchronously
- The system gracefully handles missing or incomplete SmartSOCVoltBits data
- All changes are backward compatible

## Future Enhancements

1. **Additional Dependencies**: Extend to other conditional settings
2. **Bulk Operations**: Handle multiple entity updates more efficiently
3. **Configuration UI**: Add visual indicators in the configuration flow
4. **Automation Support**: Allow automations to be aware of entity availability
