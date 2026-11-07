"""JK cell health (JK BMS + JK active balancers) from the dongle's
<id>/cellhealth JSON (balancer-mode firmware 4.5.0.84S3+).

The dongle publishes the full device list once per BLE poll cycle (default
60 s) on the HA broker under the same prefix as /batteries. A JK active
balancer fitted inside a PACE / Seplos pack is NOT a battery: from this
firmware it no longer appears in /batteries, only here. The value is each
cell's CONNECTION RESISTANCE (mΩ): a cell above 1.5× the device median wants
its busbar or sense lead checked, and a value rising over weeks means a
loosening or corroding joint. Pure helpers live here so they are testable
without Home Assistant.
"""
from __future__ import annotations

from typing import Any

BALANCING_NAMES = {0: "off", 1: "charging", 2: "discharging"}


def mac_slug(mac: str) -> str:
    """Entity-id-safe form of a MAC: 'C8:47:80:81:23:D9' -> 'c8478081 23d9'-ish without separators."""
    return str(mac).lower().replace(":", "").replace("-", "")


def resistance_median(values: list[float]) -> float | None:
    """The same rule as the dongle's own screen: sort ascending, take
    sorted[floor(n/2)] (upper-middle for an even count)."""
    nums = sorted(v for v in values if isinstance(v, (int, float)))
    if not nums:
        return None
    return nums[len(nums) // 2]


def flagged_cells(values: list[float]) -> list[int]:
    """1-based cells whose resistance is STRICTLY above 1.5× the median."""
    med = resistance_median(values)
    if med is None or med <= 0:
        return []
    return [i + 1 for i, v in enumerate(values) if isinstance(v, (int, float)) and v > med * 1.5]


def balancing_text(value: Any) -> str:
    if isinstance(value, bool):
        return "charging" if value else "off"
    if isinstance(value, (int, float)):
        return BALANCING_NAMES.get(int(value), str(value))
    return str(value) if value is not None else "off"


def balancer_waiting(device: dict) -> bool:
    """The balancer only acts once a cell is above its start voltage AND the
    spread exceeds the trigger: spread over the trigger with every cell still
    below the start voltage = waiting for the top of charge, not a fault."""
    cfg = device.get("balancerCfg") or {}
    start = cfg.get("startVoltage") or 0
    if not cfg.get("enabled") or not start:
        return False
    if (device.get("cellDeltaMv") or 0) <= (cfg.get("triggerMv") or 0):
        return False
    cells = [v for v in device.get("cellVoltages") or [] if isinstance(v, (int, float))]
    if not cells:
        return False
    return max(cells) < start


def flatten_device(device: dict) -> dict[str, Any]:
    """One JK device's JSON -> the flat {entity_suffix: value} map the
    coordinator stores. Keys are stable per MAC; per-cell values use the
    1-based cell number."""
    resistances = [v for v in device.get("cellResistanceMohm") or [] if isinstance(v, (int, float))]
    voltages = [v for v in device.get("cellVoltages") or [] if isinstance(v, (int, float))]
    flagged = flagged_cells(resistances)
    cfg = device.get("balancerCfg") or None
    out: dict[str, Any] = {
        "name": device.get("name") or device.get("mac"),
        "role": device.get("role") or "battery",
        "model": device.get("model"),
        "sw": device.get("sw"),
        "hw": device.get("hw"),
        "status": "ok" if device.get("online", True) else "offline",
        "pack_voltage": device.get("packVoltage"),
        "avg_cell_voltage": device.get("avgCellVoltage"),
        "cell_delta_mv": device.get("cellDeltaMv"),
        "max_cell": device.get("maxCell"),
        "min_cell": device.get("minCell"),
        "balancing": balancing_text(device.get("balancing")),
        "balance_current": device.get("balanceCurrent"),
        "runtime_s": device.get("runtimeS"),
        "faults": ", ".join(device.get("faults") or []) or "none",
        "res_median_mohm": resistance_median(resistances),
        "res_max_mohm": max(resistances) if resistances else None,
        "res_flagged_count": len(flagged),
        "res_flagged_cells": flagged,
    }
    for i, r in enumerate(resistances):
        out[f"cell_{i + 1}_resistance"] = r
    for i, v in enumerate(voltages):
        out[f"cell_{i + 1}_voltage"] = v
    if cfg is not None:
        out["balancer_enabled"] = "on" if cfg.get("enabled") else "off"
        out["balancer_start_voltage"] = cfg.get("startVoltage")
        out["balancer_trigger_mv"] = cfg.get("triggerMv")
        out["balancer_max_current"] = cfg.get("maxCurrent")
        out["balancer_waiting"] = "yes" if balancer_waiting(device) else "no"
    return out
