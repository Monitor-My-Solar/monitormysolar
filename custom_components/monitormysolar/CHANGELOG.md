# Changelog
## Version 4.0.0
### Best with dongle firmware 4.3.0+. Some features below REQUIRE 4.3.0.

This is a big release. The headline is that firmware 4.3.0 changes how the dongle
talks to Home Assistant — it now streams only what changed and confirms every
setting write on its own, and it no longer needs the dongle's IP address for
anything. The integration has been reworked to take advantage of that while
staying fully backward compatible with older dongles.

**Upgrading?** Please read the two ⚠️ sections below (dongle IP removed, and the
one-off entity clean-up on first start). Your history and settings are preserved.

#### New Entities added
- Ac Couple Enable
- Smart Load Enable
- RSD Disable
- Grid Peak Shaving Enable
- Gen Peak Shaving Enable
- Smart Load On/Off Voltage
- Smart Load On/off SOC
- Start PV Power (Smart Load)
- Ac Couple Start/stop Voltage
- Ac Couple Start/stop SOC

##### Offgrid only 
- AC First Start and end 

##### Changed Entities
- Some battery/temperature sensors differ by inverter family. For example on
  LuxPower units, battery temperature is reported as **Max/Min Cell Temperature
  (BMS)** rather than a single "Battery Temperature"; on Deye-family units the
  single "Battery Temperature" is provided. You only get the entities your unit
  actually reports — anything left over from an older version that your unit
  doesn't provide will simply show as unavailable and can be removed (see the new
  Restore/clean-up tool below).

#### ⚠️ Breaking change — Dongle IP address removed
- The dongle IP address is **no longer collected or used**. Firmware updates and
  all admin actions now run over MQTT, so an IP is never needed.
- The "Update dongle IPs" option and all IP input fields have been removed from
  setup and options. Existing IP values in your config are ignored.
- **Firmware updates now require dongle firmware 4.3.0 or newer** (the MQTT admin
  command surface). Dongles older than 4.3.0 can no longer be updated from Home
  Assistant — update them once to 4.3.0 by the previous method / app first.

#### Firmware updates over MQTT
- The firmware update entity now triggers OTA via the dongle's MQTT admin command
  (`<dongle_id>/admin {"cmd":"ota"}`) and streams live progress over MQTT
  (`<dongle_id>/ota/progress`), with a final pass/fail on `<dongle_id>/ota/result`.
  No dongle IP, HTTP, or WebSocket involved.
- Added a **Use Beta Firmware** option (Settings) to choose the prod or beta
  track. Updates are selected by track only — since firmware 4.3.0 the version is
  CI-stamped from the build, so the dongle always installs the current build on the
  chosen track (no version targeting).
- The installed-version display strips the chip suffix (e.g. `S3`/`C6`) so it
  compares correctly against the published build version.

#### Optional dongle ID in entity names (with history kept)
- New single-dongle installs get clean entity names without the dongle ID. Existing
  installs are unchanged; opt in via Settings. History (states + statistics) is
  preserved across the change.
- Setup asks whether this is a fresh install or a reconnect so existing history
  lines up automatically.

#### Replace a dongle (transfer history)
- New "Replace a dongle" action (Options → Manage Dongles) moves all entities and
  their full history from a failed/swapped dongle to its replacement.

#### Status diagnostic entities
- The dongle `/status` payload now drives individual diagnostic sensors (firmware
  version, chip type, MQTT/server connection states, memory, boot/crash counts, SD
  health, last reset reason).

#### Deye / SunSynk / SolArk / NeoVolta support
- Added the **Deye** inverter family as a selectable brand (labelled
  "Deye / SunSynk / SolArk / NeoVolta") with a full entity catalog (114 entities:
  84 sensors, 30 numbers, 6 selects, 4 switches), unique_ids mapping 1:1 with the
  dongle's Deye catalog keys.
- Deye TimeSlots (a nested array) currently lands as a single opaque,
  disabled-by-default sensor; per-slot entities are a documented follow-up.

#### Unified `/input` + `/hold` topics (firmware 4.3.0+)
- Firmware 4.3.0+ publishes consolidated `<dongle>/input` and `<dongle>/hold`
  payloads. The coordinator routes these the same way as the legacy per-bank
  topics (the per-key lookup is bank-agnostic), so the same value updates the same
  entity whichever topic it arrives on.
