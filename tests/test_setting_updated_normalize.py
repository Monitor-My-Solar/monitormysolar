"""FW >= 4.3.0 /setting/updated durable channel: value normalization.

The dongle emits every successful write on <dongle>/setting/updated with the
value as a STRING, e.g. {"setting":"SmartLoad3_PortMode","value":"1.00",...}.
That raw "1.00" must be coerced to each platform's native type BEFORE it lands
in coordinator.entities — an int index for selects (else the select renders
'unknown'), a float for numbers, 0/1 for switches, string-as-is for time.

Both /response (legacy) and /setting/updated (new) fire on a 4.3.0 HA write;
both must converge on the SAME representation.

Uses the `coordinator` fixture (built via __new__ in conftest) so the HA stubs
are already in place; normalize_setting_value reads no instance state.
"""

PORTMODE = {"unique_id": "SmartLoad3_PortMode",
            "options": ["Does Not Operate", "Smart Load", "Ac Coupled"]}


def test_select_string_float_becomes_index(coordinator):
    n = coordinator.normalize_setting_value
    assert n("select", PORTMODE, "1.00") == 1   # -> "Smart Load"
    assert n("select", PORTMODE, "2.00") == 2   # -> "Ac Coupled"
    assert n("select", PORTMODE, "0.00") == 0   # -> "Does Not Operate"


def test_select_plain_int_becomes_index(coordinator):
    n = coordinator.normalize_setting_value
    assert n("select", PORTMODE, 1) == 1
    assert n("select", PORTMODE, "1") == 1


def test_select_existing_label_passthrough(coordinator):
    assert coordinator.normalize_setting_value("select", PORTMODE, "Ac Coupled") == "Ac Coupled"


def test_select_out_of_range_left_untouched(coordinator):
    # 9 is not a valid index; return as-is so the entity can keep its state.
    assert coordinator.normalize_setting_value("select", PORTMODE, "9.00") == "9.00"


def test_number_string_float_becomes_number(coordinator):
    n = coordinator.normalize_setting_value
    assert n("number", {}, "8.00") == 8         # whole -> int
    assert n("number", {}, "8.50") == 8.5       # fractional -> float
    assert n("number", {}, "0.00") == 0


def test_switch_string_float_becomes_bit(coordinator):
    n = coordinator.normalize_setting_value
    assert n("switch", {}, "1.00") == 1
    assert n("switch", {}, "0.00") == 0
    assert n("switch", {}, "1") == 1


def test_time_passthrough(coordinator):
    assert coordinator.normalize_setting_value("time", {}, "06:30") == "06:30"


def test_none_passthrough(coordinator):
    assert coordinator.normalize_setting_value("select", PORTMODE, None) is None


def test_both_channels_converge_on_same_index(coordinator):
    # /response confirm_option mirrors index 1; /setting/updated normalizes
    # "1.00" to index 1. Same value -> no fight, no unknown.
    from_response = 1
    from_setting_updated = coordinator.normalize_setting_value("select", PORTMODE, "1.00")
    assert from_response == from_setting_updated == 1
