"""The text platform for the Bradford White Connect integration.

Exposes the user-editable string properties of the heater. Currently
only ``heater_name`` (the friendly name shown in the BW Connect app).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bradford_white_connect_client.types import Device
from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BradfordWhiteConnectData
from .const import DOMAIN
from .coordinator import BradfordWhiteConnectStatusCoordinator
from .entity import BradfordWhiteConnectStatusEntity
from .helper import get_device_property_value


def _has_property(name: str) -> Callable[[Device], bool]:
    """Build a supported_fn that checks for a property's presence on the device."""
    return lambda device: name in (device.properties or {})


@dataclass(frozen=True, kw_only=True)
class BWTextDescription(TextEntityDescription):
    """Describes a writable text input."""

    property_name: str
    supported_fn: Callable[[Device], bool] = lambda device: True


TEXTS: tuple[BWTextDescription, ...] = (
    BWTextDescription(
        key="heater_name",
        translation_key="heater_name",
        entity_category=EntityCategory.CONFIG,
        native_max=64,
        property_name="heater_name",
        supported_fn=_has_property("heater_name"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bradford White Connect text platform."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BradfordWhiteConnectText(data.status_coordinator, dsn, device, desc)
        for dsn, device in data.status_coordinator.data.items()
        for desc in TEXTS
        if desc.supported_fn(device)
    )


class BradfordWhiteConnectText(BradfordWhiteConnectStatusEntity, TextEntity):
    """Writable text input backed by an Ayla string property."""

    entity_description: BWTextDescription

    def __init__(
        self,
        coordinator: BradfordWhiteConnectStatusCoordinator,
        dsn: str,
        device: Device,
        description: BWTextDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, dsn, device)
        self.entity_description = description
        self._attr_unique_id = f"{dsn}_{description.key}"

    @property
    def native_value(self) -> str | None:
        """Return the current string value, or None if unset."""
        value = get_device_property_value(
            self.device, self.entity_description.property_name
        )
        if value is None:
            return None
        return str(value)

    async def async_set_value(self, value: str) -> None:
        """Send the new string to the underlying property."""
        await self.coordinator.async_set_property(
            self.device, self.entity_description.property_name, value
        )
