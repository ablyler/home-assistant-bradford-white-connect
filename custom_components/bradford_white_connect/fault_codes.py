"""Fault-code and heat-mode decoders for Bradford White Connect.

The ``alarm`` property is a 40-character ASCII string of ``0`` / ``1``,
one bit per fault slot. The mapping from bit position to F-code is
inferred (the cloud API does not publish a schema), and the F-code
descriptions are taken from the Bradford White AeroTherm
RE2H50/RE2H80 service quick-reference guide (P/N 31-75036-1, 03-15):
http://waterheatertimer.org/pdf/Bradford-White-heat-pump-error-codes.pdf

That manual covers personalities up to ``86A``. Newer personalities
(``63A`` and beyond, e.g. the RE2H65T10) appear to extend the table
with codes BW has not published publicly, and field testing shows
that bit positions on those units do not always match the older
mapping. The decoder therefore:

* exposes the **bit indices** (which are stable, undisputed facts) as
  the main state and ``active_bits`` attribute, and
* exposes the **tentative F-code descriptions** only as the
  ``tentative_descriptions`` attribute, with a clear caveat in
  ``description_source``.

The convention used for the tentative F-code labels is
**position 0 = F1**, **position 1 = F2**, ..., **position N = F(N+1)**.
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


DESCRIPTION_SOURCE: str = (
    "Tentative F-code labels inferred from the Bradford White AeroTherm "
    "RE2H50/RE2H80 service quick-reference guide (P/N 31-75036-1, 03-15); "
    "newer personalities (e.g. 63A) may use different mappings."
)


def decode_alarm_bitmap(bitmap: str | None) -> list[dict[str, str | int]]:
    """Decode a 40-char bitmap into a list of active fault bits.

    Returns a list of ``{"bit": int, "tentative_code": str,
    "tentative_description": str}`` dicts, one per ``1`` found. Only
    the ``bit`` index is reported as a hard fact; the code and
    description are best-guess from the older RE2H50/80 manual. The
    list is empty if no bits are set or the input is empty/None.
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
                "tentative_code": f"F{fault_number}",
                "tentative_description": description,
            }
        )
    return active


def heat_mode_to_name(value: int | None) -> str | None:
    """Translate an integer heat mode to its lowercase HA-style name."""
    if value is None:
        return None
    return HEAT_MODE_NAMES.get(int(value))
