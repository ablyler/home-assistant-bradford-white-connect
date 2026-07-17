"""The button platform for the Bradford White Connect integration.

Each button writes a single boolean ``true`` to a writable Ayla
input property. The water heater's controller is expected to accept the
command and self-clear the property; we don't optimistically mirror state.

Supported buttons:

- ``controller_reboot`` - soft-reboot the controller board.
- ``wifi_reboot`` - reboot the Wi-Fi module only.

The previously-shipped ``clear_alarm_counts`` and ``reset_filter`` buttons
were removed in 0.5.0; see the README for the rationale (the cloud cannot
clear the latched ``alarm`` / ``global_error`` / ``water_overheat_notify``
outputs, so those buttons were cosmetic).
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
from .entity import BradfordWhiteConnectDescribedStatusEntity
from .helper import has_property


@dataclass(frozen=True, kw_only=True)
class BWButtonDescription(ButtonEntityDescription):
    """Describes a one-shot write button."""

    property_name: str
    supported_fn: Callable[[Device], bool] = lambda device: True


BUTTONS: tuple[BWButtonDescription, ...] = (
    BWButtonDescription(
        key="controller_reboot",
        translation_key="controller_reboot",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.DIAGNOSTIC,
        property_name="controller_reboot",
        supported_fn=has_property("controller_reboot"),
    ),
    BWButtonDescription(
        key="wifi_reboot",
        translation_key="wifi_reboot",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.DIAGNOSTIC,
        property_name="wifi_reboot",
        supported_fn=has_property("wifi_reboot"),
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


class BradfordWhiteConnectButton(
    BradfordWhiteConnectDescribedStatusEntity, ButtonEntity
):
    """Generic one-shot write button."""

    entity_description: BWButtonDescription

    async def async_press(self) -> None:
        """Send the underlying datapoint write."""
        await self.coordinator.async_set_property(
            self.device, self.entity_description.property_name, True
        )
