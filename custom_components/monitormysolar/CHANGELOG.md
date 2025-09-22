# Changelog

## Version 3.1.0 - GridBoss Enhancements & Performance Improvements

### 🔄 **Important: GridBoss Upgrade Instructions**
If you are using GridBoss functionality, please follow these steps to upgrade:
1. **Delete the integration** from Home Assistant
2. **Reboot** Home Assistant
3. **Update through HACS** to get the latest version
4. **Re-setup** the integration with your GridBoss configuration

This ensures a clean upgrade and prevents any configuration conflicts with the new GridBoss features.
- **Multi-Inverter**: Enhanced support for parallel inverter configurations with GridBoss

### 🚀 Major Performance Improvements
- **Fixed Home Assistant Slow Startup**: Implemented startup delay to prevent MQTT message processing during HA initialization
- **Eliminated Excessive Coordinator Updates**: Reduced coordinator update frequency from every 1.5 seconds to only when needed
- **Optimized MQTT Processing**: Deferred non-critical MQTT message processing until after HA startup completion
- **Improved Main Thread Performance**: Prevented blocking operations during Home Assistant startup
- **Resolved Bootstrap Timeout**: Fixed blocking `while True:` loop in SyncStatusSensor that was causing 5+ minute startup times
- **Non-Blocking Async Scheduling**: Replaced blocking loops with proper async scheduling using `async_call_later()`

### 🔧 GridBoss Configuration & Setup Fixes
- **Enhanced Config Flow**: Added dedicated GridBoss configuration step with proper dongle selection
- **Improved Error Handling**: Added comprehensive error handling for dongle connectivity and firmware code reception
- **Fixed Entity Creation Logic**: Implemented strict GridBoss entity filtering to prevent creation of unnecessary standard entities
- **Corrected Device Naming**: Fixed GridBoss device naming to display "GridBoss" instead of generic names

### 📡 GridBoss MQTT & Payload Processing
- **Fixed Nested Payload Parsing**: Implemented proper handling of GridBoss nested JSON payload structure
- **Corrected Entity Name Mapping**: Fixed mapping between payload keys and entity unique_ids
- **Enhanced Topic Routing**: Improved MQTT topic routing for GridBoss-specific settings
- **Simplified Payload Processing**: Streamlined nested data processing with recursive flattening

### 🛠️ Technical Improvements
- **Removed Complex Throttling**: Simplified coordinator update mechanism for better performance
- **Enhanced Fault/Warning Deduplication**: Prevented duplicate processing of identical fault/warning data
- **Improved Entity Type Determination**: Optimized entity type detection for better performance
- **Better Error Recovery**: Enhanced error handling and recovery mechanisms

### 🎯 User Experience Enhancements
- **Faster Home Assistant Startup**: Reduced startup time by deferring MQTT processing
- **Cleaner Debug Logs**: Eliminated excessive "Manually updated MonitorySolar Coordinator data" messages
- **More Responsive Interface**: Home Assistant becomes responsive much faster after restart
- **Better Configuration Flow**: Improved GridBoss setup process with clear error messages

### 🔄 Backward Compatibility
- **Maintained All Existing Features**: All previous functionality preserved
- **No Breaking Changes**: Existing configurations continue to work without modification
- **Preserved Entity History**: All entity data and settings remain intact
- **Seamless Upgrade Path**: No manual intervention required for existing users

### 📋 Technical Details
- **Startup Delay**: 30-second delay before MQTT message processing begins
- **Firmware Code Processing**: Still processed immediately for proper entity creation
- **GridBoss Entity Filtering**: Only creates entities explicitly allowed for "IAAB" firmware
- **Payload Structure**: Supports both old and new nested payload formats

