"""Settings entities must not report a fabricated value before data arrives.

Dongles on FW >= 4.3.0 only stream change-data, so a hold register (a setting)
reaches HA exactly once, in the connect-time snapshot. If that snapshot is lost
the entity never receives a value -- and a number seeded with 0 or a switch
seeded with False is then indistinguishable from a real reading of 0/off.
Seeding None instead surfaces it as 'unknown', which is what select.py already
does.
"""
from unittest.mock import MagicMock


def _entry(entity_id):
    entry = MagicMock()
    coord = entry.runtime_data
    coord.build_entity_id.return_value = entity_id
    coord.get_formatted_dongle_id.return_value = "dongle_x"
    coord.get_firmware_code.return_value = "AAAA"
    return entry


def test_number_has_no_value_before_data_arrives():
    from custom_components.monitormysolar.number import InverterNumber

    entry = _entry("number.dongle_x_acchgsoclimit")
    n = InverterNumber(
        {"name": "AC Charge SOC Limit", "unique_id": "acchgsoclimit", "min": 0, "max": 100},
        MagicMock(), entry, "holdbank1", "dongle-X",
    )
    assert n._attr_native_value is None


def test_switch_has_no_state_before_data_arrives():
    from custom_components.monitormysolar.switch import InverterSwitch

    entry = _entry("switch.dongle_x_accharge")
    s = InverterSwitch(
        {"name": "AC Charge", "unique_id": "accharge"},
        MagicMock(), entry, "holdbank1", "dongle-X",
    )
    assert s.is_on is None


def test_select_already_has_no_state_before_data_arrives():
    """Baseline: select.py was already correct; number/switch now match it."""
    from custom_components.monitormysolar.select import InverterSelect

    entry = _entry("select.dongle_x_acchargetype")
    sel = InverterSelect(
        {"name": "AC Charge Type", "unique_id": "acchargetype", "options": ["Time", "SOC/Volt"]},
        MagicMock(), entry, "dongle-X",
    )
    assert sel.current_option is None
