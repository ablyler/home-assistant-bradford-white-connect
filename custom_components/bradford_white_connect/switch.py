"""The switch platform for the Bradford White Connect integration.

Currently only exposes DRM (Demand Response Mode) controls. These let a
utility-aware automation enable load-shedding behavior on the heater
without taking it offline entirely:

- ``drm_advanced_loadup``: opt-in to advanced load-up behavior (preheat
  during a utility-signalled low-cost window).
- ``drm_service``: enable the service-side DRM acknowledgement.

Both are booleans backed by writable Ayla input properties.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from bradford_white_connect_client.types import Device
from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BradfordWhiteConnectData
from .const import DOMAIN
from .entity import BradfordWhiteConnectDescribedStatusEntity
from .helper import get_device_property_value, has_property


def _is_truthy(value: Any) -> bool:
    """Return True for any truthy/1/"true" representation; False otherwise."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "on", "yes"}
    return bool(value)


@dataclass(frozen=True, kw_only=True)
class BWSwitchDescription(SwitchEntityDescription):
    """Describes a writable boolean input switch."""

    property_name: str
    supported_fn: Callable[[Device], bool] = lambda device: True


SWITCHES: tuple[BWSwitchDescription, ...] = (
    BWSwitchDescription(
        key="drm_advanced_loadup",
        translation_key="drm_advanced_loadup",
        entity_category=EntityCategory.CONFIG,
        property_name="drm_advanced_loadup",
        supported_fn=has_property("drm_advanced_loadup"),
    ),
    BWSwitchDescription(
        key="drm_service",
        translation_key="drm_service",
        entity_category=EntityCategory.CONFIG,
        property_name="drm_service",
        supported_fn=has_property("drm_service"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bradford White Connect switch platform."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BradfordWhiteConnectSwitch(data.status_coordinator, dsn, device, desc)
        for dsn, device in data.status_coordinator.data.items()
        for desc in SWITCHES
        if desc.supported_fn(device)
    )


class BradfordWhiteConnectSwitch(
    BradfordWhiteConnectDescribedStatusEntity, SwitchEntity
):
    """Switch backed by an Ayla boolean input property."""

    entity_description: BWSwitchDescription

    @property
    def is_on(self) -> bool | None:
        """Return the current boolean state, or None if the property is missing."""
        value = get_device_property_value(
            self.device, self.entity_description.property_name
        )
        if value is None:
            return None
        return _is_truthy(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Send ``true`` to the underlying property."""
        await self.coordinator.async_set_property(
            self.device, self.entity_description.property_name, True
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Send ``false`` to the underlying property."""
        await self.coordinator.async_set_property(
            self.device, self.entity_description.property_name, False
        )
