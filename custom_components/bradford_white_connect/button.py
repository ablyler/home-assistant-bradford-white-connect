"""The button platform for the Bradford White Connect integration.

Each button writes a single boolean ``true`` to a writable Ayla
input property. The water heater's controller is expected to accept the
command and self-clear the property; we don't optimistically mirror state.

Supported buttons:

- ``clear_alarm_counts`` - reset the F-code counters stored on the
  controller. (Does NOT clear latched output flags such as
  ``water_overheat_notify`` or ``global_error`` - those are device
  outputs that the cloud cannot directly write.)
- ``reset_filter`` - clear the dirty-filter alarm and reset the percent.
- ``controller_reboot`` - soft-reboot the controller board.
- ``wifi_reboot`` - reboot the Wi-Fi module only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bradford_white_connect_client.types import Device
from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BradfordWhiteConnectData
from .const import DOMAIN
from .coordinator import BradfordWhiteConnectStatusCoordinator
from .entity import BradfordWhiteConnectStatusEntity


def _has_property(name: str) -> Callable[[Device], bool]:
    """Build a supported_fn that checks for a property's presence on the device."""
    return lambda device: name in (device.properties or {})


@dataclass(frozen=True, kw_only=True)
class BWButtonDescription(ButtonEntityDescription):
    """Describes a one-shot write button."""

    property_name: str
    supported_fn: Callable[[Device], bool] = lambda device: True


BUTTONS: tuple[BWButtonDescription, ...] = (
    BWButtonDescription(
        key="clear_alarm_counts",
        translation_key="clear_alarm_counts",
        entity_category=EntityCategory.DIAGNOSTIC,
        property_name="clear_alarm_counts",
        supported_fn=_has_property("clear_alarm_counts"),
    ),
    BWButtonDescription(
        key="reset_filter",
        translation_key="reset_filter",
        entity_category=EntityCategory.CONFIG,
        property_name="reset_filter",
        supported_fn=_has_property("reset_filter"),
    ),
    BWButtonDescription(
        key="controller_reboot",
        translation_key="controller_reboot",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.DIAGNOSTIC,
        property_name="controller_reboot",
        supported_fn=_has_property("controller_reboot"),
    ),
    BWButtonDescription(
        key="wifi_reboot",
        translation_key="wifi_reboot",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.DIAGNOSTIC,
        property_name="wifi_reboot",
        supported_fn=_has_property("wifi_reboot"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bradford White Connect button platform."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BradfordWhiteConnectButton(data.status_coordinator, dsn, device, desc)
        for dsn, device in data.status_coordinator.data.items()
        for desc in BUTTONS
        if desc.supported_fn(device)
    )


class BradfordWhiteConnectButton(BradfordWhiteConnectStatusEntity, ButtonEntity):
    """Generic one-shot write button."""

    entity_description: BWButtonDescription

    def __init__(
        self,
        coordinator: BradfordWhiteConnectStatusCoordinator,
        dsn: str,
        device: Device,
        description: BWButtonDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, dsn, device)
        self.entity_description = description
        self._attr_unique_id = f"{dsn}_{description.key}"

    async def async_press(self) -> None:
        """Send the underlying datapoint write."""
        await self.coordinator.async_set_property(
            self.device, self.entity_description.property_name, True
        )