### 🐛 Bug Fixes
- Fixed `IndentationError` in sensor.py that prevented integration loading
- Resolved `NameError: name 'data_to_process' is not defined` in coordinator
- Fixed GridBoss entity count issues (was creating ~400 entities, now creates only relevant ones)
- Corrected GridBoss device naming in Home Assistant interface
- Fixed nested payload parsing for GridBoss settings updates
- **Fixed Home Assistant startup timeout**: Replaced blocking `while True:` loop in SyncStatusSensor with non-blocking async scheduling
- **Resolved 5+ minute startup times**: Prevented bootstrap timeout warnings and excessive coordinator updates during startup
- **Fixed GridBoss MQTT routing issue**: GridBoss settings were incorrectly being sent to bank-specific topics instead of the standard `/update` topic, causing settings to be rejected
- **Enhanced GridBoss conditional entity system**: Implemented hierarchical availability logic based on Port Mode → SOC/Volt mode → Enable state
- **Added Port Mode selects**: New SmartLoad1-4 Port Mode selects with proper numeric value mapping (0=Does Not Operate, 1=Smart Load, 2=AC Coupled)
- **Fixed switch availability logic**: Added proper availability checking to switch entities based on Port Mode, SOC/Volt mode, and SmartLoad enable state
- **Firmware code persistence**: Firmware codes are now saved to config entry data and only requested when not already available, improving startup performance
- **Fixed availability timing issue**: Added 0.5s delay to availability updates to prevent blocking legitimate user actions when Port Mode changes
- **Removed availability blocking from user actions**: Availability logic now only affects UI display (grayed out entities) but no longer blocks user actions, preventing the "revert" issue
- **Fixed select entity revert issue**: Select entities now properly store previous state before changing and revert correctly on MQTT failure, preventing the auto-revert issue with Port Mode selects
- **Fixed coordinator override issue**: Added user-initiated change flag to prevent coordinator from overriding user selections during MQTT processing, solving the select revert problem
- **Fixed availability delay issue**: Port Mode changes now trigger immediate availability updates, and enable switches are always available when Port Mode is set to "Smart Load" or "AC Coupled" (both SmartLoad and AC Coupled enable switches)
- **Added SOC/Volt mode select entities**: New SmartLoad1-4 Mode selects with "Time" and "SOC/Volt" options, available when Port Mode is set to "Smart Load" or "AC Coupled"

### 📝 Notes
- **Dongle Firmware**: Requires dongle firmware 3.1.0+ for optimal GridBoss functionality
- **Performance**: Significant improvement in Home Assistant startup time
- **GridBoss**: Full support for GridBoss units with firmware code "IAAB"

---

## Version 3.0.1 - GridBoss Support & Enhanced Multi-Inverter Features

### Minimum Requirements include the dongle Firmware 3.0.0> if your dongle is below this then a OTA update will be required. 
- if you do not update your dongle before 02/07/2025 you will need to contact us for a upgrade path 
- OTA updates stop working on FW Below 3.0.0 on the data above. 

### ⚠️ Breaking Changes
- UI version entities removed (no longer needed)
- Update entities changed from brand-specific to dongle-specific
- `current_ui_versions` attribute removed from coordinator

# Migration Guide from v2.x to v3.0.1

## Important: After updating to v3.0.1

If you're upgrading from a previous version and see errors like:
```
AttributeError: 'MonitorMySolar' object has no attribute 'current_ui_versions'
```

You need to:

1. **Restart Home Assistant** - This ensures all code changes are loaded
2. If still having issues:
   - Remove the integration (your settings will be preserved)
   - Restart Home Assistant
   - Re-add the integration with the same dongle IDs

## What Changed in v3.0.1

- UI version tracking has been removed (only firmware versions are tracked)
- Update entities are now per-dongle instead of per-brand
- GridBoss support added for firmware code IAAB
- Improved multi-dongle management
- Updated and added some new settings for select inverters for Generators 

## Breaking Changes

- `current_ui_versions` attribute removed from coordinator
- Update entities changed from brand-specific to dongle-specific

## Notes

