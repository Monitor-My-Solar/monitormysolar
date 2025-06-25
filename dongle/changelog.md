## 3.0.0

### Breaking Changes

*   **Inverter Model Selection Required:**
    *   Setup process now requires selecting both inverter brand AND specific model
    *   Model-specific configurations enable optimized communication protocols
    *   Existing installations will prompt for model selection on first boot
    *   Supported models include standard versions, ACS variants, Grid Boss, and more

### Major New Features & User Experience Improvements

#### **Complete UI/UX Overhaul**
*   **New Modern Setup Flow:**
    *   Implemented a step-by-step wizard interface with progress tracking
    *   Added visual feedback with icons and status indicators
    *   Streamlined the setup process with better validation and error handling
    *   Added timezone selection with automatic DST handling
    *   Improved WiFi network scanning with signal strength indicators
    
*   **Redesigned Settings Page:**
    *   Created a modern sidebar navigation system
    *   Organized settings into logical sections: Overview, Connections, Firmware, Advanced, etc.
    *   Added real-time WebSocket updates for live data
    *   Implemented dark mode support with persistent theme selection
    *   Added responsive design for mobile devices

*   **Enhanced Connection Management:**
    *   Replaced basic checkboxes with modern toggle switches (Bootstrap-style)
    *   Added switches directly on connection cards for quick enable/disable
    *   Implemented unsaved changes tracking with confirmation dialogs
    *   Added visual feedback for modified settings (yellow border/glow)
    *   Save button appears only when changes are made

#### **Robust OTA Update System**
*   **Memory-Optimized OTA Process:**
    *   Implemented reboot-based OTA to maximize available heap memory
    *   OTA now sets pending flags and reboots before downloading
    *   Minimal services run during OTA to prevent memory exhaustion
    
*   **OTA Rollback Protection:**
    *   Added ESP-IDF rollback protection with automatic image verification
    *   Dual storage of OTA state in both NVS and LittleFS for redundancy
    *   Boot loop detection - automatically rolls back after 3 failed boots
    *   60-second stability check before marking new firmware as valid
    *   Tracks boot count to detect and prevent boot loops

*   **Enhanced User Feedback:**
    *   Real-time OTA progress via WebSocket
    *   Persistent loading overlay that survives page refreshes
    *   Automatic page refresh at key points during update
    *   Clear status messages throughout the update process

#### **Security & Certificate Updates**
*   **Updated TLS Certificates:**
    *   Added new root CA certificates for secure connections
    *   Improved certificate validation for OTA updates
    *   Enhanced security for cloud service connections

*   **JWT Authentication:**
    *   Implemented proper JWT token handling for API security
    *   Added session management with secure token storage
    *   Password-protected settings with session persistence

#### **Remote Logging & Support System**
*   **Session-Based Remote Logging:**
    *   Implemented secure session key authentication for support connections
    *   Real-time log streaming to dongles.ws.monitormy.solar for live debugging
    *   Historical log transmission with chunked data upload
    *   Progress tracking with user notifications (similar to OTA updates)
    
*   **Chunked Data Transmission:**
    *   Developed robust system for sending large log files in manageable chunks
    *   Prevents memory exhaustion when uploading historical logs
    *   Server acknowledgment system for reliable data transfer
    *   Automatic retry logic with WebSocket library error tolerance
    
*   **Enhanced User Experience:**
    *   Real-time progress updates: "Uploading logs... 45% complete (89 chunks sent)"
    *   Connection status indicators: "✅ Connected to support session"
    *   Visual feedback for log streaming operations
    *   Session management with connect/disconnect controls

#### **Code Architecture Improvements**
*   **Major Refactoring:**
    *   Separated HTTP routes into modular files for better maintainability
    *   Created dedicated modules for different functionality areas
    *   Improved error handling and logging throughout
    *   Better memory management with heap defragmentation

*   **Global Buffer Management:**
    *   Centralized all buffer and stack size definitions in `global_buffers.h`
    *   Optimized task stack allocations based on actual usage patterns
    *   Implemented monitored task creation with stack overflow protection
    *   Static buffer reuse to prevent memory fragmentation

