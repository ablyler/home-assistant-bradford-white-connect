"""The sensor platform for the A. O. Smith integration."""

from bradford_white_connect_client.types import Device
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BradfordWhiteConnectData
from .const import DOMAIN, ENERGY_TYPE_HEAT_PUMP, ENERGY_TYPE_RESISTANCE
from .coordinator import BradfordWhiteConnectEnergyCoordinator
from .entity import BradfordWhiteConnectEnergyEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Bradford White Connect water heater platform."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]

    # Add energy sensor entities for each device
    async_add_entities(
        BradfordWhiteConnectEnergySensorEntity(
            data.energy_coordinator, dsn, device, ENERGY_TYPE_RESISTANCE
        )
        for dsn, device in data.status_coordinator.data.items()
    )

    async_add_entities(
        BradfordWhiteConnectEnergySensorEntity(
            data.energy_coordinator, dsn, device, ENERGY_TYPE_HEAT_PUMP
        )
        for dsn, device in data.status_coordinator.data.items()
    )


class BradfordWhiteConnectEnergySensorEntity(
    BradfordWhiteConnectEnergyEntity, SensorEntity
):
    """Class for the energy sensor entity."""

    _attr_translation_key = "energy_usage"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: BradfordWhiteConnectEnergyCoordinator,
        dsn: str,
        device: Device,
        energy_type: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, dsn, device)
        energy_type_title = " ".join(energy_type.split("_")).title()
        self._attr_name = f"{device.properties['product_name'].value} {energy_type_title} Energy Usage"
        self._attr_unique_id = f"{energy_type}_{dsn}"
        self._device = device
        self._dsn = dsn
        self._energy_type = energy_type

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.energy_usage