- Your entity history will be preserved
- All settings will remain intact
- The integration title will update to show "Inverter" or "Inverters" based on dongle count


### 🎯 Major Features



#### 1. **GridBoss Support (BETA)**
- ✨ Full integration for GridBoss distribution units (firmware code IAAB)
- 📊 Comprehensive monitoring of voltage, current, power, and energy across all phases
- ⚡ Smart load control for up to 6 configurable loads with scheduling
- 🔌 Generator integration with startup/shutdown control
- ☀️ AC coupling support for monitoring external solar systems
- 📈 68 new sensors for real-time monitoring
- 🔧 17 switches for system control
- ⏰ 48 time entities for scheduling
- 🎛️ 56 number entities for configuration

#### 2. **Simplified Firmware Updates**
- 🚀 Firmware update entity now available for all dongles (not brand-specific)
- 📊 Real-time progress tracking with percentage display
- 🔄 WebSocket monitoring for update progress during dongle reboot
- ❌ Fixed "Unknown error" in update entity UI
- 📝 Proper release notes display with changelog support

#### 3. **Advanced Dongle Management**
- ✨ Add or remove dongles after installation via the Options flow
- 🔧 No need to delete and recreate the integration when adding parallel inverters
- 🔍 Live connectivity testing when adding new dongles
- 🔄 Automatic integration reload after dongle changes

#### 4. **Inverter Synchronization (Beta) **
- 🔄 New sync settings switch for automatic inverter synchronization
- 📊 Sync status sensor showing real-time synchronization state
- ⚡ Automatic detection and correction of out-of-sync settings
- 📝 Detailed sync history tracking with timestamps

#### 5. **Enhanced Status Monitoring**
- 📊 New "Check Status" option in configuration showing:
  - Connection status for each dongle (✅ Connected / ❌ Not responding)
  - Firmware versions and codes
  - Total entity count
  - Setup errors and warnings
- 🔍 Sync status sensor with detailed attributes:
  - Out-of-sync settings with ❌ indicators
  - Synced settings sample with ✅ indicators
  - Last check timestamp
  - Individual dongle values for each setting

#### 6. **Entity Filtering by Firmware Code**
- 🎯 All settings entities (switches, numbers, time, select) now respect firmware codes
- 🔍 Entities only created when firmware code matches requirements
- 🚫 Prevents incompatible entities from being created

### 🐛 Bug Fixes

#### 1. **GridBoss & Update Entity Fixes**
- Fixed "Unknown error" when viewing update entities
- Fixed incorrect method name `release_summary` → `release_notes()`
- Fixed missing `UpdateDeviceClass.FIRMWARE` declaration
- Removed problematic AwesomeVersion dependency
- Fixed version comparison logic
- Fixed entity creation to check firmware codes properly
- Fixed MQTT topic subscriptions for GridBoss data
- Removed UI version tracking (only firmware versions now)

#### 2. **Combined Entity Fixes**
- Fixed double "combined" prefix in sync settings entity ID
- Fixed combined switches showing as unavailable on startup
- Fixed combined entity attributes not updating when individual dongles change
- Fixed combined entities looking for MQTT data instead of aggregating from source entities
- Fixed entity ID generation consistency across all combined entity types

#### 3. **Callback & Async Issues**
- Fixed `TypeError: 'NoneType' object is not callable` errors in switches, selects, and time entities
- Fixed incorrect usage of `call_soon_threadsafe` with method calls
- Fixed async/sync callback mixing issues

#### 4. **MQTT Response Handling**
- Fixed dongle ID format mismatches in multi-dongle responses
- Improved response matching for different dongle ID formats (colons vs underscores)
- Added comprehensive logging for multi-dongle operations
- Fixed missing responses from inverters during combined operations

#### 5. **Firmware Update Fixes**
- Fixed update entities showing as "Unavailable"
- Fixed WebSocket firmware update progress parsing
- Changed firmware updates to use HTTP API instead of MQTT
- Added proper error detection for failed updates