*   **WebSocket Implementation:**
    *   Real-time updates for power flow data
    *   Live connection status monitoring
    *   OTA and log streaming progress tracking
    *   Automatic reconnection with exponential backoff
    *   Support for custom event types (log_streaming_status, remote_streaming_status)

*   **Task Management:**
    *   Improved FreeRTOS task coordination
    *   Better synchronization with event groups
    *   Optimized stack usage with proper size allocation
    *   Enhanced task monitoring and lifecycle management

### Fixes & Improvements

* **Import Values for all time**
    * Fixes a issue where import vaues for all time were being shown as PV1 Data

*   **Critical Boot Issue:**
    *   Fixed crash when device gets IP address during OTA pending boot
    *   Resolved mdns_group event group initialization order
    *   Added skip_hostname_setup flag for OTA boot path

*   **WebSocket Stability:**
    *   Fixed WebSocket disconnection handling during OTA
    *   Improved reconnection logic with better error handling
    *   Added connection state persistence across page refreshes

*   **UI/UX Fixes:**
    *   Fixed "Check Updates" button to navigate to correct firmware section
    *   Improved form validation and error messages
    *   Better handling of offline mode restrictions

*   **Memory Management:**
    *   Fixed memory leaks in WebSocket handling
    *   Improved heap fragmentation management
    *   Better resource cleanup on task deletion
    *   Resolved stack overflow in historical logs transmission task
    *   Optimized buffer allocation for chunked data operations

*   **Remote Logging Fixes:**
    *   Fixed WebSocket library error handling - now ignores false errors while relying on server acknowledgments
    *   Implemented retry logic for WebSocket identification messages (3 attempts with delays)
    *   Resolved chunked log transmission interruption issues
    *   Added proper session disconnection handling and cleanup

*   **MQTT Queue Processing:**
    *   Fixed issue where MQTT settings queue would accumulate without clearing processed messages
    *   Resolved write_settings_array not being properly reset between write cycles
    *   Fixed state machine to process all queued settings before returning to normal operation
    *   Added proper null termination and memory clearing for setting entries

*   **OTA Update Fixes:**
    *   Fixed missing DEV/PROD flags for MQTT-initiated OTA updates
    *   Added proper initiator tracking for HTTP-initiated OTA updates
    *   Ensured firmware version is correctly updated after successful OTA
    *   Fixed both new format and legacy MQTT OTA commands
    *   Fixed OTA flags not persisting across reboot by adding LittleFS backup
    *   Simplified HTTP OTA handler to set flags and reboot directly without unnecessary task creation
    *   Added comprehensive logging for OTA flag setting and NVS operations
    *   Enhanced version management for all OTA paths (HTTP/MQTT) to use server-provided versions when not explicitly specified
    *   Unified version update flow - all OTA methods now save version to `ota_new_version` for consistent post-OTA processing

*   **Grid Boss Fixes:**
    *   Fixed incorrect serial_number_str declaration in json_utils.h
    *   Aligned Grid Boss fault parsing to use bit masks like standard fault system
    *   Consolidated Grid Boss fault codes into main fault_codes.c

### Technical Enhancements

*   **Network Improvements:**
    *   Better WiFi reconnection logic
    *   Improved Ethernet support
    *   Enhanced mDNS service discovery

*   **API Enhancements:**
    *   New redirect routes for legacy URLs
    *   Better error responses with proper HTTP status codes
    *   Improved JSON parsing and validation
    *   Added WebSocket event types: `log_streaming_status` and `remote_streaming_status`
    *   Enhanced real-time status updates for support operations

*   **Monitoring & Diagnostics:**
    *   Enhanced logging with better categorization
    *   Improved error reporting
    *   Better system health monitoring
    *   Implemented comprehensive task stack usage monitoring
    *   Added real-time connection state tracking for remote services
    *   Enhanced WebSocket connection diagnostics with detailed logging

*   **Buffer & Memory Management:**
    *   Centralized buffer size definitions for consistent memory usage
    *   Implemented static buffer reuse patterns to reduce heap fragmentation
    *   Optimized task stack sizes based on actual runtime requirements
    *   Added overflow protection for critical tasks

