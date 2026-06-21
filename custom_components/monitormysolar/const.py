"""Constants for Inverter MQTT."""
from logging import Logger, getLogger
from homeassistant.const import (
    CONF_MODE,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfApparentPower,
    UnitOfTime,
)
from homeassistant.components.update import (
    UpdateDeviceClass
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

# Domain for the integration
DOMAIN = "monitormysolar"

# Device grouping configuration
CONF_ENABLE_DEVICE_GROUPING = "enable_device_grouping"
DEFAULT_ENABLE_DEVICE_GROUPING = False

# Number input mode configuration
CONF_USE_INPUT_BOX = "use_input_box"
DEFAULT_USE_INPUT_BOX = False

# Firmware track selection: install beta firmware instead of prod.
CONF_USE_BETA = "use_beta_firmware"
DEFAULT_USE_BETA = False

# Entity naming: drop the dongle ID prefix from entity_ids.
# Only honored for single-dongle installs (multi-dongle must keep the dongle ID
# to disambiguate). No module-level default: it is install-time contextual —
# fresh installs default True, existing/reconnect installs default False so
# history (anchored to unique_id) is preserved.
CONF_DROP_DONGLE_ID = "drop_dongle_id"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.TIME,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.UPDATE,
]


FIRMWARE_CODES = {
    "a_3_6k_Hybrid": {
        "Device_Type": "A Standard model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "High Voltage Battery Version",
            "C": "Gen 3-6k"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "US Model"
        }
    },
    "B_AC_Coupled": {
        "Device_Type": "A Standard Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    },
    "C_6_12k_OffGrid": {
        "Device_Type": "C Standard Model",
        "Derived_Device_Type": {
            "a": "Standard Model",
            "b": "Others",
            "c": "Others"
        },
        "ODM_Code": {
            "a": "Luxpower",
            "b": "Others",
            "c": "Others"
        },
        "Feature_Code": {
            "a": "Standard Model",
            "b": "Parallel Model",
            "c": "Others"
        }
    },
    "E_8_10K_Hybrid": {
        "Device_Type": "A Standard Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    },
    "F_12K_Hybrid": { # FAAB USA EG4 12k Model
        "Device_Type": "A Standard Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    },
    "G_3Phase_Hybrid": {
        "Device_Type": "A Standard Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    },
    "H_EU_GEN_7-10k": {
        "Device_Type": "A Standard Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    },
    "I_GridBoss": {
        "Device_Type": "I GridBoss Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    }
}

VALID_FIRMWARE_CODES = {
    "AAAA": "3-6k Hybrid Standard",
    "AAAB": "3-6k Hybrid Parallel",
    "BAAA": "AC Coupled Standard",
    "BAAB": "AC Coupled Parallel",
    "ccaa": "6-12k Standard",
    "FAAB": "12k Hybrid Parallel",
    "FAAA": "12k Hybrid Standard",
    "EAAA": "8-10k Hybrid Standard",
    "EAAB": "8-10k Hybrid Parallel",
    "HAAA": "Gen Models",
    "ceaa" : "Off Grid",
    "IAAB": "GridBoss",
}

BATTERY_STATUS_MAP = {
    "00": {"charge": False, "discharge": False},
    "01": {"charge": True, "discharge": False},
    "02": {"charge": False, "discharge": True},
    "03": {"charge": True, "discharge": True},
    "10": {"charge": False, "discharge": False},
    "11": {"charge": True, "discharge": False},
    "12": {"charge": False, "discharge": False},
    "13": {"charge": True, "discharge": True},
    "20": {"charge": False, "discharge": False},
    "21": {"charge": True, "discharge": False},
    "22": {"charge": False, "discharge": False},
    "23": {"charge": True, "discharge": True},
    "0": {"charge": False, "discharge": False},
    "1": {"charge": True, "discharge": False},
    "2": {"charge": False, "discharge": True},
    "3": {"charge": True, "discharge": True}
}

# Default MQTT configuration for Home Assistant broker
DEFAULT_MQTT_SERVER = "core-mosquitto"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_USERNAME = ""
DEFAULT_MQTT_PASSWORD = ""


# Diagnostic sensors derived from the firmware-level /status payload. These apply
# to every dongle regardless of brand/firmware (all dongles publish /status), so
# they are created for all dongles independently of the per-brand ENTITIES table.
# Each reads one (possibly nested) field from the /status blob via status_field.
# sensor_class "status_field" -> StatusFieldSensor in sensor.py.
STATUS_DIAGNOSTIC_SENSORS = [
    # --- Health / connectivity essentials ---
    {"name": "Firmware Version", "type": "sensor", "unique_id": "fw_version_full", "status_field": "version", "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "Chip Type", "type": "sensor", "unique_id": "chip_type", "status_field": "chipType", "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "MQTT HA State", "type": "sensor", "unique_id": "mqtt_ha_state", "status_field": "mqtt.ha_state", "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "MQTT Web State", "type": "sensor", "unique_id": "mqtt_web_state", "status_field": "mqtt.web_state", "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "Inverter Server State", "type": "sensor", "unique_id": "lux_server_state", "status_field": "lux_server.state", "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "SD Card Health", "type": "sensor", "unique_id": "sd_health", "status_field": "sd.health", "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "Last Reset Reason", "type": "sensor", "unique_id": "last_reset_reason", "status_field": "Last_Reset_Reason", "sensor_class": "status_field", "device_group": "Diagnostics"},
    # --- Memory diagnostics ---
    {"name": "Heap Free", "type": "sensor", "unique_id": "heap_free", "status_field": "memory.heap_free", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": "B", "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "Heap Min Free", "type": "sensor", "unique_id": "heap_min", "status_field": "memory.heap_min", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": "B", "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "Heap Fragmentation", "type": "sensor", "unique_id": "heap_frag_pct", "status_field": "memory.heap_frag_pct", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": PERCENTAGE, "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "PSRAM Free", "type": "sensor", "unique_id": "psram_free", "status_field": "memory.psram_free", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": "B", "sensor_class": "status_field", "device_group": "Diagnostics"},
    # --- Reliability counters ---
    {"name": "Boot Count", "type": "sensor", "unique_id": "boot_count", "status_field": "boot.count", "state_class": SensorStateClass.TOTAL_INCREASING, "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "Crash Count", "type": "sensor", "unique_id": "crash_count", "status_field": "crash.count", "state_class": SensorStateClass.TOTAL_INCREASING, "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "Inverter Server Reconnects", "type": "sensor", "unique_id": "lux_server_reconnects", "status_field": "lux_server.reconnects", "state_class": SensorStateClass.TOTAL_INCREASING, "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "Inverter Server Failed", "type": "sensor", "unique_id": "lux_server_failed", "status_field": "lux_server.failed", "state_class": SensorStateClass.TOTAL_INCREASING, "sensor_class": "status_field", "device_group": "Diagnostics"},
    {"name": "SD Write Failures", "type": "sensor", "unique_id": "sd_write_failures", "status_field": "sd.write_failures", "state_class": SensorStateClass.TOTAL_INCREASING, "sensor_class": "status_field", "device_group": "Diagnostics"},
]



ENTITIES = {
        "Lux": {
            "sensor": {
                "calculated": [
                    {"name": "Battery Time to Empty", "type": "sensor", "unique_id": "battery_time_empty", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.DURATION, "unit_of_measurement": UnitOfTime.HOURS, "calculation": {"operation": "battery_time", "sensors": ["batcapacity", "vbat", "pload", "batteryflow_live", "soc", "pall"], "attributes": ["calculated_kwh_storage_total", "calculated_kwh_left", "time_battery_empty", "human_readable_time_left"]}, "sensor_class": "calculated", "device_group": "Calculated"},
                    {"name": "PV1 Current", "type": "sensor", "unique_id": "ipv1", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "calculation": {"operation": "division", "sensors": ["ppv1", "vpv1"]}, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa"], "sensor_class": "calculated", "device_group": "Calculated"},
                    {"name": "PV2 Current", "type": "sensor", "unique_id": "ipv2", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "calculation": {"operation": "division", "sensors": ["ppv2", "vpv2"]}, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa"], "sensor_class": "calculated", "device_group": "Calculated"},
                    {"name": "PV3 Current", "type": "sensor", "unique_id": "ipv3", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "calculation": {"operation": "division", "sensors": ["ppv3", "vpv3"]}, "allowed_firmware_codes": ["FAAB","FAAA", "FAAB", "EAAA", "EAAB"], "sensor_class": "calculated", "device_group": "Calculated"},
                ],
                "status": [
                    {"name": "Uptime Sensor", "type": "sensor", "unique_id": "uptime", "attributes":["status", "freeheap", "minfreeheap", "stackusage", "HA_State_MQTT", "Web_State_MQTT", "Web_Error", "HA_Error"], "sensor_class": "status", "device_group": "Inverter"},

                ],
                "timestamp": [
                    {"name": "Last Bank Update", "type": "sensor", "unique_id": "last_bank_update", "state_class": "measurement", "device_class": SensorDeviceClass.TIMESTAMP, "entity_registry_enabled_default": False, "attributes": ["inputbank1_last_update","inputbank2_last_update","inputbank3_last_update","inputbank4_last_update","inputbank5_last_update","inputbank6_last_update","holdbank1_last_update","holdbank2_last_update","holdbank3_last_update","holdbank4_last_update","holdbank5_last_update","holdbank6_last_update", "holdbank3_last_update","holdbank4_last_update", "holdbank5_last_update", "holdbank6_last_update"], "sensor_class": "timestamp", "device_group": "Inverter"},
                ],
                "powerflow": [
                    {"name": "Grid Flow Live", "type": "sensor", "unique_id": "gridflow_live", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "attribute1": "ptouser", "attribute2": "ptogrid", "sensor_class": "powerflow", "device_group": "Inverter"},
                    {"name": "Battery Flow Live", "type": "sensor", "unique_id": "batteryflow_live", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "attribute1": "pdischarge", "attribute2": "pcharge", "sensor_class": "powerflow", "device_group": "Inverter"},

                ],
                "fault": [
                    {"name": "Fault Status", "type": "sensor", "unique_id": "fault_status", "state_class": "text", "sensor_class": "fault", "device_group": "Inverter"},
                ],
                "warning": [
                    {"name": "Warning Status", "type": "sensor", "unique_id": "warning_status", "state_class": "text", "sensor_class": "warning", "device_group": "Inverter"},
                ],
                "pv": [
                    {"name": "Voltage PV1", "type": "sensor", "unique_id": "vpv1", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "PV"},
                    {"name": "Voltage PV2", "type": "sensor", "unique_id": "vpv2", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "PV"},
                    {"name": "Voltage PV3", "type": "sensor", "unique_id": "vpv3", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["FAAB","FAAA", "FAAB", "EAAA", "EAAB"], "source": "inputbank1", "device_group": "PV"},
                    {"name": "Power PV1", "type": "sensor", "unique_id": "ppv1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "PV"},
                    {"name": "Power PV2", "type": "sensor", "unique_id": "ppv2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "PV"},
                    {"name": "Power PV3", "type": "sensor", "unique_id": "ppv3", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAB","FAAA", "FAAB", "EAAA", "EAAB", "HAAA"], "source": "inputbank1", "device_group": "PV"},
                    {"name": "Pv Power", "type": "sensor", "unique_id": "ppv1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["BAAA", "BAAB"], "source": "inputbank1", "device_group": "PV"},
                    {"name": "Power PV All", "type": "sensor", "unique_id": "Pall", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "PV"},
                ],
                "battery": [
                    {"name": "Voltage Battery", "type": "sensor", "unique_id": "vbat", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "State of Charge", "type": "sensor", "unique_id": "soc", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": PERCENTAGE, "device_class": SensorDeviceClass.BATTERY, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "State of Health", "type": "sensor", "unique_id": "soh", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": PERCENTAGE, "device_class": SensorDeviceClass.BATTERY, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Power Charge", "type": "sensor", "unique_id": "pcharge", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Power Discharge", "type": "sensor", "unique_id": "pdischarge", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery BMS Status 0", "type": "sensor", "unique_id": "BatStatus0_BMS", "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery BMS Status 5", "type": "sensor", "unique_id": "BatStatus5_BMS", "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Status Aggregrate Value", "type": "sensor", "unique_id": "BatStatus_INV", "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Number Of Batteries (Parallel)", "type": "sensor", "unique_id": "BatParallelNum", "state_class": SensorStateClass.TOTAL, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Capacity (Ah)", "type": "sensor", "unique_id": "BatCapacity", "state_class": SensorStateClass.TOTAL, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Current", "type": "sensor", "unique_id": "BatCurrent_BMS", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Fault Code", "type": "sensor", "unique_id": "FaultCode_BMS", "state_class": "text", "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Warning Code", "type": "sensor", "unique_id": "WarningCode_BMS", "state_class": "text", "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Max Cell Voltage", "type": "sensor", "unique_id": "MaxCellVolt_BMS", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Min Cell Voltage", "type": "sensor", "unique_id": "MinCellVolt_BMS", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Cycle Count", "type": "sensor", "unique_id": "CycleCnt_BMS", "state_class": SensorStateClass.TOTAL, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Inverter Battery Voltage Sample", "type": "sensor", "unique_id": "BatVoltSample_INV", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Max Charge Current", "type": "sensor", "unique_id": "MaxChgCurr", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Max Discharge Current", "type": "sensor", "unique_id": "MaxDischgCurr", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Charge Voltage Ref", "type": "sensor", "unique_id": "ChargeVoltRef", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Discharge Voltage Ref", "type": "sensor", "unique_id": "DischgCutVolt", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Battery"},
                ],
                "temperature_sensors": [
                    {"name": "Internal Temperature", "type": "sensor", "unique_id": "tinner", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                    {"name": "Radiator Temperature 1", "type": "sensor", "unique_id": "tradiator1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                    {"name": "Radiator Temperature 2", "type": "sensor", "unique_id": "tradiator2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "allowed_firmware_codes": ["FAAB", "FAAA", "EAAA", "EAAB", "HAAA"], "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                    {"name": "Battery Temperature", "type": "sensor", "unique_id": "tbat", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                    {"name": "Max Cell Temperature", "type": "sensor", "unique_id": "MaxCellTemp_BMS", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                    {"name": "Min Cell Temperature", "type": "sensor", "unique_id": "MinCellTemp_BMS", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                    {"name": "Radiator T1", "type": "sensor", "unique_id": "T1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "allowed_firmware_codes": ["FAAB", "FAAA", "HAAA"], "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                    {"name": "Radiator T2", "type": "sensor", "unique_id": "T2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "allowed_firmware_codes": ["FAAB", "FAAA", "HAAA"], "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                    {"name": "Radiator T3", "type": "sensor", "unique_id": "T3", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "allowed_firmware_codes": ["FAAB", "FAAA", "HAAA"], "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                    {"name": "Radiator T4", "type": "sensor", "unique_id": "T4", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "allowed_firmware_codes": ["FAAB", "FAAA", "HAAA"], "source": "inputbank1", "sensor_class": "temperature", "device_group": "Temperature"},
                ],
                "grid": [
                    {"name": "Voltage AC R", "type": "sensor", "unique_id": "vacr", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Voltage AC S", "type": "sensor", "unique_id": "vacs", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["GAAB", "GAAA"], "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Voltage AC T", "type": "sensor", "unique_id": "vact", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["GAAB", "GAAA"], "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Frequency AC", "type": "sensor", "unique_id": "fac", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfFrequency.HERTZ, "device_class": SensorDeviceClass.FREQUENCY, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Power to Grid (live)", "type": "sensor", "unique_id": "ptogrid", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Power to User(live)", "type": "sensor", "unique_id": "ptouser", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Power Factor", "type": "sensor", "unique_id": "pf", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER_FACTOR, "unit_of_measurement": PERCENTAGE, "source": "inputbank1", "device_group": "Grid"},
                ],
                "eps": [
                    {"name": "Voltage EPS R", "type": "sensor", "unique_id": "vepsr", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "EPS"},
                    {"name": "Voltage EPS S", "type": "sensor", "unique_id": "vepss", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["GAAA", "GAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank1", "device_group": "EPS"},
                    {"name": "Voltage EPS T", "type": "sensor", "unique_id": "vepst", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["GAAA", "GAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank1", "device_group": "EPS"},
                    {"name": "Frequency EPS", "type": "sensor", "unique_id": "feps", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfFrequency.HERTZ, "device_class": SensorDeviceClass.FREQUENCY, "source": "inputbank1", "device_group": "EPS"},
                    {"name": "Power EPS", "type": "sensor", "unique_id": "peps", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "EPS"},
                    {"name": "Apparent Power EPS", "type": "sensor", "unique_id": "seps", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfApparentPower.VOLT_AMPERE , "device_class": SensorDeviceClass.APPARENT_POWER, "source": "inputbank1", "device_group": "EPS"},
                ],
                "energy_daily": [
                    {"name": "Energy PV1 Day", "type": "sensor", "unique_id": "epv1_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "Energy"},
                    {"name": "PV Energy Day", "type": "sensor", "unique_id": "epv1_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["BAAA", "BAAB"], "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy PV2 Day", "type": "sensor", "unique_id": "epv2_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy PV3 Day", "type": "sensor", "unique_id": "epv3_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["FAAB", "FAAA", "EAAA", "EAAB", "HAAA"], "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Total PV Day", "type": "sensor", "unique_id": "epv_all", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Inverter Day", "type": "sensor", "unique_id": "einv_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Rectifier Day", "type": "sensor", "unique_id": "erec_day", "state_class": SensorStateClass.TOTAL_INCREASING,"unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Charge Day", "type": "sensor", "unique_id": "echg_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Discharge Day", "type": "sensor", "unique_id": "edischg_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy EPS Day", "type": "sensor", "unique_id": "eeps_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy to Grid Day", "type": "sensor", "unique_id": "etogrid_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy to User Day", "type": "sensor", "unique_id": "etouser_day", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Of Generator Today", "type": "sensor", "unique_id": "Egen_day", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["FAAA", "FAAB", "HAAA"], "source": "inputbank1", "device_group": "Energy"},
                ],
                "energy_total": [
                    {"name": "Energy PV1 All", "type": "sensor", "unique_id": "epv1_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "Energy"},
                    {"name": "PV Energy All", "type": "sensor", "unique_id": "epv1_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["BAAA", "BAAB"], "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy PV2 All", "type": "sensor", "unique_id": "epv2_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy PV3 All", "type": "sensor", "unique_id": "epv3_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["FAAB", "FAAA", "EAAA", "EAAB", "HAAA"], "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Inverter All", "type": "sensor", "unique_id": "einv_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Rectifier All", "type": "sensor", "unique_id": "erec_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Charge All", "type": "sensor", "unique_id": "echg_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Discharge All", "type": "sensor", "unique_id": "edischg_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy EPS All", "type": "sensor", "unique_id": "eeps_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy to Grid All", "type": "sensor", "unique_id": "etogrid_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy to User All", "type": "sensor", "unique_id": "etouser_all", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Of Generator All", "type": "sensor", "unique_id": "Egen_All", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["FAAA", "FAAB", "HAAA"], "source": "inputbank1", "device_group": "Energy"},
                ],
                "inverter_info": [
                    {"name": "House Consumption (Live)", "type": "sensor", "unique_id": "pload", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "State", "type": "sensor", "unique_id": "state", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Hourly Consumption", "type": "sensor", "unique_id": "HourlyConsumption", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Daily Consumption", "type": "sensor", "unique_id": "DailyConsumption", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"], "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Working Mode", "type": "sensor", "unique_id": "statedescription", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Internal Fault", "type": "sensor", "unique_id": "internalfault", "state_class": SensorStateClass.MEASUREMENT, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Power Inverter", "type": "sensor", "unique_id": "pinv", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Power Rectifier", "type": "sensor", "unique_id": "prec", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Current Inverter RMS", "type": "sensor", "unique_id": "iinvrms", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Voltage Bus 1", "type": "sensor", "unique_id": "vbus1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Voltage Bus 2", "type": "sensor", "unique_id": "vbus2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Fault Code", "type": "sensor", "unique_id": "FaultCode", "state_class": "text", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Warning Code", "type": "sensor", "unique_id": "WarningCode", "state_class": "text", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Running Time", "type": "sensor", "unique_id": "RunningTime", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfTime.SECONDS, "device_class": SensorDeviceClass.DURATION, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Auto Test Limit", "type": "sensor", "unique_id": "wAutoTestLimit", "state_class": SensorStateClass.MEASUREMENT, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Auto Test Default Time", "type": "sensor", "unique_id": "uwAutoTestDefaultTime", "state_class": SensorStateClass.MEASUREMENT, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Auto Test Trip Value", "type": "sensor", "unique_id": "uwAutoTestTripValue", "state_class": SensorStateClass.MEASUREMENT, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Auto Test Trip Time", "type": "sensor", "unique_id": "uwAutoTestTripTime", "state_class": SensorStateClass.MEASUREMENT, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "AC Input Type", "type": "sensor", "unique_id": "ACInputType", "state_class": SensorStateClass.MEASUREMENT, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "On Grid Load Power", "type": "sensor", "unique_id": "OnGridLoadPower", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "HAAA"], "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Master or Slave Device", "type": "sensor", "unique_id": "MasterOrSlave", "state_class": "text", "source": "inputbank1", "device_group": "Inverter"},
                ],
                "gridboss_inputbank1": [
                    {"name": "GridBoss Status", "type": "sensor", "unique_id": "midboxStatus", "state_class": "text", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Grid RMS Voltage", "type": "sensor", "unique_id": "gridRMSVoltage", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "unit_of_measurement": UnitOfElectricPotential.VOLT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "BU RMS Voltage", "type": "sensor", "unique_id": "buRMSVoltage", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "unit_of_measurement": UnitOfElectricPotential.VOLT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Gen RMS Voltage", "type": "sensor", "unique_id": "genRMSVoltage", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "unit_of_measurement": UnitOfElectricPotential.VOLT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Grid L1 RMS Voltage", "type": "sensor", "unique_id": "gridL1RMSVoltage", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "unit_of_measurement": UnitOfElectricPotential.VOLT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Grid L2 RMS Voltage", "type": "sensor", "unique_id": "gridL2RMSVoltage", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "unit_of_measurement": UnitOfElectricPotential.VOLT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "BU L1 RMS Voltage", "type": "sensor", "unique_id": "buL1RMSVoltage", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "unit_of_measurement": UnitOfElectricPotential.VOLT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "BU L2 RMS Voltage", "type": "sensor", "unique_id": "buL2RMSVoltage", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "unit_of_measurement": UnitOfElectricPotential.VOLT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Gen L1 RMS Voltage", "type": "sensor", "unique_id": "genL1RMSVoltage", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "unit_of_measurement": UnitOfElectricPotential.VOLT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Gen L2 RMS Voltage", "type": "sensor", "unique_id": "genL2RMSVoltage", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "unit_of_measurement": UnitOfElectricPotential.VOLT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Grid L1 RMS Current", "type": "sensor", "unique_id": "gridL1RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Grid L2 RMS Current", "type": "sensor", "unique_id": "gridL2RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Load L1 RMS Current", "type": "sensor", "unique_id": "loadL1RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Load L2 RMS Current", "type": "sensor", "unique_id": "loadL2RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Gen L1 RMS Current", "type": "sensor", "unique_id": "genL1RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Gen L2 RMS Current", "type": "sensor", "unique_id": "genL2RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "BU L1 RMS Current", "type": "sensor", "unique_id": "buL1RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "BU L2 RMS Current", "type": "sensor", "unique_id": "buL2RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad1 L1 RMS Current", "type": "sensor", "unique_id": "smartLoad1L1RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad1 L2 RMS Current", "type": "sensor", "unique_id": "smartLoad1L2RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad2 L1 RMS Current", "type": "sensor", "unique_id": "smartLoad2L1RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad2 L2 RMS Current", "type": "sensor", "unique_id": "smartLoad2L2RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad3 L1 RMS Current", "type": "sensor", "unique_id": "smartLoad3L1RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad3 L2 RMS Current", "type": "sensor", "unique_id": "smartLoad3L2RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad4 L1 RMS Current", "type": "sensor", "unique_id": "smartLoad4L1RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad4 L2 RMS Current", "type": "sensor", "unique_id": "smartLoad4L2RMSCurrent", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Grid L1 Active Power", "type": "sensor", "unique_id": "gridL1ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Grid L2 Active Power", "type": "sensor", "unique_id": "gridL2ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Load L1 Active Power", "type": "sensor", "unique_id": "loadL1ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Load L2 Active Power", "type": "sensor", "unique_id": "loadL2ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Gen L1 Active Power", "type": "sensor", "unique_id": "genL1ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "Gen L2 Active Power", "type": "sensor", "unique_id": "genL2ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "BU L1 Active Power", "type": "sensor", "unique_id": "buL1ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "BU L2 Active Power", "type": "sensor", "unique_id": "buL2ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad1 L1 Active Power", "type": "sensor", "unique_id": "smartLoad1L1ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad1 L2 Active Power", "type": "sensor", "unique_id": "smartLoad1L2ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad2 L1 Active Power", "type": "sensor", "unique_id": "smartLoad2L1ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad2 L2 Active Power", "type": "sensor", "unique_id": "smartLoad2L2ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad3 L1 Active Power", "type": "sensor", "unique_id": "smartLoad3L1ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad3 L2 Active Power", "type": "sensor", "unique_id": "smartLoad3L2ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad4 L1 Active Power", "type": "sensor", "unique_id": "smartLoad4L1ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "SmartLoad4 L2 Active Power", "type": "sensor", "unique_id": "smartLoad4L2ActivePower", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "unit_of_measurement": UnitOfPower.WATT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E Load Today All", "type": "sensor", "unique_id": "eLoad_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E to Grid Today All", "type": "sensor", "unique_id": "EtoGrid_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E to User Today All", "type": "sensor", "unique_id": "EtoUser_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E Gen Today All", "type": "sensor", "unique_id": "Egen_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E SmartLoad1 Today All", "type": "sensor", "unique_id": "ESmartLoad1_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E SmartLoad2 Today All", "type": "sensor", "unique_id": "ESmartLoad2_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E SmartLoad3 Today All", "type": "sensor", "unique_id": "ESmartLoad3_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E SmartLoad4 Today All", "type": "sensor", "unique_id": "ESmartLoad4_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E ACcouple1 Today All", "type": "sensor", "unique_id": "EAcouple1_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E ACcouple2 Today All", "type": "sensor", "unique_id": "EAcouple2_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E ACcouple3 Today All", "type": "sensor", "unique_id": "EAcouple3_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E ACcouple4 Today All", "type": "sensor", "unique_id": "EAcouple4_TodayAll", "state_class": SensorStateClass.TOTAL_INCREASING, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E Load Total", "type": "sensor", "unique_id": "ELoad_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E BU Total", "type": "sensor", "unique_id": "EBU_Total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E to Grid Total", "type": "sensor", "unique_id": "EtoGrid_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E to User Total", "type": "sensor", "unique_id": "EtoUser_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E Gen Total", "type": "sensor", "unique_id": "Egen_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E SmartLoad1 Total", "type": "sensor", "unique_id": "ESmartLoad1_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E SmartLoad2 Total", "type": "sensor", "unique_id": "ESmartLoad2_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E SmartLoad3 Total", "type": "sensor", "unique_id": "ESmartLoad3_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E SmartLoad4 Total", "type": "sensor", "unique_id": "ESmartLoad4_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E ACcouple1 Total", "type": "sensor", "unique_id": "EAcouple1_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E ACcouple2 Total", "type": "sensor", "unique_id": "EAcouple2_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E ACcouple3 Total", "type": "sensor", "unique_id": "EAcouple3_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "E ACcouple4 Total", "type": "sensor", "unique_id": "EAcouple4_total", "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                    {"name": "MIDBox AC Type", "type": "sensor", "unique_id": "MIDBoox_ACType", "state_class": SensorStateClass.MEASUREMENT, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank1", "device_group": "GridBoss"},
                ],
                "gridboss_inputbank2": [
                    {"name": "Phase Lock Frequency", "type": "sensor", "unique_id": "PhaseLockFreq", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.FREQUENCY, "unit_of_measurement": UnitOfFrequency.HERTZ, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank2", "device_group": "GridBoss"},
                    {"name": "Grid Frequency", "type": "sensor", "unique_id": "GridFreq", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.FREQUENCY, "unit_of_measurement": UnitOfFrequency.HERTZ, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank2", "device_group": "GridBoss"},
                    {"name": "Gen Frequency", "type": "sensor", "unique_id": "GenFreq", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.FREQUENCY, "unit_of_measurement": UnitOfFrequency.HERTZ, "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank2", "device_group": "GridBoss"},
                    {"name": "Smart Port Mode", "type": "sensor", "unique_id": "SmartPortMode", "state_class": "text", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_inputbank2", "device_group": "GridBoss"},
                ],
                "inputbank2": [
                    {"name": "EPS Voltage L1N", "type": "sensor", "unique_id": "EPSVoltL1N", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "EPS Voltage L2N", "type": "sensor", "unique_id": "EPSVoltL2N", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power EPS L1N", "type": "sensor", "unique_id": "Peps_L1N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power EPS L2N", "type": "sensor", "unique_id": "Peps_L2N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Apperant Power L1N (va)", "type": "sensor", "unique_id": "Seps_L1N", "unit_of_measurement": UnitOfApparentPower.VOLT_AMPERE, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.APPARENT_POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Apperant Power L2N (va)", "type": "sensor", "unique_id": "Seps_L2N", "unit_of_measurement": UnitOfApparentPower.VOLT_AMPERE, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.APPARENT_POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Energy EPS L1N Day", "type": "sensor", "unique_id": "EepsL1N_day", "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Energy EPS L2N Day", "type": "sensor", "unique_id": "EepsL2N_day", "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Energy EPS L1N All", "type": "sensor", "unique_id": "EepsL1N_all", "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Energy EPS L2N All", "type": "sensor", "unique_id": "EepsL2N_all", "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL, "device_class": SensorDeviceClass.ENERGY, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Reactive Power (Qinv Var)", "type": "sensor", "unique_id": "Qinv", "unit_of_measurement": UnitOfApparentPower.VOLT_AMPERE, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.APPARENT_POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Arc Fault Current CH1", "type": "sensor", "unique_id": "AFCI_CurrCH1", "unit_of_measurement": UnitOfElectricCurrent.MILLIAMPERE, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Arc Fault Current CH2", "type": "sensor", "unique_id": "AFCI_CurrCH2", "unit_of_measurement": UnitOfElectricCurrent.MILLIAMPERE, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Arc Fault Current CH3", "type": "sensor", "unique_id": "AFCI_CurrCH3", "unit_of_measurement": UnitOfElectricCurrent.MILLIAMPERE, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Arc Fault Current CH4", "type": "sensor", "unique_id": "AFCI_CurrCH4", "unit_of_measurement": UnitOfElectricCurrent.MILLIAMPERE, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Realtime Arc of CH1", "type": "sensor", "unique_id": "AFCI_ArcCH1", "unit_of_measurement": UnitOfTime.SECONDS, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.DURATION, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Realtime Arc of CH2", "type": "sensor", "unique_id": "AFCI_ArcCH2", "unit_of_measurement": UnitOfTime.SECONDS, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.DURATION, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Realtime Arc of CH3", "type": "sensor", "unique_id": "AFCI_ArcCH3", "unit_of_measurement": UnitOfTime.SECONDS, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.DURATION, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Realtime Arc of CH4", "type": "sensor", "unique_id": "AFCI_ArcCH4", "unit_of_measurement": UnitOfTime.SECONDS, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.DURATION, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name":  "AC Coupled Power", "type": "sensor", "unique_id": "ACCouplePower", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Grid Voltage L1N", "type": "sensor", "unique_id": "GridVoltL1N", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Grid Voltage L2N", "type": "sensor", "unique_id": "GridVoltL2N", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Gen Voltage L1N", "type": "sensor", "unique_id": "GenVoltL1N", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Gen Voltage L2N", "type": "sensor", "unique_id": "GenVoltL2N", "unit_of_measurement": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.VOLTAGE, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power Inverter L1N", "type": "sensor", "unique_id": "PinvL1N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power Inverter L2N", "type": "sensor", "unique_id": "PinvL2N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power Rectifier L1N", "type": "sensor", "unique_id": "PrecL1N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power Rectifier L2N", "type": "sensor", "unique_id": "PrecL2N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power To Grid L1N", "type": "sensor", "unique_id": "Ptogrid_L1N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power To Grid L2N", "type": "sensor", "unique_id": "Ptogrid_L2N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power To User L1N", "type": "sensor", "unique_id": "Ptouser_L1N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},
                    {"name": "Power To User L2N", "type": "sensor", "unique_id": "Ptouser_L2N", "unit_of_measurement": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.POWER, "allowed_firmware_codes": ["FAAA", "FAAB", "ccaa", "ceaa"], "source": "inputbank2", "device_group": "Inverter"},

                ],
                "holdbank1" : [
                    {"name": "FWCode", "type": "sensor", "unique_id": "FWCode", "source": "holdbank1", "device_group": "Inverter"},
                    {"name": "Slave Version", "type": "sensor", "unique_id": "SlaveVer", "state_class": "text", "source": "holdbank1", "device_group": "Inverter"},
                    {"name": "Com Version", "type": "sensor", "unique_id": "ComVer", "state_class": "text", "source": "holdbank1", "device_group": "Inverter"},
                    {"name": "Control Version", "type": "sensor", "unique_id": "CntlVer", "state_class": "text", "source": "holdbank1", "device_group": "Inverter"},
                    {"name": "FW Version", "type": "sensor", "unique_id": "FWVer", "state_class": "text", "source": "holdbank1", "device_group": "Inverter"},

                ],
            },
            "switch": {
                "holdbank1": [
                    {"name": "Restart Inverter", "type": "switch", "unique_id": "ResetSetting", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "EPS", "type": "switch", "unique_id": "EPS", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Ground neutral detectionenable", "type": "switch", "unique_id": "NeutralDetect", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "AC Charge", "type": "switch", "unique_id": "ACCharge", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "seamless off-grid mode switching ", "type": "switch", "unique_id": "SWSeamlessly", "source": "holdbank1", "device_group": "Controls"},
                    {"name":"Standby Switch", "type": "switch", "unique_id": "SetToStandby", "source": "holdbank1", "device_group": "Controls"},
                    {"name":"Force Discharge", "type": "switch", "unique_id": "ForcedDischg", "source": "holdbank1", "device_group": "Controls"},
                    {"name":"Charge Priority", "type": "switch", "unique_id": "ForcedChg", "source": "holdbank1", "device_group": "Controls"},
                    {"name":"Export Allowed", "type": "switch", "unique_id": "FeedInGrid", "source": "holdbank1", "device_group": "Controls"},
                ],
                "gridboss_holdbank1": [
                    {"name": "Generator Enable", "type": "switch", "unique_id": "Generator_enable", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Enable", "type": "switch", "unique_id": "SmartLoad1_Enable", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Enable", "type": "switch", "unique_id": "SmartLoad2_Enable", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Enable", "type": "switch", "unique_id": "SmartLoad3_Enable", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Enable", "type": "switch", "unique_id": "SmartLoad4_Enable", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Grid On", "type": "switch", "unique_id": "SmartLoad1_GridOn", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Grid On", "type": "switch", "unique_id": "SmartLoad2_GridOn", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Grid On", "type": "switch", "unique_id": "SmartLoad3_GridOn", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Grid On", "type": "switch", "unique_id": "SmartLoad4_GridOn", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 Enable", "type": "switch", "unique_id": "ACcouple1_Enable", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 Enable", "type": "switch", "unique_id": "ACcouple2_Enable", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 Enable", "type": "switch", "unique_id": "ACcouple3_Enable", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 Enable", "type": "switch", "unique_id": "ACcouple4_Enable", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Shedding", "type": "switch", "unique_id": "SmartLoad1_Shedding", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Shedding", "type": "switch", "unique_id": "SmartLoad2_Shedding", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Shedding", "type": "switch", "unique_id": "SmartLoad3_Shedding", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Shedding", "type": "switch", "unique_id": "SmartLoad4_Shedding", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                ],
                "holdbank3": [
                    {"name": "PV Grid Off", "type": "switch", "unique_id": "ubPVGridOffEn", "source": "holdbank3"}, #"allowed_firmware_codes": ["A", "B", "E", "F", "G"], "device_group": "Controls"},
                    {"name": "Fast Zero Export", "type": "switch", "unique_id": "ubFastZeroExport", "source": "holdbank3"}, #"allowed_firmware_codes": ["A", "B", "E", "F", "G"], "device_group": "Controls"},
                    {"name": "Micro Grid On", "type": "switch", "unique_id": "ubMicroGridEn", "source": "holdbank3"}, #"allowed_firmware_codes": ["A", "B", "E", "F", "G"], "device_group": "Controls"},
                    {"name": "Battery Shared", "type": "switch", "unique_id": "ubBatShared", "source": "holdbank3"}, #"allowed_firmware_codes": ["A", "B", "E", "F", "G"], "device_group": "Controls"},
                    {"name": "Charge Last", "type": "switch", "unique_id": "ubChgLastEn", "source": "holdbank3"}, #"allowed_firmware_codes": ["A", "B", "E", "F", "G"], "device_group": "Controls"},
                    {"name": "Take Load Together", "type": "switch", "unique_id": "TakeLoadTogether", "source": "holdbank3", "device_group": "Controls"},
                ],
                "holdbank4": [
                    {"name": "Half hour charge Switch", "type": "switch", "unique_id": "HalfHourACChrStartEn", "source": "holdbank4", "device_group": "Controls"},
                ],
            },
            "binary_sensor": {  # This should be the only place defining these sensors
                "battery": [  # Only one bank for battery sensors
                    {"name": "Battery Charge",
                    "type": "binary_sensor",
                    "unique_id": "battery_charge_status",
                    "parent_sensor": "batstatus_inv",
                    "status_type": "charge", "source": "battery", "sensor_class": "battery"},
                    {"name": "Battery Discharge",
                    "type": "binary_sensor",
                    "unique_id": "battery_discharge_status",
                    "parent_sensor": "batstatus_inv",
                    "status_type": "discharge", "source": "battery", "sensor_class": "battery"}
                ]
            },
            "number": {
                "holdbank2": [
                    {"name": "Active Power", "type": "number", "unique_id": "ActivePowerPercentCMD", "unit": "%", "min": 0, "max": 100 , "mode": "slider", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "Charge Power Rate", "type": "number", "unique_id": "ChargePowerPercentCMD", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank2", "device_group": "Controls", "allowed_firmware_codes": ["AAAA", "AAAB","BAAA", "BAAB"]},
                    {"name": "Discharge Power Rate", "type": "number", "unique_id": "DischgPowerPercentCMD", "unit": "%", "min": 0, "max": 100 , "mode": "slider", "source": "holdbank2", "device_group": "Controls", "allowed_firmware_codes": ["AAAA", "AAAB","BAAA", "BAAB"]},
                    {"name": "AC Charge Rate", "type": "number", "unique_id": "ACChgPowerCMD", "unit": "kW", "min": 0, "max": 24, "mode": "slider", "source": "holdbank2", "device_group": "Controls", "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "ceaa", "HAAA"]},
                    {"name": "AC Charge SOC Limit", "type": "number", "unique_id": "ACChgSOCLimit", "unit": "%", "min": 0, "max": 100, "mode": "slider", "class": "BATTERY", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "Charge First Rate", "type": "number", "unique_id": "ChgFirstPowerCMD", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "Charge First SOC Limit", "type": "number", "unique_id": "ChgFirstSOCLimit", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank2", "device_group": "Controls"},
                ],
                "gridboss_holdbank2": [
                    {"name": "Generator Warmup Time", "type": "number", "unique_id": "Generator_Warmup", "unit": "s", "min": 0, "max": 600, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "Generator Cool Down Time", "type": "number", "unique_id": "Generator_CoolDown", "unit": "s", "min": 0, "max": 600, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "Generator Exercise Period", "type": "number", "unique_id": "Generator_Exercise_Period", "unit": "d", "min": 0, "max": 365, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Start SOC", "type": "number", "unique_id": "SmartLoad1_StartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 End SOC", "type": "number", "unique_id": "SmartLoad1_EndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Start SOC", "type": "number", "unique_id": "SmartLoad2_StartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 End SOC", "type": "number", "unique_id": "SmartLoad2_EndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Start SOC", "type": "number", "unique_id": "SmartLoad3_StartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 End SOC", "type": "number", "unique_id": "SmartLoad3_EndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Start SOC", "type": "number", "unique_id": "SmartLoad4_StartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 End SOC", "type": "number", "unique_id": "SmartLoad4_EndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Start Voltage", "type": "number", "unique_id": "SmartLoad1_StartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 End Voltage", "type": "number", "unique_id": "SmartLoad1_EndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Start Voltage", "type": "number", "unique_id": "SmartLoad2_StartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 End Voltage", "type": "number", "unique_id": "SmartLoad2_EndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Start Voltage", "type": "number", "unique_id": "SmartLoad3_StartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 End Voltage", "type": "number", "unique_id": "SmartLoad3_EndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Start Voltage", "type": "number", "unique_id": "SmartLoad4_StartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 End Voltage", "type": "number", "unique_id": "SmartLoad4_EndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 Start SOC", "type": "number", "unique_id": "ACcouple1_StartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 End SOC", "type": "number", "unique_id": "ACcouple1_EndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 Start SOC", "type": "number", "unique_id": "ACcouple2_StartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 End SOC", "type": "number", "unique_id": "ACcouple2_EndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 Start SOC", "type": "number", "unique_id": "ACcouple3_StartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 End SOC", "type": "number", "unique_id": "ACcouple3_EndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 Start SOC", "type": "number", "unique_id": "ACcouple4_StartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 End SOC", "type": "number", "unique_id": "ACcouple4_EndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 Start Voltage", "type": "number", "unique_id": "ACcouple1_StartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 End Voltage", "type": "number", "unique_id": "ACcouple1_EndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 Start Voltage", "type": "number", "unique_id": "ACcouple2_StartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 End Voltage", "type": "number", "unique_id": "ACcouple2_EndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 Start Voltage", "type": "number", "unique_id": "ACcouple3_StartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 End Voltage", "type": "number", "unique_id": "ACcouple3_EndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 Start Voltage", "type": "number", "unique_id": "ACcouple4_StartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 End Voltage", "type": "number", "unique_id": "ACcouple4_EndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Shedding Start PV Power", "type": "number", "unique_id": "SmartLoad1_SheddingStartPv_Power", "unit": "W", "min": 0, "max": 10000, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Shedding Start PV Power", "type": "number", "unique_id": "SmartLoad2_SheddingStartPv_Power", "unit": "W", "min": 0, "max": 10000, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Shedding Start PV Power", "type": "number", "unique_id": "SmartLoad3_SheddingStartPv_Power", "unit": "W", "min": 0, "max": 10000, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Shedding Start PV Power", "type": "number", "unique_id": "SmartLoad4_SheddingStartPv_Power", "unit": "W", "min": 0, "max": 10000, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Shedding Start SOC", "type": "number", "unique_id": "SmartLoad1_SheddingStartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Shedding End SOC", "type": "number", "unique_id": "SmartLoad1_SheddingEndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Shedding Start SOC", "type": "number", "unique_id": "SmartLoad2_SheddingStartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Shedding End SOC", "type": "number", "unique_id": "SmartLoad2_SheddingEndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Shedding Start SOC", "type": "number", "unique_id": "SmartLoad3_SheddingStartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Shedding End SOC", "type": "number", "unique_id": "SmartLoad3_SheddingEndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Shedding Start SOC", "type": "number", "unique_id": "SmartLoad4_SheddingStartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Shedding End SOC", "type": "number", "unique_id": "SmartLoad4_SheddingEndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Shedding Start Voltage", "type": "number", "unique_id": "SmartLoad1_SheddingStartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Shedding End Voltage", "type": "number", "unique_id": "SmartLoad1_SheddingEndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Shedding Start Voltage", "type": "number", "unique_id": "SmartLoad2_SheddingStartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Shedding End Voltage", "type": "number", "unique_id": "SmartLoad2_SheddingEndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Shedding Start Voltage", "type": "number", "unique_id": "SmartLoad3_SheddingStartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Shedding End Voltage", "type": "number", "unique_id": "SmartLoad3_SheddingEndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Shedding Start Voltage", "type": "number", "unique_id": "SmartLoad4_SheddingStartVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Shedding End Voltage", "type": "number", "unique_id": "SmartLoad4_SheddingEndVolt", "unit": "V", "min": 40, "max": 60, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "Flash 50/60Hz", "type": "number", "unique_id": "Flash_5060hz", "unit": "", "min": 0, "max": 1, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                    {"name": "NEC 120 Current Limit", "type": "number", "unique_id": "NEC_120CurrLimit", "unit": "A", "min": 0, "max": 200, "mode": "slider", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank2", "device_group": "GridBoss Controls"},
                ],
                "holdbank3": [
                    {"name": "Force Discharge Power Rate", "type": "number", "unique_id": "ForcedDischgPowerCMD", "unit": "kW", "min": 0, "max": 24 , "mode": "slider", "source": "holdbank3", "allowed_firmware_codes": ["FAAA", "FAAB", "EAAA", "EAAB", "HAAA"]},
                    {"name": "Force Discharge SOC Limit", "type": "number", "unique_id": "ForcedDischgSOCLimit", "unit": "%", "min": 0, "max": 100 , "mode": "slider", "source": "holdbank3"},
                    {"name": "Lead acid Charge Rate (A)", "type": "number", "unique_id": "ChargeRate", "unit": "A", "min": 0, "max": 140, "firmware_max_values": {"FAAA": 250, "FAAB": 250, "EAAA": 195, "EAAB": 195, "HAAA": 195, "ccaa": 250, "ceaa": 250, "AAAA": 78, "AAAB": 78, "BAAA": 78, "BAAB": 78}, "mode": "slider", "native_unit": "A", "class": "CURRENT", "source": "holdbank3"},
                    {"name": "Lead Acid Discharge Rate (A)", "type": "number", "unique_id": "DischgRate", "unit": "A", "min": 0, "max": 140, "firmware_max_values": {"FAAA": 250, "FAAB": 250, "EAAA": 195, "EAAB": 195, "HAAA": 195, "ccaa": 250, "ceaa": 250, "AAAA": 78, "AAAB": 78, "BAAA": 78, "BAAB": 78}, "mode": "slider", "native_unit": "A", "class": "CURRENT", "source": "holdbank3"},
                    {"name": "Battery Discharge Start Point (W)", "type": "number", "unique_id": "PtoUserStartdischg", "unit": "W", "min": 1, "max": 500 , "mode": "slider", "native_unit": "W", "class": "POWER", "source": "holdbank3"},
                    {"name": "Battery Charge Start Point (W)", "type": "number", "unique_id": "PtoUserStartchg", "unit": "W", "min": -50, "max": 1, "mode": "slider", "native_unit": "W", "class": "POWER", "source": "holdbank3"},
                    {"name": "CT Offset (W)", "type": "number", "unique_id": "wCT_PowerOffset", "unit": "W", "min": -1000, "max": 1000 , "mode": "slider", "native_unit": "W", "class": "POWER", "source": "holdbank3"},
                    {"name": "Export Power (%)", "type": "number", "unique_id": "MaxBackFlow", "unit": "W", "min": 0, "max": 200 , "mode": "slider", "source": "holdbank3"},
                    {"name": "On-grid Discharge Cut-off SOC Limit", "type": "number", "unique_id": "EOD", "unit": "%", "min": 0, "max": 90, "mode": "slider", "source": "holdbank3"},
                    {"name": "Off-grid Battery Voltage Cut off", "type": "number", "unique_id": "CutVoltForDischg", "unit": "V", "min": 40, "max": 56, "mode": "slider", "source": "holdbank3"},
                    {"name": "Charge Current DC(A)", "type": "number", "unique_id": "ChargeCurr", "unit": "A", "min": 0, "max": 140, "firmware_max_values": {"FAAA": 250, "FAAB": 250, "EAAA": 195, "EAAB": 195, "HAAA": 195, "ccaa": 250, "ceaa": 250, "AAAA": 78, "AAAB": 78, "BAAA": 78, "BAAB": 78}, "mode": "slider", "native_unit": "A", "class": "CURRENT", "source": "holdbank3"},
                    {"name": "Discharge Current DC(A)", "type": "number", "unique_id": "DischgCurr", "unit": "A", "min": 0, "max": 140, "firmware_max_values": {"FAAA": 250, "FAAB": 250, "EAAA": 195, "EAAB": 195, "HAAA": 195, "ccaa": 250, "ceaa": 250, "AAAA": 78, "AAAB": 78, "BAAA": 78, "BAAB": 78}, "mode": "slider", "native_unit": "A", "class": "CURRENT", "source": "holdbank3"},
                ],
                "holdbank4": [
                    {"name": "Off-grid Discharge Cut-off SOC Limit", "type": "number", "unique_id": "SOCLowLimitForESPSDischg", "unit": "%", "min": 0, "max": 90, "mode": "slider", "source": "holdbank4"},
                    {"name": "AC Charge Start (SOC)", "type": "number", "unique_id": "ACChgStartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank4"},
                    {"name": "AC Charge Start (Voltage)", "type": "number", "unique_id": "ACChgStartVolt", "step": 0.1, "unit": "V", "min": 38.5, "max": 52, "mode": "slider", "source": "holdbank4", "mqtt_multiplier": 10},
                    {"name": "AC Charge End (Voltage)", "type": "number", "unique_id": "ACChgEndVolt", "step": 0.1, "unit": "V", "min": 48, "max": 59, "mode": "slider", "source": "holdbank4", "mqtt_multiplier": 10},
                    {"name": "Max Grid Input Power", "type": "number", "unique_id": "MaxGridInputPower", "unit": "kW", "min": 0, "max": 24, "mode": "slider", "step": 0.1, "source": "holdbank4"},
                    {"name": "Generator Ratied Input Power", "type": "number", "unique_id": "GenRatePower", "unit": "kW", "min": 0, "max": 24, "mode": "slider", "step": 0.1, "allowed_firmware_codes": ["HAAA", "FAAA", "FAAB", "ccaa", "ceaa"], "source": "holdbank4"},
                    {"name": "Generator Charge Start Voltage", "type": "number", "unique_id": "GenChgStartVolt", "unit": "V", "min": 40, "max": 56, "mode": "slider", "step": 0.1, "allowed_firmware_codes": ["HAAA", "FAAA", "FAAB", "ccaa", "ceaa"], "source": "holdbank4", "mqtt_multiplier": 10},
                    {"name": "Generator Charge End Voltage", "type": "number", "unique_id": "GenChgEndVolt", "unit": "V", "min": 50, "max": 60, "mode": "slider", "step": 0.1, "allowed_firmware_codes": ["HAAA", "FAAA", "FAAB", "ccaa", "ceaa"], "source": "holdbank4", "mqtt_multiplier": 10},
                    {"name": "Generator Charge Start SOC", "type": "number", "unique_id": "GenChgStartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "step": 1, "allowed_firmware_codes": ["HAAA", "FAAA", "FAAB", "ccaa", "ceaa"], "source": "holdbank4"},
                    {"name": "Generator Charge End SOC", "type": "number", "unique_id": "GenChgEndSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "step": 1, "allowed_firmware_codes": ["HAAA", "FAAA", "FAAB", "ccaa", "ceaa"], "source": "holdbank4"},
                    {"name": "Max Generator Charge Battery Current", "type": "number", "unique_id": "MaxGenChgBatCurr", "unit": "A", "min": 0, "max": 140, "firmware_max_values": {"FAAA": 250, "FAAB": 250, "HAAA": 195, "ccaa": 250, "ceaa": 250}, "mode": "slider", "step": 1, "allowed_firmware_codes": ["HAAA", "FAAA", "FAAB", "ccaa", "ceaa"], "source": "holdbank4"},
                    {"name": "Generator Charge Start Current", "type": "number", "unique_id": "GenChgStartCurr", "unit": "A", "min": 0, "max": 140, "firmware_max_values": {"FAAA": 250, "FAAB": 250, "HAAA": 195, "ccaa": 250, "ceaa": 250}, "mode": "slider", "step": 1, "allowed_firmware_codes": ["HAAA", "FAAA", "FAAB", "ccaa", "ceaa"], "source": "holdbank4"}

                ],
                "holdbank5": [
                    {"name": "On Grid Battery Voltage Cut off", "type": "number", "unique_id": "OngridEOD_Voltage", "unit": "V", "min": 40, "max": 56, "mode": "slider", "mqtt_multiplier": 10}
                ],
                "holdbank6": [
                    {"name": "System Charge SOC Limit %", "type": "number", "unique_id": "BatStopChgSOC", "unit": "%", "min": 0, "max": 101, "mode": "slider", "allowed_firmware_codes": ["HAAA", "FAAA", "FAAB", "ccaa", "ceaa"], "source": "holdbank6"},
                    {"name": "System Charge Volt limit (v)", "type": "number", "unique_id": "BatStopChgVolt", "unit": "V", "min": 40, "max": 56, "mode": "slider", "allowed_firmware_codes": ["HAAA", "FAAA", "FAAB", "ccaa", "ceaa"], "source": "holdbank6"},
                    {"name": "Stop Dischage (Voltage)", "type": "number", "unique_id": "ForceDichgEndVolt", "unit": "V", "min": 40, "max": 56, "mode": "slider", "source": "holdbank6", "mqtt_multiplier": 10},
                ],
            },
            "select": {
                "holdbank3": [
                    {"name": "CT Sample Ratio", "type": "select", "unique_id": "CTSampleRatio", "options": ["1:1000", "1:3000"], "source": "holdbank3", "device_group": "Controls"},
                    {"name": "Clear Parallel Alarm", "type": "select", "unique_id": "ClearParallelAlarm", "options": ["N/A", "Clear" ], "source": "holdbank3", "device_group": "Controls"},


                ],
                "holdbank4": [
                    {"name": "Charge Based on:", "type": "select", "unique_id": "ACChargeType", "options": ["Disabled", "Time According To", "According To Voltage", "According To SOC", "According To Time and Voltage", "According To Time and SOC"], "allowed_firmware_codes": ["AAAA", "AAAB", "BAAA", "BAAB","ccaa","EAAA", "EAAB","ceaa"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "Charge Based on:", "type": "select", "unique_id": "ACChargeType", "options": ["According To Time", "According To SOC/VOLT", "According To Time and SOC/VOLT"], "allowed_firmware_codes": ["FAAB","FAAA", "HAAA"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "00:00 -- 00:30", "type": "select", "unique_id": "Time0", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "00:30 -- 01:00", "type": "select", "unique_id": "Time1", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "01:00 -- 01:30", "type": "select", "unique_id": "Time2", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "01:30 -- 02:00", "type": "select", "unique_id": "Time3", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "02:00 -- 02:30", "type": "select", "unique_id": "Time4", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "02:30 -- 03:00", "type": "select", "unique_id": "Time5", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "03:00 -- 03:30", "type": "select", "unique_id": "Time6", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "03:30 -- 04:00", "type": "select", "unique_id": "Time7", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "04:00 -- 04:30", "type": "select", "unique_id": "Time8", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "04:30 -- 05:00", "type": "select", "unique_id": "Time9", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "05:00 -- 05:30", "type": "select", "unique_id": "Time10", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "05:30 -- 06:00", "type": "select", "unique_id": "Time11", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "06:00 -- 06:30", "type": "select", "unique_id": "Time12", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "06:30 -- 07:00", "type": "select", "unique_id": "Time13", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "07:00 -- 07:30", "type": "select", "unique_id": "Time14", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "07:30 -- 08:00", "type": "select", "unique_id": "Time15", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "08:00 -- 08:30", "type": "select", "unique_id": "Time16", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "08:30 -- 09:00", "type": "select", "unique_id": "Time17", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "09:00 -- 09:30", "type": "select", "unique_id": "Time18", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "09:30 -- 10:00", "type": "select", "unique_id": "Time19", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "10:00 -- 10:30", "type": "select", "unique_id": "Time20", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "10:30 -- 11:00", "type": "select", "unique_id": "Time21", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "11:00 -- 11:30", "type": "select", "unique_id": "Time22", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "11:30 -- 12:00", "type": "select", "unique_id": "Time23", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "12:00 -- 12:30", "type": "select", "unique_id": "Time24", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "12:30 -- 13:00", "type": "select", "unique_id": "Time25", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "13:00 -- 13:30", "type": "select", "unique_id": "Time26", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "13:30 -- 14:00", "type": "select", "unique_id": "Time27", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "14:00 -- 14:30", "type": "select", "unique_id": "Time28", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "14:30 -- 15:00", "type": "select", "unique_id": "Time29", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "15:00 -- 15:30", "type": "select", "unique_id": "Time30", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "15:30 -- 16:00", "type": "select", "unique_id": "Time31", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "16:00 -- 16:30", "type": "select", "unique_id": "Time32", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "16:30 -- 17:00", "type": "select", "unique_id": "Time33", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "17:00 -- 17:30", "type": "select", "unique_id": "Time34", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "17:30 -- 18:00", "type": "select", "unique_id": "Time35", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "18:00 -- 18:30", "type": "select", "unique_id": "Time36", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "18:30 -- 19:00", "type": "select", "unique_id": "Time37", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "19:00 -- 19:30", "type": "select", "unique_id": "Time38", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "19:30 -- 20:00", "type": "select", "unique_id": "Time39", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "20:00 -- 20:30", "type": "select", "unique_id": "Time40", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "20:30 -- 21:00", "type": "select", "unique_id": "Time41", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "21:00 -- 21:30", "type": "select", "unique_id": "Time42", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "21:30 -- 22:00", "type": "select", "unique_id": "Time43", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "22:00 -- 22:30", "type": "select", "unique_id": "Time44", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "22:30 -- 23:00", "type": "select", "unique_id": "Time45", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "23:00 -- 23:30", "type": "select", "unique_id": "Time46", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},
                    {"name": "23:30 -- 24:00", "type": "select", "unique_id": "Time47", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"], "source": "holdbank4", "device_group": "Controls"},

                    # Add more selects as needed
                ],
                "holdbank5": [
                    {"name": "Charge Control", "type": "select", "unique_id": "ubBatChgcontrol", "options": ["SOC", "Voltage"], "allowed_firmware_codes": ["AAAA", "AAAB", "BAAA", "BAAB","EAAA", "EAAB","HAAA","FAAB","FAAA"], "source": "holdbank5", "device_group": "Controls"},
                    {"name": "Discharge Control", "type": "select", "unique_id": "ubBatDischgControl", "options": ["SOC", "Voltage"], "source": "holdbank5", "device_group": "Controls"},
                ],
                "holdbank6": [
                    {"name": "Quick Charge Duration", "type": "select", "unique_id": "quickchgtime", "options": ["0", "15", "30", "45", "60", "90", "120"], "additional_payload": {"key": "ubquickchgstarten","value_map": {"0": "0","default": "1"}}, "source": "holdbank6", "sensor_class": "holdbank6", "device_group": "Controls"},

                ],
                "gridboss_holdbank1": [
                    {"name": "Smart Port 1", "type": "select", "unique_id": "SmartLoad1_PortMode", "options": ["Does Not Operate", "Smart Load", "Ac Coupled"], "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "Smart Port 2", "type": "select", "unique_id": "SmartLoad2_PortMode", "options": ["Does Not Operate", "Smart Load", "Ac Coupled"], "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "Smart Port 3", "type": "select", "unique_id": "SmartLoad3_PortMode", "options": ["Does Not Operate", "Smart Load", "Ac Coupled"], "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "Smart Port 4", "type": "select", "unique_id": "SmartLoad4_PortMode", "options": ["Does Not Operate", "Smart Load", "Ac Coupled"], "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "Smart Load 1 Mode", "type": "select", "unique_id": "SmartLoad1_SOC_Volt", "options": ["Time", "SOC/Volt"], "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "Smart Load 2 Mode", "type": "select", "unique_id": "SmartLoad2_SOC_Volt", "options": ["Time", "SOC/Volt"], "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "Smart Load 3 Mode", "type": "select", "unique_id": "SmartLoad3_SOC_Volt", "options": ["Time", "SOC/Volt"], "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                    {"name": "Smart Load 4 Mode", "type": "select", "unique_id": "SmartLoad4_SOC_Volt", "options": ["Time", "SOC/Volt"], "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank1", "device_group": "GridBoss Controls"},
                ]
            },
            "button": {
                "inputbank1": [
                    {"name": "Dongle Firmware Update", "type": "button", "unique_id": "firmware_update_button", "source": "inputbank1", "sensor_class": "firmware_update", "device_group": "Inverter"},
                ],
                "restart": [
                    {"name": "Restart Inverter", "type": "button", "unique_id": "INVReboot", "source": "restart", "sensor_class": "restart", "device_group": "Controls"},
                ],
            },

            "time": {
                "holdbank2": [
                    {"name": "AC Charge Start", "type": "time", "unique_id": "ACChgStart", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "AC Charge End", "type": "time", "unique_id": "ACChgEnd", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "AC Charge Start1", "type": "time", "unique_id": "ACChgStart1", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "AC Charge End1", "type": "time", "unique_id": "ACChgEnd1", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "AC Charge Start2", "type": "time", "unique_id": "ACChgStart2", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "AC Charge End2", "type": "time", "unique_id": "ACChgEnd2", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "Charge Priority Start", "type": "time", "unique_id": "ChgFirstStart", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "Charge Priority End", "type": "time", "unique_id": "ChgFirstEnd", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "Charge Priority Start1", "type": "time", "unique_id": "ChgFirstStart1", "source": "holdbank2", "device_group": "Controls"},
                    {"name": "Charge Priority End1", "type": "time", "unique_id": "ChgFirstEnd1", "source": "holdbank2", "device_group": "Controls"},
                ],
                "holdbank3": [
                    {"name": "Charge Priority Start2", "type": "time", "unique_id": "ChgFirstStart2", "source": "holdbank3", "device_group": "Controls"},
                    {"name": "Charge Priority End2", "type": "time", "unique_id": "ChgFirstEnd2", "source": "holdbank3", "device_group": "Controls"},
                    {"name": "Force Discharge Start", "type": "time", "unique_id": "ForcedDischgStart", "source": "holdbank3", "device_group": "Controls"},
                    {"name": "Force Discharge End", "type": "time", "unique_id": "ForcedDischgEnd", "source": "holdbank3", "device_group": "Controls"},
                    {"name": "Force Discharge Start1", "type": "time", "unique_id": "ForcedDischgStart1", "source": "holdbank3", "device_group": "Controls"},
                    {"name": "Force Discharge End1", "type": "time", "unique_id": "ForcedDischgEnd1", "source": "holdbank3", "device_group": "Controls"},
                    {"name": "Force Discharge Start2", "type": "time", "unique_id": "ForcedDischgStart2", "source": "holdbank3", "device_group": "Controls"},
                    {"name": "Force Discharge End2", "type": "time", "unique_id": "ForcedDischgEnd2", "source": "holdbank3", "device_group": "Controls"},
                ],
                "gridboss_holdbank3": [
                    {"name": "SmartLoad1 Start0", "type": "time", "unique_id": "SmartLoad1Start0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 End0", "type": "time", "unique_id": "SmartLoad1End0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Start1", "type": "time", "unique_id": "SmartLoad1Start1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 End1", "type": "time", "unique_id": "SmartLoad1End1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 Start2", "type": "time", "unique_id": "SmartLoad1Start2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad1 End2", "type": "time", "unique_id": "SmartLoad1End2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Start0", "type": "time", "unique_id": "SmartLoad2Start0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 End0", "type": "time", "unique_id": "SmartLoad2End0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Start1", "type": "time", "unique_id": "SmartLoad2Start1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 End1", "type": "time", "unique_id": "SmartLoad2End1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 Start2", "type": "time", "unique_id": "SmartLoad2Start2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad2 End2", "type": "time", "unique_id": "SmartLoad2End2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Start0", "type": "time", "unique_id": "SmartLoad3Start0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 End0", "type": "time", "unique_id": "SmartLoad3End0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Start1", "type": "time", "unique_id": "SmartLoad3Start1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 End1", "type": "time", "unique_id": "SmartLoad3End1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 Start2", "type": "time", "unique_id": "SmartLoad3Start2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad3 End2", "type": "time", "unique_id": "SmartLoad3End2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Start0", "type": "time", "unique_id": "SmartLoad4Start0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 End0", "type": "time", "unique_id": "SmartLoad4End0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Start1", "type": "time", "unique_id": "SmartLoad4Start1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 End1", "type": "time", "unique_id": "SmartLoad4End1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 Start2", "type": "time", "unique_id": "SmartLoad4Start2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "SmartLoad4 End2", "type": "time", "unique_id": "SmartLoad4End2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 Start0", "type": "time", "unique_id": "ACcouple1Start0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 End0", "type": "time", "unique_id": "ACcouple1End0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 Start1", "type": "time", "unique_id": "ACcouple1Start1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 End1", "type": "time", "unique_id": "ACcouple1End1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 Start2", "type": "time", "unique_id": "ACcouple1Start2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple1 End2", "type": "time", "unique_id": "ACcouple1End2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 Start0", "type": "time", "unique_id": "ACcouple2Start0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 End0", "type": "time", "unique_id": "ACcouple2End0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 Start1", "type": "time", "unique_id": "ACcouple2Start1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 End1", "type": "time", "unique_id": "ACcouple2End1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 Start2", "type": "time", "unique_id": "ACcouple2Start2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple2 End2", "type": "time", "unique_id": "ACcouple2End2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 Start0", "type": "time", "unique_id": "ACcouple3Start0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 End0", "type": "time", "unique_id": "ACcouple3End0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 Start1", "type": "time", "unique_id": "ACcouple3Start1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 End1", "type": "time", "unique_id": "ACcouple3End1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 Start2", "type": "time", "unique_id": "ACcouple3Start2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple3 End2", "type": "time", "unique_id": "ACcouple3End2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 Start0", "type": "time", "unique_id": "ACcouple4Start0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 End0", "type": "time", "unique_id": "ACcouple4End0", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 Start1", "type": "time", "unique_id": "ACcouple4Start1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 End1", "type": "time", "unique_id": "ACcouple4End1", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 Start2", "type": "time", "unique_id": "ACcouple4Start2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                    {"name": "ACcouple4 End2", "type": "time", "unique_id": "ACcouple4End2", "allowed_firmware_codes": ["IAAB"], "source": "gridboss_holdbank3", "device_group": "GridBoss Controls"},
                ],
            },
            "calculated": [
                    {"name": "Battery Time to Empty", "type": "sensor", "unique_id": "battery_time_empty", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.DURATION, "unit_of_measurement": UnitOfTime.HOURS, "calculation": {"operation": "battery_time", "sensors": ["batcapacity", "vbat", "pload", "peps", "batteryflow_live", "soc", "pall"], "attributes": ["calculated_kwh_storage_total", "calculated_kwh_left", "time_battery_empty", "human_readable_time_left"]}},
                    {"name": "PV1 Current", "type": "sensor", "unique_id": "ipv1", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "calculation": {"operation": "division", "sensors": ["ppv1", "vpv1"]}, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"]},
                    {"name": "PV2 Current", "type": "sensor", "unique_id": "ipv2", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "calculation": {"operation": "division", "sensors": ["ppv2", "vpv2"]}, "allowed_firmware_codes": ["AAAA", "AAAB", "FAAA", "FAAB", "EAAA", "EAAB", "ccaa", "HAAA", "ceaa"]},
                    {"name": "PV3 Current", "type": "sensor", "unique_id": "ipv3", "state_class": SensorStateClass.MEASUREMENT, "device_class": SensorDeviceClass.CURRENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "calculation": {"operation": "division", "sensors": ["ppv3", "vpv3"]}, "allowed_firmware_codes": ["FAAB","FAAA", "FAAB", "EAAA", "EAAB", "HAAA","ceaa"]},
                ],
            "update": {
                 "system": [
                     {
                         "name": "Firmware Update",
                         "type": "update", 
                         "unique_id": "firmware_update",
                         "version_key": "SW_VERSION",
                         "update_command": "updatedongle",
                         "allowed_firmware_codes": ["IAAB", "AAAA", "AAAB", "BAAA", "BAAB", "ccaa", "FAAB", "FAAA", "EAAA", "EAAB", "HAAA", "ceaa"]
                     }
                 ]
             }
        },

        # =====================================================================
        # Deye / SunSynk / SolArk / NeoVolta family.
        #
        # The dongle emits this family's data via the generated Deye register
        # catalog (deye_catalog_GENERATED.h -> build_deye_input_payload /
        # build_deye_hold_payload in unified_emit.c). Every `unique_id` below
        # MATCHES THE CATALOG KEY EXACTLY (case-sensitive on the wire; the
        # coordinator lowercases both sides when matching, so case is
        # cosmetic for routing but kept identical to the catalog for clarity).
        #
        # `source` values use the standard "inputbank1"/"holdbank1" labels so
        # the GridBoss gating in _create_entities_for_dongle (source.startswith
        # "gridboss_") treats every Deye entity as a normal inverter entity.
        # Under unified /input + /hold topics the source string is otherwise
        # cosmetic — routing is purely by unique_id.
        #
        # TimeSlots[] (nested time-of-use array, regs 250-279) is emitted as a
        # JSON array of objects {time, power, voltage, soc, chargeEnable}.
        # flatten_nested_data() only recurses dicts, not lists, so it lands as
        # a single opaque value on sensor.<dongle>_timeslots. Per-slot entities
        # are NOT created here — the dongle does not emit flat per-slot keys.
        # TODO: if per-slot controls are wanted, the firmware should emit flat
        # keys (e.g. TimeSlot0_power) or the coordinator needs a Deye-specific
        # nested flatten (mirroring _process_gridboss_nested_data).
        # =====================================================================
        "Deye": {
            "sensor": {
                "inputbank1": [
                    # Identity / status
                    {"name": "State", "type": "sensor", "unique_id": "State", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Firmware Code", "type": "sensor", "unique_id": "FWCode", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Inverter Date Time", "type": "sensor", "unique_id": "DateTime", "source": "inputbank1", "device_group": "Inverter"},

                    # Energy — daily (TOTAL_INCREASING, resets each day)
                    {"name": "Energy Inverter Day", "type": "sensor", "unique_id": "EinvDay", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy PV Day", "type": "sensor", "unique_id": "EpvDay", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Charge Day", "type": "sensor", "unique_id": "EchgDay", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Discharge Day", "type": "sensor", "unique_id": "EdischgDay", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy to User Day", "type": "sensor", "unique_id": "EtouserDay", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy to Grid Day", "type": "sensor", "unique_id": "EtogridDay", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Load Day", "type": "sensor", "unique_id": "EloadDay", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Generator Day", "type": "sensor", "unique_id": "EgenDay", "state_class": SensorStateClass.TOTAL_INCREASING, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},

                    # Energy — totals (TOTAL, lifetime counters)
                    {"name": "Energy Inverter All", "type": "sensor", "unique_id": "EinvAll", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy PV All", "type": "sensor", "unique_id": "EpvAll", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Charge All", "type": "sensor", "unique_id": "EchgAll", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Discharge All", "type": "sensor", "unique_id": "EdischgAll", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy to User All", "type": "sensor", "unique_id": "EtouserAll", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy to Grid All", "type": "sensor", "unique_id": "EtogridAll", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Load All", "type": "sensor", "unique_id": "EloadAll", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},
                    {"name": "Energy Generator All", "type": "sensor", "unique_id": "EgenAll", "state_class": SensorStateClass.TOTAL, "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR, "device_class": SensorDeviceClass.ENERGY, "source": "inputbank1", "device_group": "Energy"},

                    # Grid
                    {"name": "Grid Frequency", "type": "sensor", "unique_id": "Fac", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfFrequency.HERTZ, "device_class": SensorDeviceClass.FREQUENCY, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Grid Voltage L1", "type": "sensor", "unique_id": "VacR", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Grid Voltage L2", "type": "sensor", "unique_id": "VacS", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Grid Voltage L1-L2", "type": "sensor", "unique_id": "Vac", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Grid Current L1", "type": "sensor", "unique_id": "IacR", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Grid Current L2", "type": "sensor", "unique_id": "IacS", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Grid Power L1", "type": "sensor", "unique_id": "PgridL1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Grid Power L2", "type": "sensor", "unique_id": "PgridL2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Grid Power", "type": "sensor", "unique_id": "Pgrid", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Grid"},

                    # PV
                    {"name": "Voltage PV1", "type": "sensor", "unique_id": "Vpv1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Voltage PV2", "type": "sensor", "unique_id": "Vpv2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Voltage PV3", "type": "sensor", "unique_id": "Vpv3", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Voltage PV4", "type": "sensor", "unique_id": "Vpv4", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Current PV1", "type": "sensor", "unique_id": "Ipv1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Current PV2", "type": "sensor", "unique_id": "Ipv2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Current PV3", "type": "sensor", "unique_id": "Ipv3", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Current PV4", "type": "sensor", "unique_id": "Ipv4", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Power PV1", "type": "sensor", "unique_id": "Ppv1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Power PV2", "type": "sensor", "unique_id": "Ppv2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Power PV3", "type": "sensor", "unique_id": "Ppv3", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Power PV4", "type": "sensor", "unique_id": "Ppv4", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "PV"},
                    {"name": "Power PV All", "type": "sensor", "unique_id": "Pall", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "PV"},

                    # Inverter output / EPS
                    {"name": "EPS Voltage L1-N", "type": "sensor", "unique_id": "EPSVoltL1N", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "EPS"},
                    {"name": "EPS Voltage L2-N", "type": "sensor", "unique_id": "EPSVoltL2N", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "EPS"},
                    {"name": "Inverter Power L1", "type": "sensor", "unique_id": "PinvL1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Inverter Power L2", "type": "sensor", "unique_id": "PinvL2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Inverter Power", "type": "sensor", "unique_id": "Pinv", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Inverter"},

                    # Load
                    {"name": "Load Power L1", "type": "sensor", "unique_id": "PloadL1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Load Power L2", "type": "sensor", "unique_id": "PloadL2", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "House Consumption (Live)", "type": "sensor", "unique_id": "Pload", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Load Active Power", "type": "sensor", "unique_id": "PloadActive", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Meter Power", "type": "sensor", "unique_id": "Pmeter", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Grid"},
                    {"name": "Load Frequency", "type": "sensor", "unique_id": "Fload", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfFrequency.HERTZ, "device_class": SensorDeviceClass.FREQUENCY, "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Inverter Frequency", "type": "sensor", "unique_id": "Finv", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfFrequency.HERTZ, "device_class": SensorDeviceClass.FREQUENCY, "source": "inputbank1", "device_group": "Inverter"},

                    # Battery
                    {"name": "Battery Voltage", "type": "sensor", "unique_id": "Vbat", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Temperature", "type": "sensor", "unique_id": "Tbat", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "State of Charge", "type": "sensor", "unique_id": "SOC", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": PERCENTAGE, "device_class": SensorDeviceClass.BATTERY, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Power", "type": "sensor", "unique_id": "Pbat", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfPower.WATT, "device_class": SensorDeviceClass.POWER, "source": "inputbank1", "device_group": "Battery"},
                    {"name": "Battery Current", "type": "sensor", "unique_id": "Ibat", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "inputbank1", "device_group": "Battery"},

                    # Temperatures
                    {"name": "Radiator Temperature 1", "type": "sensor", "unique_id": "Tradiator1", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "source": "inputbank1", "device_group": "Temperature"},
                    {"name": "Internal Temperature", "type": "sensor", "unique_id": "Tinner", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfTemperature.CELSIUS, "device_class": SensorDeviceClass.TEMPERATURE, "source": "inputbank1", "device_group": "Temperature"},

                    # Codes / relays (raw words)
                    {"name": "Warning Word 1", "type": "sensor", "unique_id": "WarningWord1", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Warning Word 2", "type": "sensor", "unique_id": "WarningWord2", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Fault Word 1", "type": "sensor", "unique_id": "FaultWord1", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Fault Word 2", "type": "sensor", "unique_id": "FaultWord2", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Fault Word 3", "type": "sensor", "unique_id": "FaultWord3", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Fault Word 4", "type": "sensor", "unique_id": "FaultWord4", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Grid Relay Status", "type": "sensor", "unique_id": "GridRelayStatus", "source": "inputbank1", "device_group": "Inverter"},
                    {"name": "Generator Relay Status", "type": "sensor", "unique_id": "GenRelayStatus", "source": "inputbank1", "device_group": "Inverter"},
                ],
                # Read-only BMS realtime telemetry that arrives on the hold bank.
                "holdbank1": [
                    {"name": "BMS Charge Voltage", "type": "sensor", "unique_id": "BMSChargeVoltage", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "holdbank1", "device_group": "Battery"},
                    {"name": "BMS Discharge Voltage", "type": "sensor", "unique_id": "BMSDischargeVoltage", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricPotential.VOLT, "device_class": SensorDeviceClass.VOLTAGE, "source": "holdbank1", "device_group": "Battery"},
                    {"name": "BMS Charge Current Limit", "type": "sensor", "unique_id": "BMSChargeCurrLimit", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "holdbank1", "device_group": "Battery"},
                    {"name": "BMS Discharge Current Limit", "type": "sensor", "unique_id": "BMSDischargeCurrLimit", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": UnitOfElectricCurrent.AMPERE, "device_class": SensorDeviceClass.CURRENT, "source": "holdbank1", "device_group": "Battery"},
                    {"name": "BMS Realtime SOC", "type": "sensor", "unique_id": "BMSRealtimeSOC", "state_class": SensorStateClass.MEASUREMENT, "unit_of_measurement": PERCENTAGE, "device_class": SensorDeviceClass.BATTERY, "source": "holdbank1", "device_group": "Battery"},
                    # Nested time-of-use array — lands here as an opaque value.
                    # See header note: per-slot entities are a documented TODO.
                    {"name": "Time Of Use Slots", "type": "sensor", "unique_id": "TimeSlots", "source": "holdbank1", "device_group": "Controls", "entity_registry_enabled_default": False},
                ],
            },
            "switch": {
                "holdbank1": [
                    {"name": "AC (Grid) Charge", "type": "switch", "unique_id": "ACCharge", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Export to Grid (Solar Sell)", "type": "switch", "unique_id": "FeedInGrid", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Time Of Use Enable", "type": "switch", "unique_id": "TimeOfUse", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Charge Last", "type": "switch", "unique_id": "ubChgLastEn", "source": "holdbank1", "device_group": "Controls"},
                ],
            },
            "select": {
                "holdbank1": [
                    {"name": "Battery Charge Type", "type": "select", "unique_id": "BatChargeType", "options": ["Lithium", "Lead Acid", "No Battery"], "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Battery Control Mode", "type": "select", "unique_id": "ubBatChgcontrol", "options": ["SOC", "Voltage"], "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Working Mode", "type": "select", "unique_id": "ubWorkingMode", "options": ["Selling First", "Zero Export To Load", "Zero Export To CT"], "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Grid Regulation", "type": "select", "unique_id": "GridRegulation", "options": ["General Standard", "UL1741 & IEEE1547", "CPUC RULE21", "SRD-UL-1741", "CEI 0-21", "EN50549", "Custom"], "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Grid Type", "type": "select", "unique_id": "GridType", "options": ["Split Phase (240V)", "Single Phase (230V)", "Three Phase (400V)"], "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Lithium Battery Type", "type": "select", "unique_id": "LithiumBatteryType", "options": ["No Battery", "Pylon CAN", "Pylon RS485", "Dyness CAN", "Generic"], "source": "holdbank1", "device_group": "Controls"},
                ],
            },
            "number": {
                "holdbank1": [
                    # Battery config
                    {"name": "Battery Capacity (Ah)", "type": "number", "unique_id": "BatCapacity", "unit": "Ah", "min": 0, "max": 2000, "mode": "box", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Max Charge Current", "type": "number", "unique_id": "ChargeCurr", "unit": "A", "min": 0, "max": 250, "mode": "slider", "native_unit": "A", "class": "CURRENT", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Max Discharge Current", "type": "number", "unique_id": "DischgCurr", "unit": "A", "min": 0, "max": 250, "mode": "slider", "native_unit": "A", "class": "CURRENT", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "On-grid Discharge Cut-off SOC", "type": "number", "unique_id": "EOD", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Battery Restart SOC", "type": "number", "unique_id": "BatLowBackSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Battery Low SOC", "type": "number", "unique_id": "BatLowSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Battery Shutdown Voltage", "type": "number", "unique_id": "BatLowVoltage", "step": 0.01, "unit": "V", "min": 40, "max": 60, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Battery Restart Voltage", "type": "number", "unique_id": "BatLowBackVoltage", "step": 0.01, "unit": "V", "min": 40, "max": 60, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Battery Low to Utility Voltage", "type": "number", "unique_id": "BatLowtoUtilityVoltage", "step": 0.01, "unit": "V", "min": 40, "max": 60, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Battery Charge Efficiency", "type": "number", "unique_id": "BatChargeEfficiency", "step": 0.1, "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    # Generator
                    {"name": "Generator Charge Start SOC", "type": "number", "unique_id": "GenChgStartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Max Generator Charge Battery Current", "type": "number", "unique_id": "MaxGenChgBatCurr", "unit": "A", "min": 0, "max": 250, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Generator Max Operating Time", "type": "number", "unique_id": "GenMaxOperatingTime", "step": 0.1, "unit": "h", "min": 0, "max": 24, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Generator Cool Down Time", "type": "number", "unique_id": "GenCoolDownTime", "step": 0.1, "unit": "h", "min": 0, "max": 24, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Generator Charge Start Voltage", "type": "number", "unique_id": "GenChgStartVolt", "step": 0.01, "unit": "V", "min": 40, "max": 60, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Generator Peak Shaving Power", "type": "number", "unique_id": "GenPeakShavingPower", "unit": "W", "min": 0, "max": 20000, "mode": "box", "source": "holdbank1", "device_group": "Controls"},
                    # AC (grid) charge
                    {"name": "AC Charge Start SOC", "type": "number", "unique_id": "ACChgStartSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "AC Charge Battery Current", "type": "number", "unique_id": "ACChargeBatCurrent", "unit": "A", "min": 0, "max": 250, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "AC Charge Start Voltage", "type": "number", "unique_id": "ACChgStartVolt", "step": 0.01, "unit": "V", "min": 40, "max": 60, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Grid Peak Shaving Power", "type": "number", "unique_id": "GridPeakShavingPower", "unit": "W", "min": 0, "max": 20000, "mode": "box", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Max Grid Export Power", "type": "number", "unique_id": "MaxBackFlow", "unit": "W", "min": 0, "max": 20000, "mode": "box", "source": "holdbank1", "device_group": "Controls"},
                    # Smart load
                    {"name": "Smart Load Off SOC", "type": "number", "unique_id": "SmartLoadOffSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Smart Load On SOC", "type": "number", "unique_id": "SmartLoadOnSOC", "unit": "%", "min": 0, "max": 100, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Smart Load Off Voltage", "type": "number", "unique_id": "SmartLoadOffVolt", "step": 0.01, "unit": "V", "min": 40, "max": 60, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Smart Load On Voltage", "type": "number", "unique_id": "SmartLoadOnVolt", "step": 0.01, "unit": "V", "min": 40, "max": 60, "mode": "slider", "source": "holdbank1", "device_group": "Controls"},
                    # Grid settings
                    {"name": "Grid Frequency Setting", "type": "number", "unique_id": "GridFreq", "unit": "Hz", "min": 50, "max": 60, "mode": "box", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Grid Connect Voltage High", "type": "number", "unique_id": "GridVoltConnHigh", "step": 0.1, "unit": "V", "min": 0, "max": 300, "mode": "box", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Grid Connect Voltage Low", "type": "number", "unique_id": "GridVoltConnLow", "step": 0.1, "unit": "V", "min": 0, "max": 300, "mode": "box", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Grid Connect Frequency High", "type": "number", "unique_id": "GridFreqConnHigh", "step": 0.01, "unit": "Hz", "min": 45, "max": 65, "mode": "box", "source": "holdbank1", "device_group": "Controls"},
                    {"name": "Grid Connect Frequency Low", "type": "number", "unique_id": "GridFreqConnLow", "step": 0.01, "unit": "Hz", "min": 45, "max": 65, "mode": "box", "source": "holdbank1", "device_group": "Controls"},
                ],
            },
        },

        "Solis": {
            "sensors": [
                {"name": "Energy", "type": "sensor", "unique_id": "energy", "state_class": SensorStateClass.MEASUREMENT, "unit": "kWh"},
                {"name": "Temperature", "type": "sensor", "unique_id": "temperature", "state_class": SensorStateClass.MEASUREMENT, "unit": "°C"},
            ],
            "numbers": [
                {"name": "Setpoint", "type": "number", "unique_id": "setpoint", "unit": "°C"},
            ],
        },
        "Solax": {
            "sensors": [
                {"name": "Battery Level", "type": "sensor", "unique_id": "battery_level", "state_class": SensorStateClass.MEASUREMENT, "unit": "%"},
            ],
            "switches": [
                {"name": "Inverter Status", "type": "switch", "unique_id": "inverter_status"},
            ],
        },
        "Growatt": {
            "sensors": [
                {"name": "Output Power", "type": "sensor", "unique_id": "output_power", "state_class": SensorStateClass.MEASUREMENT, "unit": "W"},
            ],
            "times": [
                {"name": "AC Charge Start1", "type": "time", "unique_id": "ac_charge_start1"},
                {"name": "AC Charge End1", "type": "time", "unique_id": "ac_charge_end1"},
            ],
        },
    }
