"""Fault-code and heat-mode decoders for Bradford White Connect.

Fault descriptions are taken from the Bradford White AeroTherm
RE2H50/RE2H80 service quick-reference guide (P/N 31-75036-1, 03-15):
http://waterheatertimer.org/pdf/Bradford-White-heat-pump-error-codes.pdf

Newer personalities (e.g. ``63A``) may use the same F-code numbering
but Bradford White has not published a public table for them. We expose
the bit index as well as any known description so the user can see
which bits are set even when the description is unknown.

The ``alarm`` property is a 40-character ASCII string of ``0`` / ``1``.
Each character is one bit. The bit-to-F-code convention used here is
**position 0 = F1**, **position 1 = F2**, ..., **position N = F(N+1)**.
This is the natural mapping consistent with the ``alarm_count`` field
where each position holds a numeric fault counter.
"""

from __future__ import annotations

from bradford_white_connect_client.constants import (
    BradfordWhiteConnectHeatingModes,
)


FAULT_CODES: dict[int, str] = {
    1: "Tank sensor (T2) failure",
    3: "Compressor failure (no current draw)",
    4: "Fan failure",
    5: "Evap inlet sensor (T3a) failure",
    6: "Evap outlet sensor (T3b) failure",
    7: "Compressor discharge sensor (T4) failure",
    8: "Ambient sensor (T5) failure",
    9: "Lower heating element failure",
    10: "Upper heating element failure",
    11: "Dry tank fault",
    12: "Bad line voltage (low)",
    13: "Stuck key fault",
    14: "Dirty filter",
    15: "DataFlash fault",
    18: "Current transformer miswired",
    19: "Low line voltage",
    20: "Condensate drain blocked",
    21: "Application update failure",
    22: "Parametric data update failure",
    23: "Microcontroller A/D failure",
}


HEAT_MODE_NAMES: dict[int, str] = {
    BradfordWhiteConnectHeatingModes.HYBRID: "hybrid",
    BradfordWhiteConnectHeatingModes.ELECTRIC: "electric",
    BradfordWhiteConnectHeatingModes.HEAT_PUMP: "heat_pump",
    BradfordWhiteConnectHeatingModes.HYBRID_PLUS: "high_demand",
    BradfordWhiteConnectHeatingModes.VACATION: "vacation",
}


HEAT_MODE_OPTIONS: list[str] = list(HEAT_MODE_NAMES.values())


def decode_alarm_bitmap(bitmap: str | None) -> list[dict[str, str | int]]:
    """Decode a 40-char bitmap into a list of active faults.

    Returns a list of ``{"bit": int, "code": str, "description": str}``
    dicts, one per ``1`` found in the bitmap. ``code`` is the ``F<n>``
    label (1-indexed). ``description`` is the human-readable English
    summary if known, otherwise ``"Unknown fault (bit {n})"``.
    The list is empty if no bits are set.

    Passes ``None`` through as an empty list; the caller decides how to
    represent the "no data" case.
    """
    if not bitmap:
        return []
    active: list[dict[str, str | int]] = []
    for index, char in enumerate(bitmap):
        if char != "1":
            continue
        fault_number = index + 1
        description = FAULT_CODES.get(
            fault_number, f"Unknown fault (bit {index})"
        )
        active.append(
            {
                "bit": index,
                "code": f"F{fault_number}",
                "description": description,
            }
        )
    return active


def heat_mode_to_name(value: int | None) -> str | None:
    """Translate an integer heat mode to its lowercase HA-style name."""
    if value is None:
        return None
    return HEAT_MODE_NAMES.get(int(value))
