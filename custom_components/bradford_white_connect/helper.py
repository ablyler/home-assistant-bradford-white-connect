"""Shared helpers for the Bradford White Connect integration.

These small utilities are used across every platform file. Keeping them
here (rather than duplicating per-platform) makes it easier to evolve
how we read from / introspect ``Device.properties`` in one place.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from bradford_white_connect_client.types import Device


def get_device_property_value(device: Device, property_name: str) -> Any:
    """Return ``device.properties[property_name].value`` if present, else ``None``.

    Guarded against:
    - the property key being absent from ``device.properties``
    - the property object existing but not exposing a ``.value`` attribute
    - ``device.properties`` itself being ``None`` (some devices report it that way
      before the first refresh)
    """
    properties = getattr(device, "properties", None) or {}
    prop = properties.get(property_name)
    if prop is None:
        return None
    return getattr(prop, "value", None)


def has_property(name: str) -> Callable[[Device], bool]:
    """Build a ``supported_fn(device) -> bool`` that checks a property's presence.

    Returns ``False`` (rather than raising) when ``device.properties`` is
    ``None`` so platform setup can call it unconditionally.
    """

    def _check(device: Device) -> bool:
        return name in (getattr(device, "properties", None) or {})

    return _check
