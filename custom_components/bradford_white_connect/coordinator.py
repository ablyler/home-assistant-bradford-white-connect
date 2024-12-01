"""The data update coordinator for the Bradford White Connect integration."""

import datetime
import logging

from bradford_white_connect_client import (
    BradfordWhiteConnectAuthenticationError,
    BradfordWhiteConnectClient,
    BradfordWhiteConnectUnknownException,
)
from bradford_white_connect_client.constants import BradfordWhiteConnectHeatingModes
from bradford_white_connect_client.types import Device
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    ENERGY_TYPE_HEAT_PUMP,
    ENERGY_TYPE_RESISTANCE,
    ENERGY_USAGE_INTERVAL,
    FAST_INTERVAL,
    REGULAR_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class BradfordWhiteConnectStatusCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    """Coordinator for device status, updating with a frequent interval."""

    def __init__(self, hass: HomeAssistant, client: BradfordWhiteConnectClient) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=REGULAR_INTERVAL)
        self.client = client
        self.shared_data = {}

    async def _async_update_data(self) -> dict[str, Device]:
        """Fetch latest data from the device status endpoint."""
        try:
            devices = await self.client.get_devices()
            for device in devices:
                # check if the last api set call (datatime) is less than REGULAR_INTERVAL
                if self.shared_data.get("last_api_set_datetime") is not None:
                    if (
                        datetime.datetime.now()
                        - self.shared_data.get("last_api_set_datetime")
                    ) < REGULAR_INTERVAL:
                        _LOGGER.debug("Setting fast update interval")
                        self.update_interval = FAST_INTERVAL
                    else:
                        _LOGGER.debug("Setting regular update interval")
                        self.update_interval = REGULAR_INTERVAL

                properties = await self.client.get_device_properties(device)

                remapped_properties = {p.property.name: p.property for p in properties}
                device.properties = remapped_properties

                temp_properties = [
                    "tank_temp",
                    "water_setpoint_out",
                    "water_setpoint_min",
                    "water_setpoint_max",
                ]

                for temp_property in temp_properties:
                    """Validate the temp property is valid"""
                    device_property = device.properties.get(temp_property)
                    if device_property is None:
                        raise UpdateFailed(
                            f"Device property {temp_property} is missing"
                        )

                    if device_property.value < 0 or device_property.value > 200:
                        raise UpdateFailed(
                            f"Device property {temp_property} is invalid: {device_property.value}"
                        )

                """Validate the current heat mode is valid"""
                device_property = device.properties.get("current_heat_mode")
                if device_property is None:
                    raise UpdateFailed("Device property 'current_heat_mode' is missing")

                if not BradfordWhiteConnectHeatingModes.is_valid(device_property.value):
                    raise UpdateFailed(
                        f"Device property 'current_heat_mode' is invalid: {device_property.value}"
                    )

            return {device.dsn: device for device in devices}
        except BradfordWhiteConnectAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except BradfordWhiteConnectUnknownException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


class BradfordWhiteConnectEnergyCoordinator(DataUpdateCoordinator[dict[str, float]]):
    """Coordinator for energy usage data, updating with a slower interval."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BradfordWhiteConnectClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=ENERGY_USAGE_INTERVAL
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, map]:
        """Fetch latest data from the energy usage endpoint."""
        energy_usage_by_dsn: dict[str, map] = {}

        # always get the energy usage the current date with a lag of one hour
        # this is to ensure we get the usage for the last hour of the day that
        # can come in after midnight
        usage_date = datetime.datetime.now() - datetime.timedelta(hours=1)

        try:
            devices = await self.client.get_devices()

            for device in devices:

                heatpump_energy = await self.client.get_total_energy_usage_for_day(
                    device, "hp", usage_date
                )
                resistance_energy = await self.client.get_total_energy_usage_for_day(
                    device, "re", usage_date
                )

                energy_usage_by_dsn[device.dsn] = {
                    ENERGY_TYPE_HEAT_PUMP: heatpump_energy,
                    ENERGY_TYPE_RESISTANCE: resistance_energy,
                }

        except BradfordWhiteConnectAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except BradfordWhiteConnectUnknownException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return energy_usage_by_dsn
