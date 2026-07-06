"""Tests for the two-way display_scale on number entities.

Some kW registers arrive RAW at 10x the engineering value (dongle sends 80 for
8.0 kW). display_scale divides on display and multiplies on send, so the UI shows
8.0 while the dongle still receives 80.
"""


def _scale_display(raw, scale):
    """Mirror InverterNumber._handle_coordinator_update display maths."""
    return raw / scale if scale != 1 else raw


def _scale_send(value, scale):
    """Mirror async_set_native_value send maths (raw register value + mqtt int)."""
    raw_value = value * scale if scale != 1 else value
    mqtt_value = int(raw_value) if scale != 1 else value
    return raw_value, mqtt_value


def test_display_divides_by_scale():
    # dongle sends raw 80 -> UI shows 8.0 kW
    assert _scale_display(80, 10) == 8.0
    assert _scale_display(240, 10) == 24.0
    assert _scale_display(0, 10) == 0.0


def test_send_multiplies_by_scale():
    # user sets 8.0 kW -> raw 80 stored, mqtt sends integer 80
    raw, mqtt = _scale_send(8.0, 10)
    assert raw == 80.0
    assert mqtt == 80
    raw, mqtt = _scale_send(2.4, 10)
    assert mqtt == 24


def test_round_trip_matches():
    # send 8.0 -> raw 80 -> dongle echoes 80 -> display 8.0 == user value
    scale = 10
    user = 8.0
    raw, mqtt = _scale_send(user, scale)
    echoed = _scale_display(mqtt, scale)
    assert echoed == user  # so the user-initiated flag clears cleanly


def test_unscaled_unaffected():
    # scale == 1 (default / voltages): no division or multiplication
    assert _scale_display(80, 1) == 80
    raw, mqtt = _scale_send(48.5, 1)
    assert raw == 48.5 and mqtt == 48.5


def test_only_kw_variants_tagged():
    """Only the three kW power registers carry display_scale in the Lux catalog."""
    import importlib.util, sys, types
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
    import pathlib
    p = pathlib.Path(__file__).resolve().parent.parent / "custom_components/monitormysolar/const.py"
    spec = importlib.util.spec_from_file_location("mms_const", p)
    const = importlib.util.module_from_spec(spec); spec.loader.exec_module(const)

    scaled = []
    for plat, banks in const.ENTITIES['Lux'].items():
        if not isinstance(banks, dict):
            continue
        for bank, items in banks.items():
            if not isinstance(items, list):
                continue
            for e in items:
                if isinstance(e, dict) and e.get("display_scale"):
                    scaled.append((e["unique_id"], e.get("unit")))
    uids = {u for u, _ in scaled}
    assert uids == {"ACChgPowerCMD", "ForcedDischgPowerCMD", "MaxBackFlow"}, scaled
    # every scaled entity is the kW variant
    assert all(unit == "kW" for _, unit in scaled), scaled
