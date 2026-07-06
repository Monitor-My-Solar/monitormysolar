"""Test the require_field availability decision for status diagnostic sensors.

The SD-card sensors (sd.health / sd.write_failures) only exist on S3 units — a C6
unit has no SD card, so those keys never appear in /status. Such sensors are tagged
require_field=True and must report unavailable when the field is absent, instead of
a stuck 'unknown'. This mirrors StatusFieldSensor.available without instantiating
the HA entity base classes.
"""


def _extract(blob, path):
    value = blob
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def _available(sensor_info, blob):
    if sensor_info.get("require_field"):
        return _extract(blob, sensor_info["status_field"]) is not None
    return True


S3_BLOB = {"chipType": "ESP32-S3", "sd": {"health": "healthy", "write_failures": 0}}
C6_BLOB = {"chipType": "ESP32-C6"}  # no sd key at all


def test_sd_available_on_s3():
    info = {"status_field": "sd.health", "require_field": True}
    assert _available(info, S3_BLOB) is True


def test_sd_unavailable_on_c6():
    info = {"status_field": "sd.health", "require_field": True}
    assert _available(info, C6_BLOB) is False
    info2 = {"status_field": "sd.write_failures", "require_field": True}
    assert _available(info2, C6_BLOB) is False


def test_non_require_field_always_available():
    info = {"status_field": "version"}  # no require_field
    assert _available(info, C6_BLOB) is True  # available even though 'version' absent here


def test_sd_sensors_are_gated_in_catalog():
    """The two SD sensors carry require_field + disabled-by-default in the catalog."""
    import importlib.util, sys, types, pathlib
    from unittest.mock import MagicMock
    for n in ['homeassistant','homeassistant.const','homeassistant.components',
              'homeassistant.components.sensor','homeassistant.components.update']:
        sys.modules.setdefault(n, types.ModuleType(n))
    import homeassistant.const as hc
    for a in ['CONF_MODE','PERCENTAGE','UnitOfElectricCurrent','UnitOfElectricPotential',
              'UnitOfEnergy','UnitOfFrequency','UnitOfPower','UnitOfTemperature',
              'UnitOfApparentPower','UnitOfTime','Platform']:
        setattr(hc, a, MagicMock())
    sys.modules['homeassistant.components.update'].UpdateDeviceClass = MagicMock()
    for a in ['SensorDeviceClass','SensorEntity','SensorStateClass']:
        setattr(sys.modules['homeassistant.components.sensor'], a, MagicMock())
    p = pathlib.Path(__file__).resolve().parent.parent / "custom_components/monitormysolar/const.py"
    spec = importlib.util.spec_from_file_location("mms_const", p)
    const = importlib.util.module_from_spec(spec); spec.loader.exec_module(const)

    sd = {e["unique_id"]: e for e in const.STATUS_DIAGNOSTIC_SENSORS
          if e["unique_id"] in ("sd_health", "sd_write_failures")}
    assert set(sd) == {"sd_health", "sd_write_failures"}
    for e in sd.values():
        assert e.get("require_field") is True
        assert e.get("entity_registry_enabled_default") is False
