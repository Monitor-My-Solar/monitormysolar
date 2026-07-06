"""Tests for the per-dongle entity_prefix naming scheme and dongle-less uid fix."""


def _set_dongle_data(coordinator, data):
    coordinator._dongle_data = data
    coordinator._dongle_ids = [d["dongle_id"] for d in data]
    # get_dongle_info reads _dongle_data
    def _get_info(dongle_id):
        for d in coordinator._dongle_data:
            if d["dongle_id"] == dongle_id:
                return d
        return None
    coordinator.get_dongle_info = _get_info


def test_single_dongle_no_prefix(coordinator):
    """Single dongle with empty entity_prefix -> clean entity_id, no prefix."""
    _set_dongle_data(coordinator, [{"dongle_id": "dongle-AA", "entity_prefix": ""}])
    assert coordinator.get_entity_prefix("dongle-AA") == ""
    assert coordinator.build_entity_id("sensor", "dongle-AA", "Battery_SOC") == "sensor.battery_soc"


def test_custom_prefix(coordinator):
    """A custom prefix (e.g. flexboss1) is applied to the entity_id."""
    _set_dongle_data(coordinator, [
        {"dongle_id": "dongle-AA", "entity_prefix": "flexboss1"},
        {"dongle_id": "dongle-BB", "entity_prefix": "flexboss2"},
    ])
    assert coordinator.build_entity_id("sensor", "dongle-AA", "SOC") == "sensor.flexboss1_soc"
    assert coordinator.build_entity_id("number", "dongle-BB", "ChargeRate") == "number.flexboss2_chargerate"


def test_prefix_formatted(coordinator):
    """A prefix that is a dongle-id gets formatted (colons/dashes -> underscores)."""
    _set_dongle_data(coordinator, [
        {"dongle_id": "dongle-AA:BB", "entity_prefix": "dongle-AA:BB"},
    ])
    assert coordinator.build_entity_id("sensor", "dongle-AA:BB", "soc") == "sensor.dongle_aa_bb_soc"


def test_legacy_no_entity_prefix_key_falls_back(coordinator):
    """Entries created before entity_prefix existed: fall back to formatted dongle id."""
    # No 'entity_prefix' key at all -> legacy behaviour.
    _set_dongle_data(coordinator, [{"dongle_id": "dongle-AA"}])
    coordinator._drop_dongle_id = False
    assert coordinator.build_entity_id("sensor", "dongle-AA", "soc") == "sensor.dongle_aa_soc"


def test_legacy_drop_flag_single_dongle(coordinator):
    """Legacy entry with drop_dongle_id flag on a single dongle -> clean."""
    _set_dongle_data(coordinator, [{"dongle_id": "dongle-AA"}])
    coordinator._drop_dongle_id = True
    assert coordinator.build_entity_id("sensor", "dongle-AA", "soc") == "sensor.soc"
