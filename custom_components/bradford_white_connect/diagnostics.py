"""Diagnostics support for the Bradford White Connect integration."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import BradfordWhiteConnectData
from .const import DOMAIN

# Fields containing PII or identifying information that should be redacted
# from any diagnostic snapshot that may be attached to a public PR or issue.
TO_REDACT = {
    "dsn",
    "mac",
    "unique_hardware_id",
    "lan_ip",
    "lat",
    "lng",
    "locality",
    "appliance_serial_number_out",
    "username",
    "email",
    "password",
}


def _property_to_dict(prop: Any) -> dict[str, Any]:
    """Convert a Property dataclass instance to a plain dict.

    Falls back to a best-effort introspection if the object is not a dataclass.
    """
    if is_dataclass(prop):
        return asdict(prop)
    return {
        attr: getattr(prop, attr)
        for attr in dir(prop)
        if not attr.startswith("_") and not callable(getattr(prop, attr, None))
    }


def _device_to_dict(device: Any) -> dict[str, Any]:
    """Render a Device into a JSON-serializable dict with expanded properties."""
    data: dict[str, Any] = {}
    for attr in (
        "product_name",
        "model",
        "dsn",
        "oem_model",
        "sw_version",
        "template_id",
        "mac",
        "unique_hardware_id",
        "lan_ip",
        "connected_at",
        "key",
        "lan_enabled",
        "connection_priority",
        "has_properties",
        "product_class",
        "connection_status",
        "lat",
        "lng",
        "locality",
        "device_type",
        "dealer",
        "facility_uuid",
    ):
        if hasattr(device, attr):
            data[attr] = getattr(device, attr)

    properties: dict[str, Any] = {}
    for name, prop in (device.properties or {}).items():
        properties[name] = _property_to_dict(prop)
    data["properties"] = properties
    return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]

    devices = {
        dsn: _device_to_dict(device)
        for dsn, device in data.status_coordinator.data.items()
    }
    energy = dict(data.energy_coordinator.data or {})

    payload: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "data": entry.data,
            "options": entry.options,
        },
        "devices": devices,
        "energy": energy,
    }

    return async_redact_data(payload, TO_REDACT)