#### **Access Point Auto-Turnoff**
*   **Configurable AP Auto-Shutdown:**
    *   Added automatic Access Point (AP) turnoff feature with user-configurable timer
    *   Timer options: 1 minute, 5 minutes, 30 minutes, or 60 minutes
    *   AP turns off automatically while keeping Station (STA) mode active
    *   Setting persists across reboots - timer starts automatically if enabled
    
*   **Enhanced UI Control:**
    *   Replaced "Hide SSID" checkbox with modern toggle switch
    *   Timer dropdown appears only when auto-turnoff is enabled
    *   Real-time WebSocket notifications when AP turns off
    *   Settings accessible via `/api/wifi/ap_auto_turnoff` endpoints
    
*   **Implementation Details:**
    *   Self-deleting FreeRTOS task manages the turnoff timer
    *   Clean resource management with no memory leaks
    *   NVS storage for persistent configuration
    *   Graceful AP shutdown preserves WiFi client connection

#### **EG4 Grid Boss Support**
*   **Full Grid Boss Integration:**
    *   Added complete support for EG4 Grid Boss inverters (EG4-branded Luxpower units)
    *   Grid Boss specific register definitions starting at address 2000
    *   Smart Load control with Start/End SOC packed register handling
    *   AC Coupling schedule management with 4 time periods
    *   Generator control with voltage and SOC thresholds
    
*   **Advanced Features:**
    *   Packed SOC register support (low byte = start %, high byte = end %)
    *   Time schedule registers for Smart Load and AC Coupling control
    *   Grid Boss specific fault and warning codes
    *   JSON conversion for all Grid Boss register banks
    *   MQTT command support for packed SOC values (format: "20,80")

#### **MQTT Quality of Service (QoS) Configuration**
*   **Configurable MQTT QoS Levels:**
    *   Added per-connection QoS settings for Home Assistant and Web MQTT
    *   Support for QoS 0 (At most once), QoS 1 (At least once), and QoS 2 (Exactly once)
    *   Settings persist across reboots
    *   Accessible via advanced settings page
    
*   **Implementation:**
    *   QoS applied to all MQTT publish operations
    *   Separate configuration for each MQTT connection
    *   Default QoS 0 for backward compatibility
    *   API endpoints: `/api/mqtt/qos` for configuration

#### **Data Request Speed Control**
*   **Configurable Polling Intervals:**
    *   Input register polling: 1-60 seconds (default: 5s)
    *   Holding register polling: 10-600 seconds (default: 10s)
    *   Scheduled data transmission: 30-3600 seconds (default: 300s)
    *   Hold register polling can be completely disabled
    
*   **Advanced Timing Control:**
    *   Settings accessible via advanced settings page
    *   Real-time updates without reboot required
    *   Optimized for reducing inverter communication load
    *   API endpoint: `/api/config/timing` for configuration

#### **Enhanced MQTT OTA Updates**
*   **New MQTT OTA Command Format:**
    ```json
    {
      "update": "FW_update",     // or "Beta_FW" for beta
      "from": "HA",              // or "MQTT", "web", "UI"
      "version": "2.7.1"         // Optional: target version
    }
    ```
*   **Features:**
    *   Support for standard and beta firmware updates via MQTT
    *   Optional version specification for controlled updates
    *   Automatic version management after successful OTA
    *   Status reporting to appropriate channel based on initiator
    *   Legacy format still supported for backward compatibility

#### **Inverter Communication State Machine**
*   **Reconnection Mode:**
    *   Added intelligent reconnection state for handling connection failures
    *   Monitors MQTT and WiFi connection states
    *   Automatic retry with exponential backoff
    *   Prevents task pile-up during extended disconnections
    
*   **Connection Monitoring:**
    *   Tracks disconnection duration
    *   Logs reconnection attempts for diagnostics
    *   Graceful handling of network interruptions
    *   State preservation across reconnection cycles

### Migration Notes

*   **IMPORTANT: Model selection is now required** - you will be prompted to select your inverter model on first boot after upgrade
*   Users upgrading from 2.x will experience a completely new interface
*   All settings are preserved during upgrade
*   OTA updates now require a reboot cycle for safety
*   Legacy URLs (/standard_settings, /ota, /offline_settings) redirect to new interface
*   MQTT QoS defaults to 0 (at most once) for backward compatibility
*   Data polling intervals retain previous defaults unless explicitly changed