- On connect the integration requests a full snapshot (`<dongle>/snapshot/request`)
  so entities populate immediately. Older firmware ignores the request and keeps
  using the per-bank topics — fully backward compatible.

#### Durable write confirmation (firmware 4.3.0+)
- Firmware 4.3.0+ publishes `<dongle>/setting/updated` on every successful write,
  no matter who initiated it (Home Assistant, the mobile app, the local web UI,
  the Lux server). The integration mirrors that value onto the matching entity so
  Home Assistant converges in ~1 ms instead of waiting for the next `/hold` cycle.
  No-op on older firmware.
- **Values are now normalised to each control's type.** The dongle reports values
  as text (e.g. `"1.00"`); the integration converts them to the right form for the
  entity — a number for a slider, an option for a dropdown, on/off for a switch —
  so controls no longer land on a stray value.
- **The two confirmation channels no longer fight.** On 4.3.0 a Home-Assistant
  write is confirmed on both the classic reply and the new durable channel. The
  integration now recognises its own write and applies it once, instead of
  processing the same change twice.

#### Settings apply cleanly and stay put
- **Fixed dropdowns (selects) briefly going blank / "unknown" after a change.**
  When you set something like a GridBoss Smart Port mode, it now commits to the
  value you chose the moment the dongle confirms success — no flicker, no revert,
  no "unknown".
- The rule is simple now: **a successful write means the value you sent is the
  value.** Home Assistant no longer second-guesses it or reads a stale value back
  over the top. This applies to selects, numbers, switches and time entities.
- Out-of-range or unexpected values coming back from the dongle can no longer blank
  a control — it keeps its current option instead.

#### Entities recover automatically after a dongle restart
- If a dongle reboots or drops off and comes back, Home Assistant now
  automatically re-requests a full snapshot so its entities repopulate instead of
  sitting at "unavailable". This is triggered on any of: the dongle coming back
  online, a detected reboot, or data resuming after a silent gap — and it's
  debounced so a burst of those only sends one request. Fixes entities going
  unavailable and staying that way after a dongle restart.

#### Firmware-group based entity selection
- Which entities a unit gets is now decided by its **firmware group**, derived from
  the firmware code, instead of brittle per-entity allow-lists of exact codes. The
  groups are: **legacy** (A-family hybrids), **ac_coupled** (B units), **GEN**
  (E/F/H — incl. 12K and 8-10K), **threephase** (G), **offgrid** (C — incl. SNA
  6000/12000XP), and **midbox** (GridBoss / I units).
- Each entity declares the groups it applies to; a unit is given an entity when its
  group matches. Membership in a group *is* validity — there's no separate "valid
  codes" list to maintain, and new codes within a known family are handled
  automatically. Matching is case-insensitive, fixing units whose code differed only
  in case.
- GridBoss (midbox) remains a distinct device that only receives its own
  midbox-tagged entities.

#### ⚠️ One-off entity clean-up on first start (no more `_2` duplicates)
- Upgrading from older versions (especially if you'd previously downgraded and come
  back) could leave **duplicate entities with a `_2` on the end** — because the way
  an entity is identified internally changed between versions.
- On the first start after updating, the integration now **automatically cleans
  these up**: it removes the leftover duplicates and moves the live entity back onto
  its clean name, keeping its full history. You should no longer have to rename or
  delete anything by hand.
- This works for **single- and multi-dongle setups alike** (a dongle in a
  GridBoss/FlexBoss combo is treated the same as a standalone one).
- Everything the clean-up does is written to a plain-English log file,
  `monitormysolar_migration.log`, in your Home Assistant config folder — so if
  anything looks off it's easy to see exactly what happened.

#### Restore deleted entities (Options)
- New **"Restore Deleted Entities"** action under the integration's Options. If you
  (or a clean-up) removed or disabled an entity and want it back, this lists them
  and recreates the ones you pick — no need to delete and re-add the whole
  integration. Home Assistant normally refuses to bring a deleted entity back on a
  reload; this handles that for you.

#### Fixes
- **Snapshot now reliably populates all entities on connect.** The full-data
  snapshot (the `{"what":"all"}` reply on `<dongle>/snap/input` and
  `<dongle>/snap/hold`) was being requested before entities had finished
  subscribing, so the reply could land in a window where input sensors missed it —
  leaving values like SOC and other static fields stuck at `unknown` until a later
  change happened to carry that key. The snapshot is now requested once Home
  Assistant has started and entities are subscribed, so every value lands. Entities
  also seed their initial state from the latest snapshot when added, so a value that
  never changes again still shows.
