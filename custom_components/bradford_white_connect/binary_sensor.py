"""Binary sensor platform for the Bradford White Connect integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bradford_white_connect_client.types import Device
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BradfordWhiteConnectData
from .const import DOMAIN
from .entity import BradfordWhiteConnectDescribedStatusEntity
from .helper import get_device_property_value, has_property


def _is_truthy(device: Device, property_name: str) -> bool | None:
    """Convert a 0/1/bool property value into bool, returning None when absent."""
    val = get_device_property_value(device, property_name)
    if val is None:
        return None
    try:
        return int(val) == 1
    except (TypeError, ValueError):
        return bool(val)


@dataclass(frozen=True, kw_only=True)
class BWBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a BW property exposed as a binary sensor."""

    value_fn: Callable[[Device], bool | None]
    supported_fn: Callable[[Device], bool] = lambda device: True


PROPERTY_BINARY_SENSORS: tuple[BWBinarySensorDescription, ...] = (
    BWBinarySensorDescription(
        key="compressor_running",
        translation_key="compressor_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda device: _is_truthy(device, "comp_status"),
        supported_fn=has_property("comp_status"),
    ),
    BWBinarySensorDescription(
        key="evap_fan_running",
        translation_key="evap_fan_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: _is_truthy(device, "evap_fan_status"),
        supported_fn=has_property("evap_fan_status"),
    ),
    BWBinarySensorDescription(
        key="upper_element_running",
        translation_key="upper_element_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda device: _is_truthy(device, "upper_status"),
        supported_fn=has_property("upper_status"),
    ),
    BWBinarySensorDescription(
        key="lower_element_running",
        translation_key="lower_element_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda device: _is_truthy(device, "lower_status"),
        supported_fn=has_property("lower_status"),
    ),
    BWBinarySensorDescription(
        key="global_error",
        translation_key="global_error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: _is_truthy(device, "global_error"),
        supported_fn=has_property("global_error"),
    ),
    BWBinarySensorDescription(
        key="water_overheat",
        translation_key="water_overheat",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: _is_truthy(device, "water_overheat_notify"),
        supported_fn=has_property("water_overheat_notify"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bradford White Connect binary_sensor platform."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]
    entities = [
        BradfordWhiteConnectPropertyBinarySensor(
            data.status_coordinator, dsn, device, desc
        )
        for dsn, device in data.status_coordinator.data.items()
        for desc in PROPERTY_BINARY_SENSORS
        if desc.supported_fn(device)
    ]
    async_add_entities(entities)


class BradfordWhiteConnectPropertyBinarySensor(
    BradfordWhiteConnectDescribedStatusEntity, BinarySensorEntity
):
    """Binary sensor derived from a device property."""

    entity_description: BWBinarySensorDescription

    @property
    def is_on(self) -> bool | None:
        """Return True if the underlying property reports an active state."""
        return self.entity_description.value_fn(self.device)
