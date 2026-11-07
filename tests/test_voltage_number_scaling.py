"""Every inverter voltage control must accept tenths and send VOLTS.

The dongle's named write applies the tenths factor itself (55.5 V -> 555 on
the register), so a control that sends tenths (`mqtt_multiplier: 10`) asks
for ten times the voltage, and one without `step: 0.1` only lets the user
enter whole volts (issue #105; the lost decimal looked like a revert, #104).
The GridBoss voltage controls take volts the same way.
"""
import sys
import types
from unittest.mock import MagicMock


def _lux_catalog():
    for n in ['homeassistant', 'homeassistant.const', 'homeassistant.components',
              'homeassistant.components.sensor', 'homeassistant.components.update']:
        sys.modules.setdefault(n, types.ModuleType(n))
    import homeassistant.const as hc
    for a in ['CONF_MODE', 'PERCENTAGE', 'UnitOfElectricCurrent', 'UnitOfElectricPotential',
              'UnitOfEnergy', 'UnitOfFrequency', 'UnitOfPower', 'UnitOfTemperature',
              'UnitOfApparentPower', 'UnitOfTime', 'Platform']:
        if not hasattr(hc, a):
            setattr(hc, a, MagicMock())
    sys.modules['homeassistant.components.update'].UpdateDeviceClass = MagicMock()
    import homeassistant.components.sensor as hs
    for a in ['SensorDeviceClass', 'SensorStateClass']:
        if not hasattr(hs, a):
            setattr(hs, a, MagicMock())
    from custom_components.monitormysolar.const import ENTITIES
    return ENTITIES["Lux"]


def _voltage_numbers():
    found = []
    for bank in _lux_catalog()["number"].values():
        for entry in bank:
            if entry.get("type") == "number" and entry.get("unit") == "V":
                found.append(entry)
    return found


def test_catalog_has_voltage_numbers():
    names = {e["unique_id"] for e in _voltage_numbers()}
    assert {"BatStopChgVolt", "OngridEOD_Voltage", "CutVoltForDischg", "ACChgStartVolt",
            "SmartLoad1_StartVolt"} <= names


def test_every_voltage_number_sends_volts():
    scaled = [e["unique_id"] for e in _voltage_numbers() if "mqtt_multiplier" in e]
    assert scaled == []


def test_every_voltage_number_accepts_tenths():
    missing = [e["unique_id"] for e in _voltage_numbers() if e.get("step") != 0.1]
    assert missing == []
