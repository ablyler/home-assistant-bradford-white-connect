"""The data update coordinator for the A. O. Smith integration."""
import logging

from bradford_white_connect_client import (
    BradfordWhiteConnectAuthenticationError,
    BradfordWhiteConnectClient,
    BradfordWhiteConnectUnknownException,
)
from bradford_white_connect_client.types import Device
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, REGULAR_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BradfordWhiteConnectStatusCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    """Coordinator for device status, updating with a frequent interval."""

    def __init__(self, hass: HomeAssistant, client: BradfordWhiteConnectClient) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=REGULAR_INTERVAL)
        self.client = client

    async def _async_update_data(self) -> dict[str, Device]:
        """Fetch latest data from the device status endpoint."""
        try:
            devices = await self.client.get_devices()
            for device in devices:
                properties = await self.client.get_device_properties(device)

                remapped_properties = {p.property.name: p.property for p in properties}
                device.properties = remapped_properties

                tank_temp = device.properties.get("tank_temp")
                if tank_temp is None:
                    raise UpdateFailed("Tank temperature is missing")

                """Validate the tank temp is valid"""
                if tank_temp.value < 0 or tank_temp.value > 200:
                    raise UpdateFailed(
                        f"Tank temperature is invalid: {device.properties.get('tank_temp').value}"
                    )

            return {device.dsn: device for device in devices}
        except BradfordWhiteConnectAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except BradfordWhiteConnectUnknownException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
