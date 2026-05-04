"""The base entity for the Bradford White Connect integration."""

from typing import TypeVar

from bradford_white_connect_client import BradfordWhiteConnectClient
from bradford_white_connect_client.types import Device
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import (
    BradfordWhiteConnectEnergyCoordinator,
    BradfordWhiteConnectStatusCoordinator,
)

_BradfordWhiteConnectCoordinatorT = TypeVar(
    "_BradfordWhiteConnectCoordinatorT", bound=BradfordWhiteConnectStatusCoordinator
)


class BradfordWhiteConnectEntity(CoordinatorEntity[_BradfordWhiteConnectCoordinatorT]):
    """Base entity for Bradford White Connect."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: _BradfordWhiteConnectCoordinatorT, dsn: str, device: Device
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._dsn = dsn
        self._device = device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, dsn)},
        )

    @property
    def client(self) -> BradfordWhiteConnectClient:
        """Shortcut to get the API client."""
        return self.coordinator.client


class BradfordWhiteConnectStatusEntity(
    BradfordWhiteConnectEntity[BradfordWhiteConnectStatusCoordinator]
):
    """Base entity for entities that use data from the status coordinator."""

    @property
    def device(self) -> Device:
        """Shortcut to get the device from the coordinator data."""
        return self.coordinator.data[self._dsn]

    @property
    def available(self) -> bool:
        """Return True if entity is available.

        Availability is governed by the coordinator's last-update success.
        The previous strict `device.connection_status == "Online"` check was
        removed because the cloud API can report `connection_status='Offline'`
        for devices that are reachable — the BW Connect app shows the unit as
        online and the coordinator successfully fetches device properties at
        the regular interval. The field appears to track something other than
        actual cloud reachability.
        """
        return super().available


class BradfordWhiteConnectEnergyEntity(
    BradfordWhiteConnectEntity[BradfordWhiteConnectEnergyCoordinator]
):
    """Base entity for entities that use data from the energy coordinator."""

    @property
    def energy_usage(self) -> float:
        """Shortcut to get the energy usage from the coordinator data."""
        return self.coordinator.data[self._dsn][self._energy_type]

    # @property
    # def available(self) -> bool:
    #     """Return True if entity is available."""
    #     return super().available and self._device.connection_status == "Online"
