"""Unit tests for the small helpers shared across platforms.

The helpers are tested against a hand-rolled stub ``Device`` (a
``SimpleNamespace`` whose ``properties`` is a ``dict[str, SimpleNamespace]``
mirroring the upstream client's shape) so the tests run without needing a
live Home Assistant instance or the upstream client's dataclasses.
"""

from __future__ import annotations

from types import SimpleNamespace

from helper import (  # type: ignore[import-not-found]
    get_device_property_value,
    has_property,
)


def _make_device(**props: object) -> SimpleNamespace:
    """Build a stub device whose ``properties`` is ``{name: SimpleNamespace(value=...)}``.

    A value of ``...`` (Ellipsis) means the property exists but does not
    expose a ``value`` attribute (i.e. the upstream client returned a
    wrapper that lacks ``.value``).
    """
    properties: dict[str, SimpleNamespace] = {}
    for name, value in props.items():
        if value is ...:
            properties[name] = SimpleNamespace()
        else:
            properties[name] = SimpleNamespace(value=value)
    return SimpleNamespace(properties=properties)


def test_get_device_property_value_missing_key_returns_none() -> None:
    device = _make_device(other=1)
    assert get_device_property_value(device, "missing") is None


def test_get_device_property_value_present_without_value_attr_returns_none() -> None:
    device = _make_device(present=...)
    assert get_device_property_value(device, "present") is None


def test_get_device_property_value_present_returns_value() -> None:
    device = _make_device(tank_temp=125.0, heater_name="Garage")
    assert get_device_property_value(device, "tank_temp") == 125.0
    assert get_device_property_value(device, "heater_name") == "Garage"


def test_get_device_property_value_when_properties_is_none() -> None:
    device = SimpleNamespace(properties=None)
    assert get_device_property_value(device, "anything") is None


def test_has_property_true_when_present() -> None:
    device = _make_device(foo=1)
    assert has_property("foo")(device) is True


def test_has_property_false_when_absent() -> None:
    device = _make_device(bar=1)
    assert has_property("foo")(device) is False


def test_has_property_does_not_raise_when_properties_is_none() -> None:
    device = SimpleNamespace(properties=None)
    assert has_property("foo")(device) is False