### 🔧 Technical Improvements

#### 1. **GridBoss Implementation**
- GridBoss entities integrated into LuxPower brand section
- All GridBoss entities tagged with `allowed_firmware_codes: ["IAAB"]`
- Dynamic MQTT subscriptions based on configuration:
  - `gridboss_inputbank1` - Real-time monitoring
  - `gridboss_inputbank2` - Frequency and mode data
  - `gridboss_holdbank1` - Control settings
- Added GridBoss option to config flow

#### 2. **Update Process Improvements**
- Simplified to basic version comparison
- Uses Home Assistant's built-in version comparison
- Progress monitoring via WebSocket during updates
- Better error messages and logging

#### 3. **Entity State Management**
- Improved state update handling for all entity types
- Enhanced availability checking during entity initialization
- Added retry logic for entity initialization

#### 4. **Error Tracking**
- Added comprehensive error tracking during setup
- Errors are now visible in the configuration flow
- Better error messages for connection issues
- Detailed logging for troubleshooting

#### 5. **Configuration Flow Enhancements**
- New menu-based options flow
- Clearer navigation and user feedback
- Live validation of dongle connections
- Improved translations and help text

### 📝 Configuration Updates

#### GridBoss Setup:
1. **New Installation**: Check "GridBoss Connected" during setup
2. **Existing Installation**: Configure → Options → Update Settings → Check "GridBoss Connected"
3. **Requirements**: 
   - LuxPower inverter
   - Firmware code IAAB
   - GridBoss option enabled

#### Options Flow Menu Structure:
1. **Manage Dongles**
   - Add new dongle (with connectivity test)
   - Remove existing dongle
   - Update dongle IP addresses

2. **Update Settings**
   - Configure update intervals
   - Enable/Disable GridBoss

3. **Check Status**
   - View dongle connectivity
   - See firmware versions
   - Review setup errors
   - Monitor entity counts

### 🚀 Usage Notes

#### GridBoss Features:
- **Monitor**: Track power flow across all phases and loads
- **Control**: Manage generator, smart loads, and AC coupling
- **Schedule**: Set time-based operations for loads and systems
- **Optimize**: Configure power limits and priorities

#### Firmware Updates:
- Updates shown for all dongles automatically
- Click "Install" to begin update
- Progress shown in real-time
- Dongle will reboot during update process

#### Sync Settings Feature:
- Enable via `switch.combined_sync_settings`
- Monitor status via `sensor.combined_sync_status`
- Automatically syncs settings across all parallel inverters
- Prevents manual configuration drift between inverters

#### Adding Dongles:
1. Go to Settings → Devices & Services
2. Find Monitor My Solar → Configure
3. Choose "Manage Dongles" → "Add new dongle"
4. Enter dongle ID (e.g., `dongle-12:34:56:78:90:12`)
5. System will test connectivity before adding


### 📋 Requirements
- MQTT integration configured
- Valid dongle IDs in format `dongle-XX:XX:XX:XX:XX:XX`
- Dongle IP address configured for firmware updates
- Firmware code IAAB for GridBoss features

### 🙏 Acknowledgments
Thanks to all users who reported issues and provided feedback for multi-inverter setups!




## Version 3.0.0 - GridBoss Support & Enhanced Multi-Inverter Features

### Minimum Requirements include the dongle Firmware 3.0.0> if your dongle is below this then a OTA update will be required. 
- if you do not update your dongle before 02/07/2025 you will need to contact us for a upgrade path 
- OTA updates stop working on FW Below 3.0.0 on the data above. 

### ⚠️ Breaking Changes
- UI version entities removed (no longer needed)
- Update entities changed from brand-specific to dongle-specific
- `current_ui_versions` attribute removed from coordinator

# Migration Guide from v2.x to v3.0.0

## Important: After updating to v3.0.0

If you're upgrading from a previous version and see errors like:
```
AttributeError: 'MonitorMySolar' object has no attribute 'current_ui_versions'
```

