"""The number platform for the Bradford White Connect integration.

These entities expose writable integer inputs as configurable numbers.
The ranges are conservative defaults consistent with what the AeroTherm
service manual / app exposes; the cloud API does not publish per-property
min/max, so changes outside these ranges are silently clamped by HA.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bradford_white_connect_client.types import Device
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
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
class BWNumberDescription(NumberEntityDescription):
    """Describes a writable numeric input."""

    property_name: str
    supported_fn: Callable[[Device], bool] = lambda device: True


NUMBERS: tuple[BWNumberDescription, ...] = (
    BWNumberDescription(
        key="set_vacation_mode_days",
        translation_key="set_vacation_mode_days",
        native_min_value=1,
        native_max_value=199,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.DAYS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        property_name="set_vacation_mode_days",
        supported_fn=_has_property("set_vacation_mode_days"),
    ),
    BWNumberDescription(
        key="set_electric_mode_days",
        translation_key="set_electric_mode_days",
        native_min_value=1,
        native_max_value=99,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.DAYS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        property_name="set_electric_mode_days",
        supported_fn=_has_property("set_electric_mode_days"),
    ),
    BWNumberDescription(
        key="set_heat_timer_1",
        translation_key="set_heat_timer_1",
        native_min_value=-1,
        native_max_value=365,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.DAYS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        property_name="set_heat_timer_1",
        supported_fn=_has_property("set_heat_timer_1"),
    ),
    BWNumberDescription(
        key="set_heat_timer_4",
        translation_key="set_heat_timer_4",
        native_min_value=-1,
        native_max_value=365,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.DAYS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        property_name="set_heat_timer_4",
        supported_fn=_has_property("set_heat_timer_4"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bradford White Connect number platform."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BradfordWhiteConnectNumber(data.status_coordinator, dsn, device, desc)
        for dsn, device in data.status_coordinator.data.items()
        for desc in NUMBERS
        if desc.supported_fn(device)
    )


class BradfordWhiteConnectNumber(BradfordWhiteConnectStatusEntity, NumberEntity):
    """Writable numeric input backed by an Ayla datapoint."""

    entity_description: BWNumberDescription

    def __init__(
        self,
        coordinator: BradfordWhiteConnectStatusCoordinator,
        dsn: str,
        device: Device,
        description: BWNumberDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, dsn, device)
        self.entity_description = description
        self._attr_unique_id = f"{dsn}_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the current value from the device, or None if missing."""
        value = get_device_property_value(
            self.device, self.entity_description.property_name
        )
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Write the new value as an integer datapoint."""
        await self.coordinator.async_set_property(
            self.device,
            self.entity_description.property_name,
            int(value),
        )
