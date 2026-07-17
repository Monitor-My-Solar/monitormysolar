"""Tests for firmware version ordering (update entity 'is newer' logic).

HA's default update comparison is inequality, which offers 'downgrades' to
units running builds newer than the server's published version. The update
entity overrides version_is_newer with a strict numeric tuple compare via
const.fw_version_is_newer. Server-side rollbacks are deliberately NOT shown
in HA (they go via the /admin OTA command).
"""
import pytest

from custom_components.monitormysolar.const import fw_version_is_newer, version_tuple


@pytest.mark.parametrize("version,expected", [
    ("4.3.2.2C6", (4, 3, 2, 2)),   # chip suffix on build segment
    ("4.3.2C6", (4, 3, 2)),        # chip suffix glued to patch
    ("4.3.0.111S3", (4, 3, 0, 111)),
    ("4.3.2", (4, 3, 2)),
    ("", None),
    (None, None),
    ("C6", None),                  # no leading digits
    ("4..2", None),                # empty segment
])
def test_version_tuple(version, expected):
    assert version_tuple(version) == expected


@pytest.mark.parametrize("latest,installed,newer", [
    ("4.3.2.2", "4.3.2.1", True),    # ordinary upgrade
    ("4.3.2.1", "4.3.2.2", False),   # server behind dev unit -> no downgrade offer
    ("4.3.2.2", "4.3.2.2", False),   # equal
    ("4.3.3", "4.3.2.9", True),      # patch bump beats higher build
    ("4.3.2.1", "4.3.2", True),      # longer tuple, strictly newer
    ("4.3.2", "4.3.2.0", False),     # zero-padding: 4.3.2 == 4.3.2.0
    ("4.3.2.0", "4.3.2", False),
    ("4.3.2.2", "4.3.2.2C6", False), # chip suffix stripped before compare
    ("5.0.0", "4.9.9.99", True),
    # Unparseable falls back to plain inequality (never hide a real update).
    ("weird", "4.3.2", True),
    ("weird", "weird", False),
    ("4.3.2", None, True),
])
def test_fw_version_is_newer(latest, installed, newer):
    assert fw_version_is_newer(latest, installed) is newer
