"""Stable and beta firmware update entities: one per track per dongle.

Needs the real homeassistant package (the update entity imports its base
classes); the module is skipped where only the stubs are present.
"""
from unittest.mock import MagicMock

import pytest

update = pytest.importorskip("custom_components.monitormysolar.update")

SERVER = {
    "s3": {"latestFwVersion": "4.3.3.2S3", "betaFwVersion": "4.5.0.87S3",
           "changelog": "stable notes", "changelogBeta": "beta notes"},
}


def _entity(track, show_beta=False, installed="4.3.3.2S3"):
    e = update.DongleFirmwareUpdate.__new__(update.DongleFirmwareUpdate)
    e._track = track
    e._dongle_id = "dongle-A"
    e._attr_has_entity_name = False
    coord = MagicMock()
    coord.server_versions = SERVER
    coord.dongle_chip.return_value = "s3"
    coord.current_fw_versions = {"dongle-A": installed}
    coord.entry.data = {"use_beta_firmware": show_beta}
    e.coordinator = coord
    return e


def test_each_track_reads_its_own_channel_field():
    assert _entity("prod").latest_version == "4.3.3.2S3"
    assert _entity("beta").latest_version == "4.5.0.87S3"
    assert _entity("prod").release_notes() == "stable notes"
    assert _entity("beta").release_notes() == "beta notes"
    assert _entity("beta").extra_state_attributes == {"chip": "S3", "track": "beta"}


def test_beta_entity_name_and_default_enablement():
    assert _entity("prod").name == "Firmware Update"
    assert _entity("beta").name == "Firmware Beta Update"
    assert _entity("prod", show_beta=False).entity_registry_enabled_default is True
    assert _entity("beta", show_beta=False).entity_registry_enabled_default is False
    assert _entity("beta", show_beta=True).entity_registry_enabled_default is True


def test_stable_entity_never_offers_the_beta_build():
    # A unit already on the beta build is not offered a downgrade to stable.
    e = _entity("prod", installed="4.5.0.87S3")
    assert e.version_is_newer(e.latest_version, e.installed_version) is False
    b = _entity("beta", installed="4.3.3.2S3")
    assert b.version_is_newer(b.latest_version, b.installed_version) is True
