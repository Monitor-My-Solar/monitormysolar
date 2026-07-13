"""Tests for firmware-code grouping and group-based entity gating."""
import pytest

from custom_components.monitormysolar.const import firmware_group, fw_code_get


@pytest.mark.parametrize("code,group", [
    ("IAAB", "midbox"),
    ("IAAA", "midbox"),
    ("AAAA", "legacy"),
    ("AAAB", "legacy"),
    ("ABAA", "legacy"),
    ("ADAA", "legacy"),      # other A -> legacy
    ("ACAB", "GEN"),         # AC -> GEN
    ("ACAA", "GEN"),
    ("BAAA", "ac_coupled"),
    ("BAAB", "ac_coupled"),
    ("BBAA", "ac_coupled"),
    ("HAAA", "GEN"),
    ("FAAA", "GEN"),
    ("FAAB", "GEN"),
    ("EAAA", "GEN"),
    ("EAAB", "GEN"),
    ("GAAA", "threephase"),
    ("GAAB", "threephase"),
    ("ccaa", "offgrid"),     # case-insensitive
    ("ceaa", "offgrid"),
    ("CEAA", "offgrid"),
    ("", "legacy"),          # empty -> permissive
    ("ZZZZ", "legacy"),      # unknown -> permissive
])
def test_firmware_group(code, group):
    assert firmware_group(code) == group


# The code-keyed tables mix casings ("FAAA" vs "ceaa") and dongles report mixed
# case too ("Ceaa") — every code-keyed lookup must go through fw_code_get.
@pytest.mark.parametrize("code", ["ceaa", "Ceaa", "CEAA", " Ceaa "])
def test_fw_code_get_case_and_whitespace_insensitive(code):
    table = {"FAAA": 250, "ceaa": 250, "AAAA": 78}
    assert fw_code_get(table, code) == 250


def test_fw_code_get_matches_uppercase_keys_from_lowercase_code():
    table = {"FAAA": 250}
    assert fw_code_get(table, "faaa") == 250


def test_fw_code_get_default_on_miss_or_empty():
    table = {"ceaa": 250}
    assert fw_code_get(table, "ZZZZ", 140) == 140
    assert fw_code_get(table, "", 140) == 140
    assert fw_code_get(table, None, 140) == 140
    assert fw_code_get({}, "ceaa", 140) == 140


def test_valid_firmware_codes_friendly_name_for_ceaa():
    from custom_components.monitormysolar.const import VALID_FIRMWARE_CODES
    assert fw_code_get(VALID_FIRMWARE_CODES, "Ceaa") == "Off Grid"


def _set_fw(coordinator, code):
    coordinator.get_firmware_code = lambda dongle_id: code


def test_entity_allowed_generic_entity(coordinator):
    """An entity with no allowed_groups is created for any non-midbox group."""
    _set_fw(coordinator, "HAAA")  # GEN
    assert coordinator.entity_allowed_for_dongle("d", {"unique_id": "x"}) is True


def test_entity_allowed_generic_excluded_for_midbox(coordinator):
    """Generic (ungated) entities are NOT created for midbox/GridBoss dongles."""
    _set_fw(coordinator, "IAAB")  # midbox
    assert coordinator.entity_allowed_for_dongle("d", {"unique_id": "x"}) is False


def test_entity_allowed_group_match(coordinator):
    _set_fw(coordinator, "HAAA")  # GEN
    assert coordinator.entity_allowed_for_dongle("d", {"allowed_groups": ["GEN"]}) is True
    assert coordinator.entity_allowed_for_dongle("d", {"allowed_groups": ["offgrid"]}) is False


def test_ac_coupled_b_unit_gating(coordinator):
    """B units (ac_coupled) get generic entities and ac_coupled-tagged ones."""
    _set_fw(coordinator, "BAAA")  # ac_coupled
    # generic (no allowed_groups) -> created for B (it's not midbox)
    assert coordinator.entity_allowed_for_dongle("d", {"unique_id": "x"}) is True
    # ac_coupled-tagged -> created
    assert coordinator.entity_allowed_for_dongle("d", {"allowed_groups": ["legacy", "ac_coupled"]}) is True
    # legacy-only -> NOT created for B (this is what fixed the ppv1 collision)
    assert coordinator.entity_allowed_for_dongle("d", {"allowed_groups": ["legacy"]}) is False


def test_entity_allowed_midbox_entity(coordinator):
    """A midbox-tagged entity is created only for midbox dongles."""
    _set_fw(coordinator, "IAAB")
    assert coordinator.entity_allowed_for_dongle("d", {"allowed_groups": ["midbox"]}) is True
    _set_fw(coordinator, "HAAA")
    assert coordinator.entity_allowed_for_dongle("d", {"allowed_groups": ["midbox"]}) is False


def test_is_gridboss_uses_midbox_group(coordinator):
    """Any I*** code (not just exact IAAB) is detected as GridBoss."""
    from custom_components.monitormysolar.coordinator import MonitorMySolar
    # The fixture stubs is_gridboss_dongle with a MagicMock; bind the real method.
    coordinator.is_gridboss_dongle = MonitorMySolar.is_gridboss_dongle.__get__(coordinator)
    coordinator.get_dongle_info = lambda dongle_id: {}
    coordinator._has_gridboss = False
    coordinator._gridboss_dongle = ""
    _set_fw(coordinator, "IAAB")
    assert coordinator.is_gridboss_dongle("d") is True
    _set_fw(coordinator, "IBAA")
    assert coordinator.is_gridboss_dongle("d") is True
    _set_fw(coordinator, "HAAA")
    assert coordinator.is_gridboss_dongle("d") is False