- The snapshot reply (`snap/input` / `snap/hold`) is processed even during the
  startup window rather than being dropped.
- **Multiple batteries**: when a `/batteries` payload contains more than one
  battery, all of them now get their own entities (previously only the first was
  created, because the firmware reports the same battery index for each). A battery
  position is only registered once its sensors are actually built, so a partial
  first payload no longer permanently hides a battery.
- **Duplicate / `_2` entities fixed.** Several sensors (PV power/voltage/current,
  PV energy, temperatures, charge-rate controls, and the "Charge Based on"
  selector) had two catalog definitions that resolved to the same entity, which
  forced Home Assistant to suffix the second with `_2`. Definitions are now scoped
  to the firmware group they apply to, so each unit gets exactly one of each.
- The "Charge Based on" (ACChargeType) selector now shows the correct option set
  per family: offgrid units get the 6-option list, GEN (12K) units the 3-option
  list, and legacy/AC-coupled units their own 3-option list — and the value→label
  mapping follows the same split.
- Firmware updates over MQTT: progress now ignores stale/retained progress
  messages, accepts both `success` and `ok` as a successful result, and the
  installed-version comparison no longer perpetually shows an update available.
- Status diagnostic sensors refresh on the first `/status` after startup; the noisy
  raw-byte memory sensors (heap/PSRAM) are disabled by default to avoid bloating the
  recorder.
- `<dongle>/availability` (the LWT online/offline message) is no longer mis-parsed
  as JSON — it stopped spamming "Invalid JSON" warnings.
- Entity creation no longer aborts on brand registries that contain legacy
  flat-list entries (an `isinstance` guard was added).
- Switch states given as the strings `"0"`/`"1"` are now coerced correctly
  (previously `"0"` evaluated truthy and showed switches as on).
- **kW charge/discharge rate controls now scale correctly.** The AC charge rate
  and forced charge/discharge kW controls display in real kW and send the value the
  dongle expects (e.g. show 8.0 kW, send 80), instead of being off by 10x.
- **SD card sensors only appear where there's an SD card.** SD Health / SD Write
  Failures are shown for S3-chip dongles and are hidden (and disabled by default)
  on C6 dongles, which have no SD card — no more permanently-unknown SD sensors.
- Device grouping: turning grouping **off** now removes the empty sub-devices it
  created, instead of leaving stale, empty devices behind.
- Battery, switch, select and binary-sensor entities are now gated by firmware
  group consistently, so units only get the controls that apply to them.

## Version 3.2.0

### Will require Donlge Firmware 3.2.5 to get the full effect 
As some of the items relate to units and scaling you will need to update the dongle or setting volatage based values will not work
if you are on dongle version 3.1.70 > 3.1.85 you cannot update via the normal methods please contact us for a solution depending on your mobile phone you can update via the android app (on the play store) iOS you will need the public test flight link i think there are only a small number of you affected but i can only see
the firmware versions of users that send data to us. IF YOU DO NOT HEED THIS WARNING AND BLIDLY UPDATE THE DONGLE WITHOUT CHECKING YOUR CURRENT FIRMWARE VERSION YOU WILL BE STUCK AND NEED TO SEND THE DONGLE TO US FOR A REFLASH IM BEING DEADLY SERIOUS WITH THIS.

### Abandonded entities
You might find after updating some entities are no longer provided this is because they have no relevance to your unit (unless you tell me otherwise). Just delete them or contact us if they have been removed by mistake

### New Features

#### Extended Battery Data
- **Dynamic battery device creation**: A separate "Batteries" device is now created automatically when extended battery register data is received on the `dongleid/batteries` MQTT topic
- Not all inverters support this - the device is only created at runtime if battery data is present
- Each battery in the payload gets its own set of sensors including:
  - SOC, SOH, Voltage, Current
  - Remaining Capacity, Full Capacity
  - Max/Min Cell Voltage and Cell Number
  - Max/Min Cell Temperature and Cell Number
  - Charge Voltage Reference, Max Charge Current
  - Cycle Count, Serial Number, Firmware Version
- Battery device is linked to the main dongle device via `via_device`
- Supports multiple batteries per dongle (Battery 1, Battery 2, etc.)

