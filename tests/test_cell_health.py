"""JK cell health: flag rule identical to the dongle UI, device flattening,
and the coordinator handler (entities per MAC, creation event once)."""
import json

import pytest

from custom_components.monitormysolar.cell_health import (
    balancer_waiting,
    flagged_cells,
    flatten_device,
    mac_slug,
    resistance_median,
)

SEPLOS = [190, 180, 159, 151, 150, 134, 104, 76, 74, 102, 130, 157, 171, 172, 186, 204]


def test_flag_rule_matches_dongle():
    assert resistance_median([74, 80, 204, 76]) == 80
    assert flagged_cells([74, 80, 204, 76]) == [3]
    assert resistance_median(SEPLOS) == 157
    assert flagged_cells(SEPLOS) == []          # 204 < 235.5
    assert flagged_cells([100, 100, 150]) == []  # strictly greater
    assert flagged_cells([]) == []


def _device(**over):
    d = {
        "name": "PC-0A56", "mac": "C8:47:80:81:23:D9", "role": "balancer", "model": "JK_B2A16S",
        "hw": "11", "sw": "11.57", "online": True, "packVoltage": 52.74, "avgCellVoltage": 3.296,
        "cellDeltaMv": 12, "maxCell": 2, "minCell": 4, "balancing": 1, "balanceCurrent": 0.85,
        "runtimeS": 123456, "cellVoltages": [3.300, 3.302, 3.290, 3.292],
        "cellResistanceMohm": [74, 80, 204, 76],
    }
    d.update(over)
    return d


def test_flatten_device_and_balancer_settings():
    flat = flatten_device(_device())
    assert flat["status"] == "ok" and flat["balancing"] == "charging"
    assert flat["res_median_mohm"] == 80 and flat["res_max_mohm"] == 204
    assert flat["res_flagged_count"] == 1 and flat["res_flagged_cells"] == [3]
    assert flat["cell_3_resistance"] == 204 and flat["cell_1_voltage"] == 3.3
    assert "balancer_enabled" not in flat  # pre-85S3: no settings block
    waiting = _device(cellDeltaMv=22, balancerCfg={"enabled": True, "startVoltage": 3.45, "triggerMv": 5, "maxCurrent": 2.0})
    flat = flatten_device(waiting)
    assert flat["balancer_enabled"] == "on" and flat["balancer_start_voltage"] == 3.45
    assert flat["balancer_waiting"] == "yes"
    assert balancer_waiting(_device(cellDeltaMv=22, cellVoltages=[3.46, 3.44, 3.438, 3.441],
                                    balancerCfg={"enabled": True, "startVoltage": 3.45, "triggerMv": 5, "maxCurrent": 2.0})) is False
    assert mac_slug("C8:47:80:81:23:D9") == "c8478081" "23d9"


@pytest.mark.asyncio
async def test_coordinator_handler_creates_entities_once(coordinator):
    coordinator._cell_health_data = {}
    coordinator._cell_health_entities_created = set()
    coordinator.get_entity_prefix = lambda dongle_id: "dongle_test"
    payload = json.dumps({"count": 1, "devices": [_device()]})
    await coordinator._handle_cell_health_data("dongle-test", payload)
    key = coordinator.build_entity_id("sensor", "dongle-test", "cellhealth_c847808123d9_res_flagged_count")
    assert coordinator.entities[key] == 1
    assert coordinator.entities[coordinator.build_entity_id("sensor", "dongle-test", "cellhealth_c847808123d9_cell_3_resistance")] == 204
    assert coordinator.hass.bus.async_fire.call_count == 1
    event, data = coordinator.hass.bus.async_fire.call_args[0]
    assert event.endswith("_cellhealth_data_received") and data["macs"] == ["C8:47:80:81:23:D9"]
    # Mark created (sensor.py does this) and send the next poll: values update, no new event.
    coordinator._cell_health_entities_created.add("dongle-test:C8:47:80:81:23:D9")
    await coordinator._handle_cell_health_data("dongle-test", json.dumps({"devices": [_device(cellResistanceMohm=[74, 80, 90, 76])]}))
    assert coordinator.entities[key] == 0
    assert coordinator.hass.bus.async_fire.call_count == 1
    assert coordinator.get_cell_health_data("dongle-test")["C8:47:80:81:23:D9"]["cellResistanceMohm"] == [74, 80, 90, 76]
    # Garbage and empty payloads are ignored.
    await coordinator._handle_cell_health_data("dongle-test", "{nope")
    await coordinator._handle_cell_health_data("dongle-test", "")