You need to:

1. **Restart Home Assistant** - This ensures all code changes are loaded
2. If still having issues:
   - Remove the integration (your settings will be preserved)
   - Restart Home Assistant
   - Re-add the integration with the same dongle IDs

## What Changed in v3.0.0

- UI version tracking has been removed (only firmware versions are tracked)
- Update entities are now per-dongle instead of per-brand
- GridBoss support added for firmware code IAAB
- Improved multi-dongle management

## Breaking Changes

- `current_ui_versions` attribute removed from coordinator
- Update entities changed from brand-specific to dongle-specific

## Notes

- Your entity history will be preserved
- All settings will remain intact
- The integration title will update to show "Inverter" or "Inverters" based on dongle count


### 🎯 Major Features



#### 1. **GridBoss Support (BETA)**
- ✨ Full integration for GridBoss distribution units (firmware code IAAB)
- 📊 Comprehensive monitoring of voltage, current, power, and energy across all phases
- ⚡ Smart load control for up to 6 configurable loads with scheduling
- 🔌 Generator integration with startup/shutdown control
- ☀️ AC coupling support for monitoring external solar systems
- 📈 68 new sensors for real-time monitoring
- 🔧 17 switches for system control
- ⏰ 48 time entities for scheduling
- 🎛️ 56 number entities for configuration

#### 2. **Simplified Firmware Updates**
- 🚀 Firmware update entity now available for all dongles (not brand-specific)
- 📊 Real-time progress tracking with percentage display
- 🔄 WebSocket monitoring for update progress during dongle reboot
- ❌ Fixed "Unknown error" in update entity UI
- 📝 Proper release notes display with changelog support

#### 3. **Advanced Dongle Management**
- ✨ Add or remove dongles after installation via the Options flow
- 🔧 No need to delete and recreate the integration when adding parallel inverters
- 🔍 Live connectivity testing when adding new dongles
- 🔄 Automatic integration reload after dongle changes

#### 4. **Inverter Synchronization (Beta) **
- 🔄 New sync settings switch for automatic inverter synchronization
- 📊 Sync status sensor showing real-time synchronization state
- ⚡ Automatic detection and correction of out-of-sync settings
- 📝 Detailed sync history tracking with timestamps

#### 5. **Enhanced Status Monitoring**
- 📊 New "Check Status" option in configuration showing:
  - Connection status for each dongle (✅ Connected / ❌ Not responding)
  - Firmware versions and codes
  - Total entity count
  - Setup errors and warnings
- 🔍 Sync status sensor with detailed attributes:
  - Out-of-sync settings with ❌ indicators
  - Synced settings sample with ✅ indicators
  - Last check timestamp
  - Individual dongle values for each setting

#### 6. **Entity Filtering by Firmware Code**
- 🎯 All settings entities (switches, numbers, time, select) now respect firmware codes
- 🔍 Entities only created when firmware code matches requirements
- 🚫 Prevents incompatible entities from being created

### 🐛 Bug Fixes

#### 1. **GridBoss & Update Entity Fixes**
- Fixed "Unknown error" when viewing update entities
- Fixed incorrect method name `release_summary` → `release_notes()`
- Fixed missing `UpdateDeviceClass.FIRMWARE` declaration
- Removed problematic AwesomeVersion dependency
- Fixed version comparison logic
- Fixed entity creation to check firmware codes properly
- Fixed MQTT topic subscriptions for GridBoss data
- Removed UI version tracking (only firmware versions now)

#### 2. **Combined Entity Fixes**
- Fixed double "combined" prefix in sync settings entity ID
- Fixed combined switches showing as unavailable on startup
- Fixed combined entity attributes not updating when individual dongles change
- Fixed combined entities looking for MQTT data instead of aggregating from source entities
- Fixed entity ID generation consistency across all combined entity types