#### Number Input Mode
- Added option to display number entities as text input boxes instead of sliders
- Configurable in Options > Update Settings via the "Use input box for numbers" toggle
- Applies to all 91 number entities across standard and GridBoss configurations
- Defaults to sliders (off) for existing users - no breaking change

#### Device Grouping (Optional)
- Added optional sub-device grouping for entity organisation in the HA UI
- When enabled, entities are grouped into sub-devices: PV, Battery, Grid, EPS, Energy, Temperature, Inverter, Controls, Calculated, GridBoss, GridBoss Controls
- Each sub-device is linked to the main dongle device via `via_device`
- Configurable in Options > Update Settings via the "Enable device grouping" toggle
- Defaults to off - all entities remain on the main device by default

### Entity Organisation
- Reorganised entity definitions in `const.py` into logical banks: `pv`, `battery`, `grid`, `eps`, `energy_daily`, `energy_total`, `temperature_sensors`, `inverter_info`, `calculated`, `powerflow`, `status`, `timestamp`, `fault`, `warning`
- Added `device_group` field to all entity definitions for sub-device grouping support
- Removed duplicated sensor definitions

### Configuration Flow
- Added "Use input box for numbers" toggle to Options > Update Settings
- Added "Enable device grouping" toggle to Options > Update Settings
- Integration reloads automatically when settings are changed

### Fixes
- Added extra support for volatage values to be presented as 40.X but send as 40X
- Fixed scaling on some values
- Fixed units on some values
- **Fixed optimistic update revert issue**: Switch, number, and time entities now retain their user-set values immediately after changing, instead of reverting to the old value for ~30 seconds until the next hold poll. Added `_user_initiated_change` flag (matching the existing select entity pattern) to prevent stale coordinator data from overwriting pending changes.
- **Fixed time entity revert_state**: Time entity `revert_state()` was a no-op that didn't actually restore the previous value. Now properly saves and restores `_previous_state`.
- **Fixed charge type conditional logic**: The error reason messages for charge voltage, SOC, and time entities were checking against option strings that don't exist in any firmware select (`"SOC/Volt According To"`, `"Time and SOC/Volt According To"`). Updated to use the correct consolidated option lists matching both firmware groups.
- **Fixed HAAA firmware code group**: `HAAA` was incorrectly mapped to the 6-option ACChargeType group instead of the 3-option group (`"According To Time"`, `"According To SOC/VOLT"`, `"According To Time and SOC/VOLT"`), matching the const.py entity definition.

---

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
- **Fixed entity filtering issue**: Corrected `allowed_device_types` to `allowed_firmware_codes` in const.py to ensure proper entity creation filtering based on firmware codes
- **Resolved duplicate entity creation**: Fixed issue where entities with same unique_id but different firmware code requirements were both being created due to incorrect filtering key names
- **Improved firmware code filtering**: All sensor, switch, number, select, and time entities now properly respect firmware code restrictions during entity creation
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
- **Added enhanced charge control entities**: New charge control system with dual-condition logic:
  - **Charge Control Select**: "Charge Control" select with "Voltage" and "SOC" options
  - **Charge Based On Select**: "Charge Based on" select with "Time According To", "SOC/Volt According To", and "Time and SOC/Volt According To" options (firmware-dependent)
  - **Charge Voltage Entities**: "AC Charge Start (Voltage)" and "AC Charge End (Voltage)" number entities (available when Charge Control = "Voltage" AND Charge Based On = "SOC/Volt According To" or "Time and SOC/Volt According To")
  - **Charge SOC Entities**: "AC Charge Start (SOC)" and "AC Charge End (SOC)" number entities (available when Charge Control = "SOC" AND Charge Based On = "SOC/Volt According To" or "Time and SOC/Volt According To")
  - **Charge Time Entities**: 48 time slot select entities (Time0-Time47) for 30-minute intervals with "Does Not Operate", "AC Charge", "PV Charge", "Discharge" options (available when Charge Based On = "Time According To")
  - **Charge Time Entities**: "AC Charge Start", "AC Charge End", "AC Charge Start1", "AC Charge End1", "AC Charge Start2", "AC Charge End2" time entities (available when Charge Based On = "Time According To")
- **Fixed device page hanging issue**: Resolved invalid min/max range in "Battery Charge Start Point (W)" number entity that was causing device pages to hang when loading entities
- **Migrated to Home Assistant October 2025 service registration API**: Updated service registration to use the new `service.async_register_platform_entity_service` API to ensure compatibility with the latest Home Assistant version

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


