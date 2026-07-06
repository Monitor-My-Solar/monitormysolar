"""Tests for firmware-code grouping and group-based entity gating."""
import pytest

from custom_components.monitormysolar.const import firmware_group


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
