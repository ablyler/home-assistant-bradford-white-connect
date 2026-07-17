"""Unit tests for the fault-code and heat-mode decoders.

These tests deliberately do not depend on Home Assistant; they exercise
the pure-function surface in ``fault_codes`` so the decoder can be
validated even when the full ``pytest-homeassistant-custom-component``
fixture stack is unavailable.
"""

from __future__ import annotations

from fault_codes import (  # type: ignore[import-not-found]
    FAULT_CODES,
    HEAT_MODE_NAMES,
    decode_alarm_bitmap,
    heat_mode_to_name,
)


def test_decode_alarm_bitmap_none_returns_empty() -> None:
    assert decode_alarm_bitmap(None) == []


def test_decode_alarm_bitmap_empty_string_returns_empty() -> None:
    assert decode_alarm_bitmap("") == []


def test_decode_alarm_bitmap_all_zeros_returns_empty() -> None:
    assert decode_alarm_bitmap("0" * 40) == []


def test_decode_alarm_bitmap_single_known_bit() -> None:
    # Position 0 -> F1 -> "Tank sensor (T2) failure"
    bitmap = "1" + "0" * 39
    decoded = decode_alarm_bitmap(bitmap)
    assert decoded == [
        {
            "bit": 0,
            "tentative_code": "F1",
            "tentative_description": "Tank sensor (T2) failure",
        }
    ]


def test_decode_alarm_bitmap_multiple_bits_preserves_order() -> None:
    # Set bits 0 (F1), 8 (F9), and 13 (F14) in that order.
    bits = ["0"] * 40
    bits[0] = "1"
    bits[8] = "1"
    bits[13] = "1"
    decoded = decode_alarm_bitmap("".join(bits))
    assert [entry["bit"] for entry in decoded] == [0, 8, 13]
    assert [entry["tentative_code"] for entry in decoded] == ["F1", "F9", "F14"]
    assert decoded[0]["tentative_description"] == FAULT_CODES[1]
    assert decoded[1]["tentative_description"] == FAULT_CODES[9]
    assert decoded[2]["tentative_description"] == FAULT_CODES[14]


def test_decode_alarm_bitmap_unknown_bit_uses_unknown_label() -> None:
    # Bit 1 maps to F2, which is not in FAULT_CODES (it's a documented gap).
    assert 2 not in FAULT_CODES
    bitmap = "0" + "1" + "0" * 38
    decoded = decode_alarm_bitmap(bitmap)
    assert len(decoded) == 1
    assert decoded[0]["bit"] == 1
    assert decoded[0]["tentative_code"] == "F2"
    assert decoded[0]["tentative_description"].startswith("Unknown fault")


def test_heat_mode_to_name_none_returns_none() -> None:
    assert heat_mode_to_name(None) is None


def test_heat_mode_to_name_known_values() -> None:
    for vendor_value, expected_name in HEAT_MODE_NAMES.items():
        assert heat_mode_to_name(vendor_value) == expected_name


def test_heat_mode_to_name_unknown_value_returns_none() -> None:
    # Pick an int that's deliberately outside the known enum.
    unknown = max(HEAT_MODE_NAMES.keys()) + 999
    assert heat_mode_to_name(unknown) is None
