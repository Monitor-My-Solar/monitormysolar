# Changelog

## Version 3.0.0 - GridBoss Support & Enhanced Multi-Inverter Features

### 🎯 Major Features
### Minimum Requirements include the dongle Firmware 3.0.0> if your dongle is below this then a OTA update will be required. 
- if you do not update your dongle before 02/07/2025 you will need to contact us for a upgrade path 
- OTA updates stop working on FW Below 3.0.0 on the data above. 

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

### ⚠️ Breaking Changes
- UI version entities removed (no longer needed)
- Update entities changed from brand-specific to dongle-specific

### 📋 Requirements
- MQTT integration configured
- Valid dongle IDs in format `dongle-XX:XX:XX:XX:XX:XX`
- Dongle IP address configured for firmware updates
- Firmware code IAAB for GridBoss features

### 🙏 Acknowledgments
Thanks to all users who reported issues and provided feedback for multi-inverter setups!


