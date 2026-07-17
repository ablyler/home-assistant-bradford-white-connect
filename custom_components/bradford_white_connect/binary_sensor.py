"""Binary sensor platform for the Bradford White Connect integration."""

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
from .coordinator import BradfordWhiteConnectStatusCoordinator
from .entity import BradfordWhiteConnectStatusEntity


@dataclass(frozen=True, kw_only=True)
class BWBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a BW property exposed as a binary sensor."""

    property_name: str


PROPERTY_BINARY_SENSORS: tuple[BWBinarySensorDescription, ...] = (
    BWBinarySensorDescription(
        key="compressor_running",
        property_name="comp_status",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BWBinarySensorDescription(
        key="evap_fan_running",
        property_name="evap_fan_status",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BWBinarySensorDescription(
        key="upper_element_running",
        property_name="upper_status",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BWBinarySensorDescription(
        key="lower_element_running",
        property_name="lower_status",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Bradford White Connect binary_sensor platform."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]
    entities = [
        BradfordWhiteConnectPropertyBinarySensor(
            data.status_coordinator, dsn, device, desc
        )
        for dsn, device in data.status_coordinator.data.items()
        for desc in PROPERTY_BINARY_SENSORS
        if desc.property_name in (device.properties or {})
    ]
    async_add_entities(entities)


class BradfordWhiteConnectPropertyBinarySensor(
    BradfordWhiteConnectStatusEntity, BinarySensorEntity
):
    """Binary sensor derived from a 0/1 device property."""

    entity_description: BWBinarySensorDescription

    def __init__(
        self,
        coordinator: BradfordWhiteConnectStatusCoordinator,
        dsn: str,
        device: Device,
        description: BWBinarySensorDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, dsn, device)
        self.entity_description = description
        self._attr_unique_id = f"{dsn}_{description.key}"
        # has_entity_name=True is set on base class — HA prepends the device name.
        self._attr_name = description.key.replace("_", " ").title()

    @property
    def is_on(self) -> bool | None:
        """Return True if the property reports a non-zero/truthy value."""
        prop = self.device.properties.get(self.entity_description.property_name)
        if prop is None:
            return None
        val = getattr(prop, "value", None)
        if val is None:
            return None
        try:
            return int(val) == 1
        except (TypeError, ValueError):
            return bool(val)