#### 3. **Callback & Async Issues**
- Fixed `TypeError: 'NoneType' object is not callable` errors in switches, selects, and time entities
- Fixed incorrect usage of `call_soon_threadsafe` with method calls
- Fixed async/sync callback mixing issues

#### 4. **MQTT Response Handling**
- Fixed dongle ID format mismatches in multi-dongle responses
- Improved response matching for different dongle ID formats (colons vs underscores)
- Added comprehensive logging for multi-dongle operations
- Fixed missing responses from inverters during combined operations

#### 5. **Firmware Update Fixes**
- Fixed update entities showing as "Unavailable"
- Fixed WebSocket firmware update progress parsing
- Changed firmware updates to use HTTP API instead of MQTT
- Added proper error detection for failed updates

### 🔧 Technical Improvements

#### 1. **GridBoss Implementation**
- GridBoss entities integrated into LuxPower brand section
- All GridBoss entities tagged with `allowed_firmware_codes: ["IAAB"]`
- Dynamic MQTT subscriptions based on configuration:
  - `gridboss_inputbank1` - Real-time monitoring
  - `gridboss_inputbank2` - Frequency and mode data
  - `gridboss_holdbank1` - Control settings
- Added GridBoss option to config flow

#### 2. **Update Process Improvements**
- Simplified to basic version comparison
- Uses Home Assistant's built-in version comparison
- Progress monitoring via WebSocket during updates
- Better error messages and logging

#### 3. **Entity State Management**
- Improved state update handling for all entity types
- Enhanced availability checking during entity initialization
- Added retry logic for entity initialization

#### 4. **Error Tracking**
- Added comprehensive error tracking during setup
- Errors are now visible in the configuration flow
- Better error messages for connection issues
- Detailed logging for troubleshooting

#### 5. **Configuration Flow Enhancements**
- New menu-based options flow
- Clearer navigation and user feedback
- Live validation of dongle connections
- Improved translations and help text

### 📝 Configuration Updates

#### GridBoss Setup:
1. **New Installation**: Check "GridBoss Connected" during setup
2. **Existing Installation**: Configure → Options → Update Settings → Check "GridBoss Connected"
3. **Requirements**: 
   - LuxPower inverter
   - Firmware code IAAB
   - GridBoss option enabled

#### Options Flow Menu Structure:
1. **Manage Dongles**
   - Add new dongle (with connectivity test)
   - Remove existing dongle
   - Update dongle IP addresses

2. **Update Settings**
   - Configure update intervals
   - Enable/Disable GridBoss

3. **Check Status**
   - View dongle connectivity
   - See firmware versions
   - Review setup errors
   - Monitor entity counts

### 🚀 Usage Notes

#### GridBoss Features:
- **Monitor**: Track power flow across all phases and loads
- **Control**: Manage generator, smart loads, and AC coupling
- **Schedule**: Set time-based operations for loads and systems
- **Optimize**: Configure power limits and priorities

#### Firmware Updates:
- Updates shown for all dongles automatically
- Click "Install" to begin update
- Progress shown in real-time
- Dongle will reboot during update process

#### Sync Settings Feature:
- Enable via `switch.combined_sync_settings`
- Monitor status via `sensor.combined_sync_status`
- Automatically syncs settings across all parallel inverters
- Prevents manual configuration drift between inverters

#### Adding Dongles:
1. Go to Settings → Devices & Services
2. Find Monitor My Solar → Configure
3. Choose "Manage Dongles" → "Add new dongle"
4. Enter dongle ID (e.g., `dongle-12:34:56:78:90:12`)
5. System will test connectivity before adding


### 📋 Requirements
- MQTT integration configured
- Valid dongle IDs in format `dongle-XX:XX:XX:XX:XX:XX`
- Dongle IP address configured for firmware updates
- Firmware code IAAB for GridBoss features

### 🙏 Acknowledgments
Thanks to all users who reported issues and provided feedback for multi-inverter setups!


