"""Selects whose sent values are not positional (PV Input Mode on ciaa)."""
from custom_components.monitormysolar.select import option_to_value, value_to_option

OPTS = ["Empty", "Parallel MPPT Inputs", "Independent MPPT Inputs"]
VALS = [0, 3, 4]


def test_positional_default_unchanged():
    assert option_to_value(["A", "B", "C"], None, "C") == 2
    assert value_to_option(["A", "B", "C"], None, 1) == "B"
    assert value_to_option(["A", "B", "C"], None, 7) is None
    assert value_to_option(["A", "B", "C"], None, True) == "B"


def test_option_values_send_the_register_value_not_the_index():
    assert option_to_value(OPTS, VALS, "Parallel MPPT Inputs") == 3
    assert option_to_value(OPTS, VALS, "Independent MPPT Inputs") == 4
    assert option_to_value(OPTS, VALS, "Empty") == 0


def test_option_values_decode_incoming_and_reject_unoffered():
    assert value_to_option(OPTS, VALS, 4) == "Independent MPPT Inputs"
    assert value_to_option(OPTS, VALS, 1) is None  # not offered on ciaa
    assert value_to_option(OPTS, VALS, "x") is None


def test_value_mask_drops_the_packed_high_byte():
    # Another read-only field is packed alongside the mode; the mask isolates the mode.
    assert value_to_option(OPTS, VALS, 0x0203, 0xFF) == "Parallel MPPT Inputs"
    assert value_to_option(OPTS, VALS, 0x0203) is None


def test_ciaa_pv_input_mode_catalog_row():
    from custom_components.monitormysolar.const import ENTITIES
    rows = [e for e in ENTITIES["Lux"]["select"]["holdbank1"] if e["unique_id"] == "PVInputModel"]
    assert len(rows) == 1
    assert rows[0]["options"] == OPTS
    assert rows[0]["option_values"] == VALS
    assert rows[0]["value_mask"] == 255
    assert rows[0]["allowed_firmware_codes"] == ["ciaa"]
